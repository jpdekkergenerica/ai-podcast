"""Opslag voor afleveringen, covered-nieuws en geleerde uitspraak.

De CLI gebruikt bestanden (episodes.json, covered.json, pronunciation.json).
De multi-tenant worker gebruikt een ShowStore die uit de database komt.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Protocol


class ShowStore(Protocol):
    def load_episodes(self) -> list[dict]: ...
    def save_episode(self, ep: dict) -> None: ...
    def load_covered(self, today: date, days: int) -> list[dict]: ...
    def save_covered(self, today: date, plans: list[Any], keep_days: int = 14) -> None: ...
    def load_learned(self) -> dict[str, str]: ...
    def save_learned(self, learned: dict[str, str]) -> None: ...


@dataclass
class FileShowStore:
    """Bestanden in de projectmap — gedrag van de oorspronkelijke CLI."""
    root: Path = field(default_factory=Path)
    episodes_name: str = "episodes.json"
    covered_name: str = "covered.json"
    learned_name: str = "pronunciation.json"

    @property
    def episodes_path(self) -> Path:
        return self.root / self.episodes_name

    @property
    def covered_path(self) -> Path:
        return self.root / self.covered_name

    @property
    def learned_path(self) -> Path:
        return self.root / self.learned_name

    def load_episodes(self) -> list[dict]:
        p = self.episodes_path
        return json.loads(p.read_text()) if p.exists() else []

    def save_episode(self, ep: dict) -> None:
        eps = [e for e in self.load_episodes() if e["guid"] != ep["guid"]] + [ep]
        eps.sort(key=lambda e: e.get("published") or e["date"], reverse=True)
        self.episodes_path.write_text(json.dumps(eps, ensure_ascii=False, indent=2) + "\n")

    def load_covered(self, today: date, days: int) -> list[dict]:
        if days <= 0 or not self.covered_path.exists():
            return []
        since = (today - timedelta(days=days)).isoformat()
        return [c for c in json.loads(self.covered_path.read_text()) if c["date"] >= since]

    def save_covered(self, today: date, plans: list[Any], keep_days: int = 14) -> None:
        old = json.loads(self.covered_path.read_text()) if self.covered_path.exists() else []
        since = (today - timedelta(days=keep_days)).isoformat()
        kept = [c for c in old if c["date"] >= since]
        kept += [{"date": today.isoformat(), "topic": p.name, "title": item.title, "link": item.link}
                 for p in plans for item, _ in p.items]
        self.covered_path.write_text(json.dumps(kept, ensure_ascii=False, indent=1) + "\n")

    def load_learned(self) -> dict[str, str]:
        p = self.learned_path
        return json.loads(p.read_text()) if p.exists() else {}

    def save_learned(self, learned: dict[str, str]) -> None:
        self.learned_path.write_text(
            json.dumps(dict(sorted(learned.items())), ensure_ascii=False, indent=1) + "\n")


DEFAULT_STORE = FileShowStore()
