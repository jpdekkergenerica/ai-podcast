"""Show ORM → pipeline-config dict en feed-URL's."""
from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from .defaults import (
    DEFAULT_CALL_TO_ACTION,
    DEFAULT_DURATION,
    DEFAULT_MODELS,
    DEFAULT_RELEVANCE,
    DEFAULT_VOICE,
    MAX_MINUTES_CAP,
)
from .models import CoveredItem, Episode, LearnedPronunciation, Show


def public_base_url() -> str:
    return os.environ.get("PUBLIC_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def feed_url_for(show: Show) -> str:
    return f"{public_base_url()}/feeds/{show.id}.xml?token={show.feed_token}"


def media_url_for(show: Show, filename: str) -> str:
    return f"{public_base_url()}/media/{show.id}/{filename}?token={show.feed_token}"


def site_url_for(show: Show) -> str:
    """Basis-URL voor cover/chapters/transcripts (token gaat als query mee in de feed)."""
    return f"{public_base_url()}/shows/{show.id}/site"


def show_to_cfg(show: Show) -> dict:
    return {
        "podcast": {
            "title": show.title,
            "description": show.description.strip() or show.title,
            "author": show.author,
            "email": show.email or "noreply@example.com",
            "language": show.language,
            "keep_episodes": show.keep_episodes,
            "call_to_action": show.call_to_action or DEFAULT_CALL_TO_ACTION,
            "site_url": site_url_for(show),
            "feed_url": feed_url_for(show),
            "feed_token": show.feed_token,
        },
        "duration": {
            **DEFAULT_DURATION,
            **(show.duration or {}),
            "max_minutes": min(float((show.duration or {}).get("max_minutes", DEFAULT_DURATION["max_minutes"])), MAX_MINUTES_CAP),
        },
        "relevance": {**DEFAULT_RELEVANCE, **(show.relevance or {})},
        "models": {**DEFAULT_MODELS, **(show.models or {})},
        "voice": {**DEFAULT_VOICE, **(show.voice or {})},
        "pronunciation": dict(show.pronunciation or {}),
        "topics": [
            {
                "name": t.name,
                "description": t.description,
                "keywords": list(t.keywords or []),
                "feeds": list(t.feeds or []),
            }
            for t in sorted(show.topics, key=lambda x: x.sort_order)
        ],
    }


class DbShowStore:
    """ShowStore-implementatie bovenop SQLAlchemy."""

    def __init__(self, db: Session, show_id: str):
        self.db = db
        self.show_id = show_id

    def load_episodes(self) -> list[dict]:
        rows = (
            self.db.query(Episode)
            .filter(Episode.show_id == self.show_id)
            .order_by(Episode.published.desc())
            .all()
        )
        return [r.as_dict() for r in rows]

    def save_episode(self, ep: dict) -> None:
        existing = (
            self.db.query(Episode)
            .filter(Episode.show_id == self.show_id, Episode.guid == ep["guid"])
            .one_or_none()
        )
        if existing:
            for key in ("date", "published", "title", "summary", "blurb", "tag", "file",
                        "size", "duration", "chapters", "sources"):
                setattr(existing, key, ep.get(key) if key != "size" else ep.get("size", 0))
        else:
            self.db.add(Episode(
                show_id=self.show_id,
                guid=ep["guid"],
                date=ep["date"],
                published=ep["published"],
                title=ep["title"],
                summary=ep.get("summary", ""),
                blurb=ep.get("blurb", ""),
                tag=ep.get("tag", ""),
                file=ep["file"],
                size=ep.get("size", 0),
                duration=ep.get("duration", 0),
                chapters=ep.get("chapters") or [],
                sources=ep.get("sources") or [],
            ))
        self.db.commit()

    def load_covered(self, today: date, days: int) -> list[dict]:
        if days <= 0:
            return []
        since = (today - timedelta(days=days)).isoformat()
        rows = (
            self.db.query(CoveredItem)
            .filter(CoveredItem.show_id == self.show_id, CoveredItem.date >= since)
            .all()
        )
        return [{"date": r.date, "topic": r.topic, "title": r.title, "link": r.link} for r in rows]

    def save_covered(self, today: date, plans: list[Any], keep_days: int = 14) -> None:
        since = (today - timedelta(days=keep_days)).isoformat()
        self.db.query(CoveredItem).filter(
            CoveredItem.show_id == self.show_id, CoveredItem.date < since).delete()
        for p in plans:
            for item, _ in p.items:
                self.db.add(CoveredItem(
                    show_id=self.show_id,
                    date=today.isoformat(),
                    topic=p.name,
                    title=item.title,
                    link=item.link,
                ))
        self.db.commit()

    def load_learned(self) -> dict[str, str]:
        rows = self.db.query(LearnedPronunciation).filter(
            LearnedPronunciation.show_id == self.show_id).all()
        return {r.term: r.spoken for r in rows}

    def save_learned(self, learned: dict[str, str]) -> None:
        existing = {r.term: r for r in self.db.query(LearnedPronunciation).filter(
            LearnedPronunciation.show_id == self.show_id).all()}
        for term, spoken in learned.items():
            if term in existing:
                existing[term].spoken = spoken
            else:
                self.db.add(LearnedPronunciation(show_id=self.show_id, term=term, spoken=spoken))
        for term, row in list(existing.items()):
            if term not in learned:
                self.db.delete(row)
        self.db.commit()
