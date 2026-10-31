"""Podcasts, afleveringen, stemmen, bronnen, omslag, account en meldingen van de ingelogde gebruiker."""
from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from . import covers, push, voices
from .auth import current_user
from .db import get_db
from .defaults import DEFAULT_DURATION, DEFAULT_MODELS, DEFAULT_RELEVANCE, DEFAULT_VOICE, MAX_PODCASTS_PER_USER
from .limits import FieldErrors, clean_sources, clean_topics, validate_common, validate_schedule
from .models import Device, Job, Show, Source, Topic, User, new_feed_token
from .schedule import merged
from .schemas import (
    CoverIn,
    DeviceIn,
    EpisodeOut,
    EpisodeSummary,
    MeOut,
    MessageOut,
    NotificationPrefs,
    PodcastCreate,
    PodcastOut,
    PodcastUpdate,
    SourceCheckIn,
)
from .serializers import episode_out, episode_summary, podcast_out
from .sources import check_source
from .storage import show_dir

router = APIRouter(prefix="/me")


# ---------- hulpfuncties ----------

def _load(db: Session, user: User, podcast_id: str) -> Show:
    """Een podcast van deze gebruiker. Andermans podcast bestaat voor jou niet (404, geen 403)."""
    show = (
        db.query(Show)
        .options(selectinload(Show.topics), selectinload(Show.sources), selectinload(Show.episodes), selectinload(Show.jobs))
        .filter(Show.id == podcast_id, Show.user_id == user.id)
        .one_or_none()
    )
    if show is None:
        raise HTTPException(404, "Podcast niet gevonden")
    return show


def _set_topics(show: Show, topics: list[str]) -> None:
    show.topics.clear()
    for i, text in enumerate(topics):
        show.topics.append(Topic(name=text, description=text, keywords=[], feeds=[], sort_order=i))


def _set_sources(show: Show, urls: list[str]) -> None:
    """Houdt bestaande bronnen vast; nieuwe worden gecontroleerd (herkend als RSS of website, met naam of foutmelding).
    Een bron met een fout blokkeert het opslaan niet: bronnen zijn optioneel en automatisch zoeken blijft actief."""
    keep = {s.url: s for s in show.sources}
    for s in list(show.sources):
        if s.url not in urls:
            show.sources.remove(s)
    for url in urls:
        if url in keep:
            continue
        info = check_source(url)
        show.sources.append(Source(url=info["url"] if info["error"] is None else url, kind=info["kind"], name=info["name"],
                                   feed_url=info["feed_url"], error=info["error"]))


def _refresh_feed(show_id: str) -> None:
    from worker.run import refresh_feed
    try:
        refresh_feed(show_id)
    except Exception as e:  # noqa: BLE001  de feed wordt bij de volgende run opnieuw geschreven
        print(f"Waarschuwing: feed niet ververst ({e})")


def _local_today(show: Show):
    return datetime.now(ZoneInfo(merged(show.schedule)["timezone"])).date()


def _fresh(db: Session, user: User, podcast_id: str) -> Show:
    db.expire_all()
    return _load(db, user, podcast_id)


# ---------- podcasts ----------

@router.get("/podcasts", response_model=list[PodcastOut])
def list_podcasts(user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> list[PodcastOut]:
    shows = (
        db.query(Show)
        .options(selectinload(Show.topics), selectinload(Show.sources), selectinload(Show.episodes), selectinload(Show.jobs))
        .filter(Show.user_id == user.id)
        .order_by(Show.created_at.asc())
        .all()
    )
    return [podcast_out(s) for s in shows]


@router.post("/podcasts", response_model=PodcastOut, status_code=201)
def create_podcast(body: PodcastCreate, user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> PodcastOut:
    errors: dict[str, str] = {}
    topics = clean_topics(body.topics, errors)
    urls = clean_sources(body.sources, errors)
    validate_common(title=body.title, duration_minutes=body.duration_minutes, voice_id=body.voice_id, style=body.style,
                    required=True, errors=errors)
    schedule = validate_schedule(body.schedule or {}, errors)
    known = voices.known_voice_ids()
    if "voice" not in errors and known and body.voice_id not in known:
        errors["voice"] = "Deze stem bestaat niet (meer); kies een andere"
    if errors:
        raise FieldErrors(errors)
    if db.query(Show).filter(Show.user_id == user.id).count() >= MAX_PODCASTS_PER_USER:
        raise HTTPException(400, f"Je kunt hooguit {MAX_PODCASTS_PER_USER} podcasts hebben")

    show = Show(
        user_id=user.id,
        title=body.title.strip(),
        duration={**DEFAULT_DURATION, "max_minutes": float(body.duration_minutes)},
        relevance=dict(DEFAULT_RELEVANCE),
        models=dict(DEFAULT_MODELS),
        voice={**DEFAULT_VOICE, "voice_id": body.voice_id.strip(), "name": body.voice_name.strip()},
        style=body.style,
        schedule=schedule,
        pronunciation={},
        author="yourownpod",
    )
    db.add(show)
    db.flush()
    _set_topics(show, topics)
    _set_sources(show, urls)
    # De eerste aflevering start direct; de planning begint daarna. scheduled_for voorkomt een tweede run op dezelfde dag.
    job = Job(show_id=show.id, status="queued", trigger="initial", scheduled_for=_local_today(show).isoformat())
    db.add(job)
    db.commit()
    _refresh_feed(show.id)
    if os.environ.get("WORKER_INLINE", "0") == "1":
        from worker.run import process_job
        process_job(job.id)
    return podcast_out(_fresh(db, user, show.id))


@router.get("/podcasts/{podcast_id}", response_model=PodcastOut)
def get_podcast(podcast_id: str, user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> PodcastOut:
    return podcast_out(_load(db, user, podcast_id))


@router.patch("/podcasts/{podcast_id}", response_model=PodcastOut)
def update_podcast(podcast_id: str, body: PodcastUpdate, user: Annotated[User, Depends(current_user)],
                   db: Session = Depends(get_db)) -> PodcastOut:
    """Wijzigingen gelden voor toekomstige afleveringen en starten zelf geen extra generatie."""
    show = _load(db, user, podcast_id)
    errors: dict[str, str] = {}
    data = body.model_dump(exclude_unset=True)
    topics = clean_topics(body.topics, errors) if "topics" in data and body.topics is not None else None
    urls = clean_sources(body.sources, errors) if "sources" in data and body.sources is not None else None
    validate_common(title=data.get("title"), duration_minutes=data.get("duration_minutes"), voice_id=data.get("voice_id"),
                    style=data.get("style"), required=False, errors=errors)
    schedule = validate_schedule({**merged(show.schedule), **body.schedule}, errors) if body.schedule is not None else None
    if "voice_id" in data and "voice" not in errors:
        known = voices.known_voice_ids()
        if known and body.voice_id not in known:
            errors["voice"] = "Deze stem bestaat niet (meer); kies een andere"
    if errors:
        raise FieldErrors(errors)

    retitle = False
    if body.title is not None and body.title.strip() != show.title:
        show.title, retitle = body.title.strip(), True
    if body.duration_minutes is not None:
        show.duration = {**(show.duration or DEFAULT_DURATION), "max_minutes": float(body.duration_minutes)}
    if body.voice_id is not None:
        show.voice = {**DEFAULT_VOICE, **(show.voice or {}), "voice_id": body.voice_id.strip(),
                      "name": (body.voice_name or "").strip()}
    if body.style is not None:
        show.style = body.style
    if schedule is not None:
        show.schedule = schedule
    if topics is not None:
        _set_topics(show, topics)
    if urls is not None:
        _set_sources(show, urls)
    db.commit()
    if retitle and not show.cover_file:
        _refresh_feed(show.id)  # de standaardomslag toont de naam van de podcast
    return podcast_out(_fresh(db, user, podcast_id))


@router.post("/podcasts/{podcast_id}/pause", response_model=PodcastOut)
def pause_podcast(podcast_id: str, user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> PodcastOut:
    show = _load(db, user, podcast_id)
    show.active = False
    db.commit()
    return podcast_out(_fresh(db, user, podcast_id))


@router.post("/podcasts/{podcast_id}/resume", response_model=PodcastOut)
def resume_podcast(podcast_id: str, user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> PodcastOut:
    show = _load(db, user, podcast_id)
    show.active = True
    db.commit()
    return podcast_out(_fresh(db, user, podcast_id))


@router.post("/podcasts/{podcast_id}/rotate-feed-token", response_model=PodcastOut)
def rotate_feed_token(podcast_id: str, user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> PodcastOut:
    """Nieuwe feedlink; de oude stopt direct met werken (handig als de link ongewenst is gedeeld)."""
    show = _load(db, user, podcast_id)
    show.feed_token = new_feed_token()
    db.commit()
    _refresh_feed(show.id)
    return podcast_out(_fresh(db, user, podcast_id))


@router.delete("/podcasts/{podcast_id}", response_model=MessageOut)
def delete_podcast(podcast_id: str, user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> MessageOut:
    show = _load(db, user, podcast_id)
    shutil.rmtree(show_dir(show.id), ignore_errors=True)
    db.delete(show)
    db.commit()
    return MessageOut(message="Podcast verwijderd")


# ---------- omslag ----------

@router.post("/podcasts/{podcast_id}/cover", response_model=PodcastOut)
def set_cover(podcast_id: str, body: CoverIn, user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> PodcastOut:
    show = _load(db, user, podcast_id)
    try:
        jpeg = covers.normalize(covers.decode(body.image))
    except covers.BadCover as e:
        raise HTTPException(400, str(e)) from e  # de vorige afbeelding blijft ongemoeid
    name = f"cover-{datetime.now(timezone.utc):%Y%m%d%H%M%S}.jpg"
    covers.save_atomic(show_dir(show.id) / name, jpeg)
    old, show.cover_file = show.cover_file, name
    db.commit()
    if old:
        (show_dir(show.id) / old).unlink(missing_ok=True)
    _refresh_feed(show.id)
    return podcast_out(_fresh(db, user, podcast_id))


@router.delete("/podcasts/{podcast_id}/cover", response_model=PodcastOut)
def delete_cover(podcast_id: str, user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> PodcastOut:
    show = _load(db, user, podcast_id)
    if show.cover_file:
        (show_dir(show.id) / show.cover_file).unlink(missing_ok=True)
        show.cover_file = None
        db.commit()
        _refresh_feed(show.id)  # terug naar de standaardomslag
    return podcast_out(_fresh(db, user, podcast_id))


# ---------- afleveringen ----------

@router.get("/podcasts/{podcast_id}/episodes", response_model=list[EpisodeSummary])
def list_episodes(podcast_id: str, user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> list[EpisodeSummary]:
    return [episode_summary(e) for e in _load(db, user, podcast_id).episodes]


@router.get("/podcasts/{podcast_id}/episodes/{guid}", response_model=EpisodeOut)
def get_episode(podcast_id: str, guid: str, user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> EpisodeOut:
    show = _load(db, user, podcast_id)
    ep = next((e for e in show.episodes if e.guid == guid), None)
    if ep is None:
        raise HTTPException(404, "Aflevering niet gevonden")
    return episode_out(ep)


# ---------- bronnen en stemmen ----------

@router.post("/sources/check")
def check_one_source(body: SourceCheckIn, user: Annotated[User, Depends(current_user)]) -> dict:
    _ = user
    return check_source(body.url)


@router.get("/voices")
def list_voices(user: Annotated[User, Depends(current_user)], q: str = "") -> list[dict]:
    _ = user
    try:
        found = voices.list_voices()
    except voices.VoicesUnavailable as e:
        raise HTTPException(503, str(e)) from e
    needle = q.strip().lower()
    return [v for v in found if not needle or needle in v["name"].lower() or needle in v["description"].lower()]


# ---------- account en meldingen ----------

def _me(user: User) -> MeOut:
    return MeOut(email=user.email, notify_new=user.notify_new, notify_failed=user.notify_failed,
                 push_registered=bool(user.devices), push_available=push.configured())


@router.get("", response_model=MeOut)
def me(user: Annotated[User, Depends(current_user)]) -> MeOut:
    return _me(user)


@router.patch("/notifications", response_model=MeOut)
def set_notifications(body: NotificationPrefs, user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> MeOut:
    if body.notify_new is not None:
        user.notify_new = body.notify_new
    if body.notify_failed is not None:
        user.notify_failed = body.notify_failed
    db.commit()
    return _me(user)


@router.post("/devices", response_model=MeOut)
def register_device(body: DeviceIn, user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> MeOut:
    existing = db.query(Device).filter(Device.token == body.token).one_or_none()
    if existing is None:
        db.add(Device(user_id=user.id, token=body.token))
    elif existing.user_id != user.id:
        existing.user_id = user.id  # hetzelfde toestel, ander account: meldingen volgen de laatste login
    db.commit()
    db.refresh(user)
    return _me(user)


@router.delete("/devices/{token}", response_model=MeOut)
def unregister_device(token: str, user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> MeOut:
    db.query(Device).filter(Device.token == token, Device.user_id == user.id).delete()
    db.commit()
    db.refresh(user)
    return _me(user)
