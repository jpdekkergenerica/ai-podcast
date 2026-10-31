"""Validatie van podcast-instellingen. Fouten komen per veld terug, zodat de app ze bij het juiste veld kan tonen."""
from __future__ import annotations

import re
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException

from .defaults import DEFAULT_SCHEDULE, DURATION_CHOICES, MAX_SOURCES, MAX_TOPIC_LENGTH, MAX_TOPICS, STYLES
from .schedule import as_utc  # noqa: F401  (hergebruikt door de worker)


class FieldErrors(HTTPException):
    """400 met {"message": ..., "fields": {veld: melding}}."""

    def __init__(self, fields: dict[str, str]):
        super().__init__(400, detail={"message": next(iter(fields.values())), "fields": fields})


def clean_topics(topics: list[str], errors: dict[str, str]) -> list[str]:
    cleaned = [re.sub(r"\s+", " ", t).strip() for t in topics]
    cleaned = [t for t in cleaned if t]
    if not cleaned:
        errors["topics"] = "Voeg minstens één onderwerp toe"
    elif len(cleaned) > MAX_TOPICS:
        errors["topics"] = f"Maximaal {MAX_TOPICS} onderwerpen"
    elif any(len(t) > MAX_TOPIC_LENGTH for t in cleaned):
        errors["topics"] = f"Een onderwerp mag hooguit {MAX_TOPIC_LENGTH} tekens zijn"
    else:
        seen: set[str] = set()
        cleaned = [t for t in cleaned if not (t.lower() in seen or seen.add(t.lower()))]
    return cleaned


def clean_sources(urls: list[str], errors: dict[str, str]) -> list[str]:
    out: list[str] = []
    for u in urls:
        u = u.strip()
        if not u:
            continue
        if urlparse(u).scheme not in ("http", "https") or not urlparse(u).hostname:
            errors["sources"] = f"'{u}' is geen website- of RSS-adres (begin met https://)"
            break
        if u not in out:
            out.append(u)
    if len(out) > MAX_SOURCES:
        errors["sources"] = f"Maximaal {MAX_SOURCES} eigen bronnen"
    return out


def validate_schedule(schedule: dict, errors: dict[str, str] | None = None) -> dict:
    """Geeft de opgeschoonde planning terug. Hooguit één aflevering per dag (één tijdstip), dus de kosten blijven begrensd."""
    errs: dict[str, str] = {}
    out = {**DEFAULT_SCHEDULE, **{k: v for k, v in schedule.items() if k in DEFAULT_SCHEDULE}}
    days = out["days"]
    if not isinstance(out["enabled"], bool):
        errs["schedule"] = "Planning aan/uit moet waar of onwaar zijn"
    elif not isinstance(days, list) or any(not isinstance(d, int) or isinstance(d, bool) or not 0 <= d <= 6 for d in days):
        errs["schedule"] = "Kies dagen tussen maandag en zondag"
    else:
        out["days"] = sorted(set(days))
        every = out["every_days"]
        if every is not None and (not isinstance(every, int) or isinstance(every, bool) or not 2 <= every <= 30):
            errs["schedule"] = "Een eigen interval is 2 tot 30 dagen"
        elif every is None and out["enabled"] and not out["days"]:
            errs["schedule"] = "Kies minstens één dag"
        elif not isinstance(out["time"], str) or not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", out["time"]):
            errs["schedule"] = "Het tijdstip moet uur:minuut zijn, bijvoorbeeld 07:00"
        else:
            try:
                ZoneInfo(str(out["timezone"]))
            except (ZoneInfoNotFoundError, ValueError):
                errs["schedule"] = f"Onbekende tijdzone: {out['timezone']}"
    if errs:
        if errors is None:
            raise FieldErrors(errs)
        errors.update(errs)
    return out


def validate_common(*, title: str | None, duration_minutes: int | None, voice_id: str | None, style: str | None,
                    required: bool, errors: dict[str, str]) -> None:
    if title is not None or required:
        t = (title or "").strip()
        if not t:
            errors["title"] = "Geef je podcast een naam"
        elif len(t) > 100:
            errors["title"] = "De naam mag hooguit 100 tekens zijn"
    if duration_minutes is not None or required:
        if duration_minutes not in DURATION_CHOICES:
            errors["duration_minutes"] = "Kies 5, 10, 15 of 20 minuten"
    if voice_id is not None or required:
        if not (voice_id or "").strip():
            errors["voice"] = "Kies een stem"
    if style is not None or required:
        if style not in STYLES:
            errors["style"] = "Kies zakelijk, informeel of verhalend"
