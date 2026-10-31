from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AppleLoginRequest(BaseModel):
    identity_token: str
    email: str | None = None


class DevLoginRequest(BaseModel):
    apple_sub: str = "dev-user"
    email: str | None = "dev@example.com"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    has_show: bool = False
    podcast_count: int = 0


class MessageOut(BaseModel):
    message: str


# ---------- podcasts ----------

class PodcastCreate(BaseModel):
    title: str = ""
    topics: list[str] = Field(default_factory=list)  # vrije tekst, één onderwerp per veld
    sources: list[str] = Field(default_factory=list)  # eigen bronnen (website- of RSS-adres), optioneel
    duration_minutes: int | None = None  # 5, 10, 15 of 20
    voice_id: str = ""
    voice_name: str = ""
    style: str = ""  # zakelijk | informeel | verhalend
    schedule: dict[str, Any] | None = None


class PodcastUpdate(BaseModel):
    title: str | None = None
    topics: list[str] | None = None
    sources: list[str] | None = None
    duration_minutes: int | None = None
    voice_id: str | None = None
    voice_name: str | None = None
    style: str | None = None
    schedule: dict[str, Any] | None = None


class TopicOut(BaseModel):
    id: str
    text: str


class SourceOut(BaseModel):
    id: str
    url: str
    kind: str
    name: str
    feed_url: str
    error: str | None


class VoiceRef(BaseModel):
    voice_id: str
    name: str


class NextRun(BaseModel):
    at: datetime  # UTC
    local: str  # bijvoorbeeld "ma 2 november om 07:00"
    timezone: str


class StatusOut(BaseModel):
    code: str  # scheduled | running | published | failed | paused | skipped
    label: str
    detail: str


class EpisodeSummary(BaseModel):
    guid: str
    date: str
    published: str
    title: str
    duration: int
    status: str = "published"


class PodcastOut(BaseModel):
    id: str
    title: str
    cover_url: str
    has_custom_cover: bool
    topics: list[TopicOut]
    sources: list[SourceOut]
    duration_minutes: int
    voice: VoiceRef
    style: str
    schedule: dict[str, Any]
    next_run: NextRun | None
    status: StatusOut
    paused: bool
    feed_url: str
    latest_episode: EpisodeSummary | None = None
    episode_count: int = 0


class SourceGroup(BaseModel):
    topic: str
    items: list[dict[str, str]]


class EpisodeOut(EpisodeSummary):
    summary: str
    period_start: str
    period_end: str
    sources: list[SourceGroup]


class CoverIn(BaseModel):
    image: str  # base64 of data-URL


class SourceCheckIn(BaseModel):
    url: str


class DeviceIn(BaseModel):
    token: str = Field(min_length=20, max_length=200)


class NotificationPrefs(BaseModel):
    notify_new: bool | None = None
    notify_failed: bool | None = None


class MeOut(BaseModel):
    email: str | None
    notify_new: bool
    notify_failed: bool
    push_registered: bool  # er is minstens één toestel geregistreerd
    push_available: bool  # de server kan meldingen versturen
