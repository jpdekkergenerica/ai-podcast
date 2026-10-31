import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .defaults import DEFAULT_SCHEDULE, MAX_FEEDS_PER_TOPIC, MAX_MANUAL_BUILDS_PER_DAY, MAX_MINUTES_CAP, MAX_TOPICS
from .models import Job, Show


def validate_topics(topics: list) -> None:
    if len(topics) > MAX_TOPICS:
        raise HTTPException(400, f"Maximaal {MAX_TOPICS} onderwerpen")
    for t in topics:
        name = t.name if hasattr(t, "name") else t.get("name", "")
        feeds = t.feeds if hasattr(t, "feeds") else t.get("feeds", [])
        feeds = [f for f in feeds if str(f).strip()]
        if not name or not str(name).strip():
            raise HTTPException(400, "Elk onderwerp heeft een naam nodig")
        if not feeds:
            raise HTTPException(400, f"Onderwerp '{name}' heeft minstens één feed nodig")
        if len(feeds) > MAX_FEEDS_PER_TOPIC:
            raise HTTPException(400, f"Maximaal {MAX_FEEDS_PER_TOPIC} feeds per onderwerp")
        for f in feeds:
            if urlparse(str(f).strip()).scheme not in ("http", "https"):
                raise HTTPException(400, f"Feed '{f}' moet een http(s)-adres zijn")


def as_utc(moment: datetime) -> datetime:
    """SQLite geeft naïeve datums terug (UTC); behandel die als UTC in plaats van lokale tijd."""
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment.astimezone(timezone.utc)


def validate_schedule(schedule: dict) -> dict:
    """Geeft de opgeschoonde planning terug. Max. één aflevering per dag (één tijdstip), dus de kosten blijven begrensd."""
    out = {**DEFAULT_SCHEDULE, **{k: v for k, v in schedule.items() if k in DEFAULT_SCHEDULE}}
    if not isinstance(out["enabled"], bool):
        raise HTTPException(400, "enabled moet waar of onwaar zijn")
    days = out["days"]
    if (not isinstance(days, list) or any(not isinstance(d, int) or isinstance(d, bool) or not 0 <= d <= 6 for d in days)):
        raise HTTPException(400, "days: kies dagen tussen 0 (maandag) en 6 (zondag)")
    out["days"] = sorted(set(days))
    if out["enabled"] and not out["days"]:
        raise HTTPException(400, "Kies minstens één dag")
    if not isinstance(out["time"], str) or not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", out["time"]):
        raise HTTPException(400, "time moet HH:MM zijn")
    try:
        ZoneInfo(str(out["timezone"]))
    except (ZoneInfoNotFoundError, ValueError) as e:
        raise HTTPException(400, f"Onbekende tijdzone: {out['timezone']}") from e
    return out


def validate_duration(duration: dict) -> None:
    """De duur bepaalt de kosten (Claude + ElevenLabs), dus begrenzen we hem ook via de instellingen."""
    max_minutes = duration.get("max_minutes")
    if max_minutes is not None and not 1 <= float(max_minutes) <= MAX_MINUTES_CAP:
        raise HTTPException(400, f"max_minutes moet tussen 1 en {MAX_MINUTES_CAP} liggen")


def assert_can_enqueue_manual(db: Session, show: Show) -> None:
    today = datetime.now(timezone.utc).date()
    jobs = db.query(Job).filter(Job.show_id == show.id, Job.trigger == "manual").all()
    today_jobs = [
        j for j in jobs
        if j.created_at and as_utc(j.created_at).date() == today
    ]
    if len(today_jobs) >= MAX_MANUAL_BUILDS_PER_DAY:
        raise HTTPException(429, f"Maximaal {MAX_MANUAL_BUILDS_PER_DAY} handmatige build(s) per dag")


def clamp_max_minutes(value: float | None, show: Show) -> float | None:
    if value is None:
        return None
    if value > MAX_MINUTES_CAP:
        raise HTTPException(400, f"max_minutes mag hooguit {MAX_MINUTES_CAP} zijn")
    return value
