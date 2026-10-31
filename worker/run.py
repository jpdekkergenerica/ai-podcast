"""Verwerkt build-jobs: plan → script → tts → opslaan → feed verversen."""
from __future__ import annotations

import io
import os
import sys
import tempfile
import traceback
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api import push
from api.db import SessionLocal, init_db
from api.defaults import MAX_ATTEMPTS
from api.models import Job, Show
from api.schedule import as_utc, due_publication
from api.serializers import MONTHS, last_scheduled_for
from api.show_config import DbShowStore, media_url_for, show_to_cfg
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
            .options(joinedload(Show.topics), joinedload(Show.episodes), joinedload(Show.sources))
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


def _latest_published_ts(show: Show) -> float | None:
    """Grens van de nieuwsperiode: moment van de vorige succesvol gepubliceerde aflevering."""
    stamps = []
    for ep in show.episodes:
        try:
            stamps.append(datetime.fromisoformat(ep.published).timestamp())
        except (TypeError, ValueError):
            continue
    return max(stamps) if stamps else None


def _skip_reason(cfg: dict) -> str:
    start = datetime.fromtimestamp(cfg["period"]["from"], tz=ZoneInfo("Europe/Amsterdam"))
    return (f"Er was geen nieuw nieuws bij jouw onderwerpen sinds {start.day} {MONTHS[start.month - 1]}. "
            "Deze aflevering is overgeslagen; bij de volgende geplande aflevering kijken we opnieuw.")


def _notify(db, show: Show, kind: str, title: str, body: str, data: dict) -> None:
    try:
        push.notify(db, show.user, kind, title, body, data)
    except Exception as e:  # noqa: BLE001  een mislukte melding mag de run nooit laten falen
        print(f"Waarschuwing: melding niet verstuurd ({e})")


def process_job(job_id: str, now: datetime | None = None) -> None:
    """Maakt één aflevering. Tijdelijke fouten worden hooguit MAX_ATTEMPTS keer opnieuw geprobeerd (zonder dubbele
    afleveringen: een aflevering wordt pas aan het eind opgeslagen); daarna volgt een melding over de mislukte generatie."""
    init_db()
    now = now or datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        job = db.get(Job, job_id)
        if job is None or job.status != "queued":
            return
        show = (
            db.query(Show)
            .options(joinedload(Show.topics), joinedload(Show.sources), joinedload(Show.episodes))
            .filter(Show.id == job.show_id)
            .one()
        )
        if not show.active:
            job.status = "skipped"
            job.error = "De podcast is gepauzeerd."
            job.finished_at = now
            db.commit()
            return
        job.status = "running"
        job.attempts = (job.attempts or 0) + 1
        job.started_at = now
        db.commit()

        cfg = show_to_cfg(show, since=_latest_published_ts(show))
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
            job.log = log_buf.getvalue()[-12000:]
            job.finished_at = datetime.now(timezone.utc)
            if episode:
                job.status, job.error = "succeeded", None
                db.commit()
                _notify(db, show, "new_episode", f"Nieuwe aflevering: {show.title}", episode["title"],
                        {"podcast_id": show.id, "guid": episode["guid"]})
            else:
                job.status, job.error = "skipped", _skip_reason(cfg)
                db.commit()
        except Exception as e:  # noqa: BLE001
            job.log = log_buf.getvalue()[-8000:] + "\n" + traceback.format_exc()[-4000:]
            job.error = f"{type(e).__name__}: {e}"
            if job.attempts < MAX_ATTEMPTS:
                job.status = "queued"
                job.run_after = now + timedelta(minutes=15 * job.attempts)
            else:
                job.status = "failed"
                job.finished_at = datetime.now(timezone.utc)
            db.commit()
            if job.status == "failed":
                _notify(db, show, "failed", f"Aflevering mislukt: {show.title}",
                        "Er ging iets mis bij het maken van de aflevering. Je eerdere afleveringen blijven beschikbaar.",
                        {"podcast_id": show.id})
    finally:
        db.close()


def process_next(limit: int = 1, now: datetime | None = None) -> int:
    """Pakt de oudste klaarstaande jobs (niet voor hun run_after). Geeft het aantal verwerkte jobs terug."""
    init_db()
    now = now or datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        jobs = db.query(Job).filter(Job.status == "queued").order_by(Job.created_at.asc()).all()
        ids = [j.id for j in jobs if j.run_after is None or as_utc(j.run_after) <= now][:limit]
    finally:
        db.close()
    for jid in ids:
        process_job(jid, now)
    return len(ids)


def enqueue_due(now: datetime | None = None) -> int:
    """Zet een job klaar voor elke podcast die volgens zijn eigen planning nu aan de beurt is. Gepauzeerde podcasts slaan we over."""
    init_db()
    now = now or datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        n = 0
        for show in db.query(Show).options(joinedload(Show.jobs)).filter(Show.active.is_(True)).all():
            if any(j.status in ("queued", "running") for j in show.jobs):
                continue
            last_for = last_scheduled_for(show.jobs)
            day = due_publication(show.schedule, last_for, now)
            if day is not None:
                db.add(Job(show_id=show.id, status="queued", trigger="schedule", scheduled_for=day.isoformat()))
                n += 1
        db.commit()
        return n
    finally:
        db.close()


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(prog="worker")
    ap.add_argument("command", choices=["once", "loop", "enqueue-due", "job"])
    ap.add_argument("--job-id")
    ap.add_argument("--sleep", type=int, default=10)
    args = ap.parse_args()
    if args.command == "job":
        if not args.job_id:
            raise SystemExit("--job-id vereist")
        process_job(args.job_id)
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
