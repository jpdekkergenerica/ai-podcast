from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .defaults import MAX_FEEDS_PER_TOPIC, MAX_MANUAL_BUILDS_PER_DAY, MAX_MINUTES_CAP, MAX_TOPICS
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


def assert_can_enqueue_manual(db: Session, show: Show) -> None:
    today = datetime.now(timezone.utc).date()
    jobs = db.query(Job).filter(Job.show_id == show.id, Job.trigger == "manual").all()
    today_jobs = [
        j for j in jobs
        if j.created_at and j.created_at.astimezone(timezone.utc).date() == today
    ]
    if len(today_jobs) >= MAX_MANUAL_BUILDS_PER_DAY:
        raise HTTPException(429, f"Maximaal {MAX_MANUAL_BUILDS_PER_DAY} handmatige build(s) per dag")


def clamp_max_minutes(value: float | None, show: Show) -> float | None:
    if value is None:
        return None
    if value > MAX_MINUTES_CAP:
        raise HTTPException(400, f"max_minutes mag hooguit {MAX_MINUTES_CAP} zijn")
    return value
