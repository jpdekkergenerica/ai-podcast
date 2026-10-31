import secrets
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .db import Base


def new_id() -> str:
    return str(uuid.uuid4())


def new_feed_token() -> str:
    return secrets.token_urlsafe(32)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    apple_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    shows: Mapped[list["Show"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Show(Base):
    __tablename__ = "shows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(200), default="yourownpod")
    email: Mapped[str] = mapped_column(String(320), default="")
    language: Mapped[str] = mapped_column(String(16), default="nl")
    call_to_action: Mapped[str] = mapped_column(Text, default="")
    keep_episodes: Mapped[int] = mapped_column(Integer, default=14)
    duration: Mapped[dict] = mapped_column(JSON, default=dict)
    relevance: Mapped[dict] = mapped_column(JSON, default=dict)
    models: Mapped[dict] = mapped_column(JSON, default=dict)
    voice: Mapped[dict] = mapped_column(JSON, default=dict)
    pronunciation: Mapped[dict] = mapped_column(JSON, default=dict)
    schedule: Mapped[dict] = mapped_column(JSON, default=dict)
    feed_token: Mapped[str] = mapped_column(String(64), default=new_feed_token, unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped[User] = relationship(back_populates="shows")
    topics: Mapped[list["Topic"]] = relationship(
        back_populates="show", cascade="all, delete-orphan", order_by="Topic.sort_order")
    episodes: Mapped[list["Episode"]] = relationship(
        back_populates="show", cascade="all, delete-orphan", order_by="Episode.published.desc()")
    covered: Mapped[list["CoveredItem"]] = relationship(
        back_populates="show", cascade="all, delete-orphan")
    learned: Mapped[list["LearnedPronunciation"]] = relationship(
        back_populates="show", cascade="all, delete-orphan")
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="show", cascade="all, delete-orphan", order_by="Job.created_at.desc()")


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    show_id: Mapped[str] = mapped_column(ForeignKey("shows.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    feeds: Mapped[list] = mapped_column(JSON, default=list)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    show: Mapped[Show] = relationship(back_populates="topics")


class Episode(Base):
    __tablename__ = "episodes"
    __table_args__ = (UniqueConstraint("show_id", "guid", name="uq_episode_guid"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    show_id: Mapped[str] = mapped_column(ForeignKey("shows.id", ondelete="CASCADE"), index=True)
    guid: Mapped[str] = mapped_column(String(120))
    date: Mapped[str] = mapped_column(String(32))
    published: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text, default="")
    blurb: Mapped[str] = mapped_column(Text, default="")
    tag: Mapped[str] = mapped_column(String(80), default="")
    file: Mapped[str] = mapped_column(String(200))
    size: Mapped[int] = mapped_column(Integer, default=0)
    duration: Mapped[int] = mapped_column(Integer, default=0)
    chapters: Mapped[list] = mapped_column(JSON, default=list)
    sources: Mapped[list] = mapped_column(JSON, default=list)

    show: Mapped[Show] = relationship(back_populates="episodes")

    def as_dict(self) -> dict:
        return {
            "guid": self.guid,
            "date": self.date,
            "published": self.published,
            "title": self.title,
            "summary": self.summary,
            "blurb": self.blurb,
            "tag": self.tag,
            "file": self.file,
            "size": self.size,
            "duration": self.duration,
            "chapters": self.chapters or [],
            "sources": self.sources or [],
        }


class CoveredItem(Base):
    __tablename__ = "covered_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    show_id: Mapped[str] = mapped_column(ForeignKey("shows.id", ondelete="CASCADE"), index=True)
    date: Mapped[str] = mapped_column(String(32), index=True)
    topic: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(500))
    link: Mapped[str] = mapped_column(String(1000), default="")

    show: Mapped[Show] = relationship(back_populates="covered")


class LearnedPronunciation(Base):
    __tablename__ = "learned_pronunciations"
    __table_args__ = (UniqueConstraint("show_id", "term", name="uq_learned_term"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    show_id: Mapped[str] = mapped_column(ForeignKey("shows.id", ondelete="CASCADE"), index=True)
    term: Mapped[str] = mapped_column(String(80))
    spoken: Mapped[str] = mapped_column(String(200))

    show: Mapped[Show] = relationship(back_populates="learned")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    show_id: Mapped[str] = mapped_column(ForeignKey("shows.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued")  # queued|running|succeeded|failed|skipped
    trigger: Mapped[str] = mapped_column(String(32), default="manual")  # manual|schedule
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    log: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)

    show: Mapped[Show] = relationship(back_populates="jobs")
