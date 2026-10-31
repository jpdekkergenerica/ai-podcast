from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone

from .defaults import DEFAULT_VOICE
from .models import Episode, Job, Show
from .schedule import as_utc, merged, next_publication
from .schemas import (
    EpisodeOut,
    EpisodeSummary,
    NextRun,
    PodcastOut,
    SourceGroup,
    SourceOut,
    StatusOut,
    TopicOut,
    VoiceRef,
)
from .show_config import feed_url_for, media_url_for

DAYS_SHORT = ["ma", "di", "wo", "do", "vr", "za", "zo"]
MONTHS = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus",
          "september", "oktober", "november", "december"]


def local_text(moment: datetime) -> str:
    return f"{DAYS_SHORT[moment.weekday()]} {moment.day} {MONTHS[moment.month - 1]} om {moment:%H:%M}"


def failure_text(job: Job) -> str:
    """Begrijpelijke uitleg in gewone taal; technische details blijven in job.error en job.log."""
    err = (job.error or "").lower()
    if "eleven" in err or "tts" in err or "voice" in err:
        reason = "De stem kon niet worden gemaakt."
    elif "anthropic" in err or "json" in err or "model" in err or "claude" in err:
        reason = "De tekst voor de aflevering kon niet worden gemaakt."
    elif "timeout" in err or "connection" in err or "network" in err:
        reason = "Een van de diensten reageerde niet."
    else:
        reason = "Er ging iets mis bij het maken van de aflevering."
    return f"{reason} Je eerdere afleveringen blijven beschikbaar. Bij de volgende geplande aflevering proberen we het opnieuw."


def last_scheduled_for(jobs: list[Job]) -> date | None:
    days = [j.scheduled_for for j in jobs if j.scheduled_for]
    return date.fromisoformat(max(days)) if days else None


def status_for(show: Show, now: datetime) -> StatusOut:
    if not show.active:
        return StatusOut(code="paused", label="Gepauzeerd", detail="Er worden tijdelijk geen nieuwe afleveringen gepland.")
    latest = show.jobs[0] if show.jobs else None
    if latest and latest.status in ("queued", "running"):
        retry = latest.attempts > 0
        detail = ("We proberen het opnieuw…" if retry else
                  "Een nieuwe aflevering wordt gemaakt." if latest.status == "running" else "De aflevering staat klaar om te beginnen.")
        return StatusOut(code="running", label="Bezig", detail=detail)
    if latest and latest.status == "failed":
        return StatusOut(code="failed", label="Mislukt", detail=failure_text(latest))
    if latest and latest.status == "skipped":
        return StatusOut(code="skipped", label="Overgeslagen", detail=latest.error or "Er was geen nieuw nieuws voor deze aflevering.")
    if show.episodes:
        return StatusOut(code="published", label="Gepubliceerd", detail="De laatste aflevering staat klaar in je feed.")
    return StatusOut(code="scheduled", label="Gepland", detail="De eerste aflevering wordt gemaakt.")


def episode_summary(ep: Episode) -> EpisodeSummary:
    return EpisodeSummary(guid=ep.guid, date=ep.date, published=ep.published, title=ep.title, duration=ep.duration)


def cover_url_for(show: Show) -> str:
    # de versie wisselt zodra de afbeelding of (bij de standaardomslag) de naam verandert, zodat apps de nieuwe omslag ophalen
    version = hashlib.sha1(f"{show.cover_file or 'standaard'}|{'' if show.cover_file else show.title}".encode()).hexdigest()[:10]
    return media_url_for(show, "cover.jpg") + f"&v={version}"


def podcast_out(show: Show, now: datetime | None = None) -> PodcastOut:
    now = now or datetime.now(timezone.utc)
    sched = merged(show.schedule)
    nxt = None if not show.active else next_publication(sched, last_scheduled_for(show.jobs), now)
    voice = {**DEFAULT_VOICE, **(show.voice or {})}
    latest_ep = show.episodes[0] if show.episodes else None
    return PodcastOut(
        id=show.id,
        title=show.title,
        cover_url=cover_url_for(show),
        has_custom_cover=bool(show.cover_file),
        topics=[TopicOut(id=t.id, text=t.name) for t in sorted(show.topics, key=lambda x: x.sort_order)],
        sources=[SourceOut(id=s.id, url=s.url, kind=s.kind, name=s.name, feed_url=s.feed_url, error=s.error) for s in show.sources],
        duration_minutes=int((show.duration or {}).get("max_minutes", 10)),
        voice=VoiceRef(voice_id=voice["voice_id"], name=voice.get("name", "")),
        style=show.style,
        schedule=sched,
        next_run=NextRun(at=nxt.astimezone(timezone.utc), local=local_text(nxt), timezone=sched["timezone"]) if nxt else None,
        status=status_for(show, now),
        paused=not show.active,
        feed_url=feed_url_for(show),
        latest_episode=episode_summary(latest_ep) if latest_ep else None,
        episode_count=len(show.episodes),
    )


def episode_out(ep: Episode) -> EpisodeOut:
    groups: dict[str, list[dict[str, str]]] = {}
    for s in ep.sources or []:
        groups.setdefault(s.get("topic", ""), []).append(
            {"title": s.get("title", ""), "link": s.get("link", ""), "source": s.get("source", "")})
    base = episode_summary(ep)
    return EpisodeOut(**base.model_dump(), summary=ep.blurb or ep.summary, period_start=ep.period_start or "",
                      period_end=ep.period_end or "", sources=[SourceGroup(topic=t, items=i) for t, i in groups.items()])
