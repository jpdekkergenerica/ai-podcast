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
    has_show: bool


class TopicIn(BaseModel):
    id: str | None = None
    name: str
    description: str = ""
    keywords: list[str] = Field(default_factory=list)
    feeds: list[str] = Field(default_factory=list)
    sort_order: int = 0


class TopicOut(TopicIn):
    id: str


class ShowCreate(BaseModel):
    title: str
    description: str = ""
    author: str = "yourownpod"
    email: str = ""
    language: str = "nl"
    call_to_action: str | None = None
    topics: list[TopicIn] = Field(default_factory=list)


class ShowUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    author: str | None = None
    email: str | None = None
    language: str | None = None
    call_to_action: str | None = None
    keep_episodes: int | None = None
    duration: dict[str, Any] | None = None
    relevance: dict[str, Any] | None = None
    voice: dict[str, Any] | None = None
    pronunciation: dict[str, str] | None = None
    schedule: dict[str, Any] | None = None
    topics: list[TopicIn] | None = None
    active: bool | None = None


class JobOut(BaseModel):
    id: str
    status: str
    trigger: str
    error: str | None
    log: str
    created_at: datetime | None
    started_at: datetime | None
    finished_at: datetime | None
    duration_minutes: float | None


class EpisodeSummary(BaseModel):
    guid: str
    date: str
    title: str
    duration: int
    published: str


class ShowOut(BaseModel):
    id: str
    title: str
    description: str
    author: str
    email: str
    language: str
    call_to_action: str
    keep_episodes: int
    duration: dict[str, Any]
    relevance: dict[str, Any]
    models: dict[str, Any]
    voice: dict[str, Any]
    pronunciation: dict[str, str]
    schedule: dict[str, Any]
    feed_token: str
    feed_url: str
    active: bool
    topics: list[TopicOut]
    latest_episode: EpisodeSummary | None = None
    latest_job: JobOut | None = None


class FeedTestRequest(BaseModel):
    name: str = ""
    description: str = ""
    keywords: list[str] = Field(default_factory=list)
    feeds: list[str] = Field(default_factory=list)
    lookback_hours: float = 72


class BuildRequest(BaseModel):
    max_minutes: float | None = None


class MessageOut(BaseModel):
    message: str
