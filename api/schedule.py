"""Planning van een podcast: welke dag en welk tijdstip de aflevering klaar moet staan.

Een planning heeft `days` (0 = maandag … 6 = zondag) of een eigen interval `every_days`, een tijdstip (`time`, lokaal in
`timezone`) en staat standaard aan. Het tijdstip is het moment waarop de aflevering klaarstaat: de generatie start
SCHEDULE_LEAD_MINUTES eerder. Een gemiste start wordt tot SCHEDULE_CATCHUP_HOURS na het tijdstip ingehaald.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .defaults import DEFAULT_SCHEDULE, SCHEDULE_CATCHUP_HOURS, SCHEDULE_LEAD_MINUTES


def merged(raw: dict | None) -> dict:
    return {**DEFAULT_SCHEDULE, **(raw or {})}


def _moment(sched: dict, day: date) -> datetime:
    hh, mm = (int(x) for x in sched["time"].split(":"))
    return datetime(day.year, day.month, day.day, hh, mm, tzinfo=ZoneInfo(sched["timezone"]))


def _eligible(sched: dict, day: date, last_for: date | None) -> bool:
    """Mag er op deze publicatiedag een aflevering komen, gegeven de laatste dag waarvoor er een run was?"""
    if sched.get("every_days"):
        return last_for is None or day >= last_for + timedelta(days=int(sched["every_days"]))
    if last_for is not None and day <= last_for:
        return False
    return day.weekday() in sched["days"]


def due_publication(raw: dict | None, last_for: date | None, now: datetime) -> date | None:
    """De publicatiedag waarvoor nú een aflevering gemaakt moet worden, of None."""
    sched = merged(raw)
    if not sched["enabled"]:
        return None
    local = now.astimezone(ZoneInfo(sched["timezone"]))
    for offset in (0, 1):  # vandaag, of morgen als de voorbereiding vóór middernacht begint
        day = local.date() + timedelta(days=offset)
        if not _eligible(sched, day, last_for):
            continue
        ready_at = _moment(sched, day)
        if ready_at - timedelta(minutes=SCHEDULE_LEAD_MINUTES) <= local < ready_at + timedelta(hours=SCHEDULE_CATCHUP_HOURS):
            return day
    return None


def next_publication(raw: dict | None, last_for: date | None, now: datetime, horizon_days: int = 90) -> datetime | None:
    """Het eerstvolgende moment waarop een aflevering klaar moet staan (lokale tijd), of None."""
    sched = merged(raw)
    if not sched["enabled"]:
        return None
    local = now.astimezone(ZoneInfo(sched["timezone"]))
    for offset in range(horizon_days):
        day = local.date() + timedelta(days=offset)
        if _eligible(sched, day, last_for) and _moment(sched, day) > local:
            return _moment(sched, day)
    return None


def as_utc(moment: datetime) -> datetime:
    """SQLite geeft naïeve datums terug (UTC); behandel die als UTC in plaats van lokale tijd."""
    return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment.astimezone(timezone.utc)
