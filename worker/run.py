"""Verwerkt build-jobs: plan → script → tts → opslaan → feed verversen."""
from __future__ import annotations

import io
import os
import sys
import tempfile
import traceback
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.db import SessionLocal, init_db
from api.defaults import SCHEDULE_CATCHUP_HOURS
from api.limits import as_utc
from api.models import Job, Show
from api.show_config import DbShowStore, media_url_for, merged_schedule, show_to_cfg
from api.storage import site_dir, store_audio
from podcast.__main__ import build
from podcast.feed import write_site
from sqlalchemy.orm import joinedload


def refresh_feed(show_id: str) -> None:
    init_db()
    db = SessionLocal()
    try:
        show = (
            db.query(Show)
            .options(joinedload(Show.topics), joinedload(Show.episodes))
            .filter(Show.id == show_id)
            .one()
        )
        cfg = show_to_cfg(show)
        store = DbShowStore(db, show.id)
        out = site_dir(show.id)

        def audio_url_for(ep: dict) -> str:
            return media_url_for(show, ep["file"])

        write_site(cfg, out, store=store, audio_url_for=audio_url_for)
        # chapters/transcripts staan al onder out/; audio blijft in storage/.../audio
    finally:
        db.close()


def process_job(job_id: str) -> None:
    init_db()
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None:
            return
        if job.status not in ("queued",):
            return
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        show = (
            db.query(Show)
            .options(joinedload(Show.topics))
            .filter(Show.id == job.show_id)
            .one()
        )
        if not show.active:
            job.status = "skipped"
            job.error = "Show is gedeactiveerd"
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
            return

        cfg = show_to_cfg(show)
        store = DbShowStore(db, show.id)
        log_buf = io.StringIO()
        episode = None
        try:
            with tempfile.TemporaryDirectory(prefix="podcast-job-") as tmp:
                out = Path(tmp)
                with redirect_stdout(log_buf):
                    episode = build(cfg, out, no_tts=False, store=store)
                if episode and not episode.get("no_tts"):
                    mp3 = out / episode["file"]
                    if mp3.exists():
                        store_audio(show.id, mp3)
                    job.duration_minutes = round(episode["duration"] / 60, 2)
                refresh_feed(show.id)
            job.status = "succeeded" if episode else "skipped"
            if not episode:
                job.error = "Geen relevant nieuws"
            job.log = log_buf.getvalue()[-12000:]
        except Exception as e:  # noqa: BLE001
            job.status = "failed"
            job.error = f"{type(e).__name__}: {e}"
            job.log = log_buf.getvalue()[-8000:] + "\n" + traceback.format_exc()[-4000:]
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()


def process_next(limit: int = 1) -> int:
    """Pakt de oudste queued jobs. Geeft het aantal verwerkte jobs terug."""
    init_db()
    db = SessionLocal()
    try:
        jobs = (
            db.query(Job)
            .filter(Job.status == "queued")
            .order_by(Job.created_at.asc())
            .limit(limit)
            .all()
        )
        ids = [j.id for j in jobs]
    finally:
        db.close()
    for jid in ids:
        process_job(jid)
    return len(ids)


def enqueue_all_active(trigger: str = "schedule") -> int:
    """Zet een job klaar voor elke actieve show. Geeft het aantal nieuwe jobs terug."""
    init_db()
    db = SessionLocal()
    try:
        shows = db.query(Show).filter(Show.active.is_(True)).all()
        n = 0
        for show in shows:
            # geen dubbele openstaande job
            open_job = (
                db.query(Job)
                .filter(Job.show_id == show.id, Job.status.in_(("queued", "running")))
                .first()
            )
            if open_job:
                continue
            db.add(Job(show_id=show.id, status="queued", trigger=trigger))
            n += 1
        db.commit()
        return n
    finally:
        db.close()


def schedule_due(show: Show, last_scheduled_at: datetime | None, now: datetime) -> bool:
    """Is deze show nu aan de beurt volgens de planning van de gebruiker?

    Ja als de planning aan staat, het lokaal een gekozen dag is, het gekozen tijdstip is bereikt (maar hooguit
    SCHEDULE_CATCHUP_HOURS geleden, zodat een late activering niet meteen een run start) en er vandaag nog geen
    geplande run is geweest."""
    sched = merged_schedule(show.schedule)
    if not sched["enabled"]:
        return False
    local = as_utc(now).astimezone(ZoneInfo(sched["timezone"]))
    if local.weekday() not in sched["days"]:
        return False
    hh, mm = (int(x) for x in sched["time"].split(":"))
    slot = local.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if not slot <= local < slot + timedelta(hours=SCHEDULE_CATCHUP_HOURS):
        return False
    if last_scheduled_at is not None and as_utc(last_scheduled_at).astimezone(ZoneInfo(sched["timezone"])).date() == local.date():
        return False
    return True


def enqueue_due(now: datetime | None = None) -> int:
    """Zet een job klaar voor elke show die volgens zijn eigen planning nu aan de beurt is."""
    init_db()
    now = now or datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        n = 0
        for show in db.query(Show).filter(Show.active.is_(True)).all():
            if not merged_schedule(show.schedule)["enabled"]:
                continue
            if db.query(Job).filter(Job.show_id == show.id, Job.status.in_(("queued", "running"))).first():
                continue
            last = (
                db.query(Job.created_at)
                .filter(Job.show_id == show.id, Job.trigger == "schedule")
                .order_by(Job.created_at.desc())
                .limit(1)
                .scalar()
            )
            if schedule_due(show, last, now):
                db.add(Job(show_id=show.id, status="queued", trigger="schedule"))
                n += 1
        db.commit()
        return n
    finally:
        db.close()


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(prog="worker")
    ap.add_argument("command", choices=["once", "loop", "enqueue-all", "enqueue-due", "job"])
    ap.add_argument("--job-id")
    ap.add_argument("--sleep", type=int, default=10)
    args = ap.parse_args()
    if args.command == "job":
        if not args.job_id:
            raise SystemExit("--job-id vereist")
        process_job(args.job_id)
    elif args.command == "enqueue-all":
        n = enqueue_all_active()
        print(f"{n} jobs in de wachtrij")
    elif args.command == "enqueue-due":
        n = enqueue_due()
        print(f"{n} jobs in de wachtrij")
    elif args.command == "once":
        n = process_next(1)
        print(f"{n} job(s) verwerkt")
    else:
        import time
        print("Worker-loop…")
        while True:
            enqueue_due()
            process_next(1)
            time.sleep(args.sleep)


if __name__ == "__main__":
    main()
