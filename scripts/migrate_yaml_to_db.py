#!/usr/bin/env python3
"""Migreert config.yaml + episodes/covered/pronunciation naar de multi-tenant database.

Gebruik:
  export DATABASE_URL=sqlite:///./data/app.db
  export AUTH_DEV_MODE=1
  python scripts/migrate_yaml_to_db.py --apple-sub dev-user
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api.db import SessionLocal, init_db
from api.defaults import (
    DEFAULT_CALL_TO_ACTION,
    DEFAULT_DURATION,
    DEFAULT_MODELS,
    DEFAULT_RELEVANCE,
    DEFAULT_VOICE,
)
from api.models import CoveredItem, Episode, LearnedPronunciation, Show, Topic, User


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--apple-sub", required=True, help="Apple sub of dev-user id")
    ap.add_argument("--email", default="")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / args.config).read_text())
    init_db()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.apple_sub == args.apple_sub).one_or_none()
        if user is None:
            user = User(apple_sub=args.apple_sub, email=args.email or None)
            db.add(user)
            db.flush()
        existing = db.query(Show).filter(Show.user_id == user.id).first()
        if existing:
            raise SystemExit(f"User {args.apple_sub} heeft al een show ({existing.id})")

        p = cfg["podcast"]
        show = Show(
            user_id=user.id,
            title=p["title"],
            description=p.get("description", ""),
            author=p.get("author", "Personal Podcast"),
            email=p.get("email", ""),
            language=p.get("language", "nl"),
            call_to_action=p.get("call_to_action") or DEFAULT_CALL_TO_ACTION,
            keep_episodes=p.get("keep_episodes", 14),
            duration={**DEFAULT_DURATION, **(cfg.get("duration") or {})},
            relevance={**DEFAULT_RELEVANCE, **(cfg.get("relevance") or {})},
            models={**DEFAULT_MODELS, **(cfg.get("models") or {})},
            voice={**DEFAULT_VOICE, **(cfg.get("voice") or {})},
            pronunciation=dict(cfg.get("pronunciation") or {}),
        )
        db.add(show)
        db.flush()

        for i, t in enumerate(cfg.get("topics") or []):
            db.add(Topic(
                show_id=show.id,
                name=t["name"],
                description=t.get("description", ""),
                keywords=list(t.get("keywords") or []),
                feeds=list(t.get("feeds") or []),
                sort_order=i,
            ))

        episodes_path = ROOT / "episodes.json"
        if episodes_path.exists():
            for ep in json.loads(episodes_path.read_text()):
                db.add(Episode(
                    show_id=show.id,
                    guid=ep["guid"],
                    date=ep["date"],
                    published=ep.get("published") or ep["date"],
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

        covered_path = ROOT / "covered.json"
        if covered_path.exists():
            for c in json.loads(covered_path.read_text()):
                db.add(CoveredItem(
                    show_id=show.id,
                    date=c["date"],
                    topic=c.get("topic", ""),
                    title=c.get("title", ""),
                    link=c.get("link", ""),
                ))

        learned_path = ROOT / "pronunciation.json"
        if learned_path.exists():
            for term, spoken in json.loads(learned_path.read_text()).items():
                db.add(LearnedPronunciation(show_id=show.id, term=term, spoken=spoken))

        db.commit()
        print(f"Show gemigreerd: {show.id}")
        print(f"User: {user.id} ({user.apple_sub})")
        from api.show_config import feed_url_for
        print(f"Feed: {feed_url_for(show)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
