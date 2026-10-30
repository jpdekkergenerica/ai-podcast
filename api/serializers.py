from .models import Job, Show
from .schemas import EpisodeSummary, JobOut, ShowOut, TopicOut
from .show_config import feed_url_for


def job_out(job: Job) -> JobOut:
    return JobOut(
        id=job.id,
        status=job.status,
        trigger=job.trigger,
        error=job.error,
        log=job.log or "",
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        duration_minutes=job.duration_minutes,
    )


def show_out(show: Show) -> ShowOut:
    latest_ep = show.episodes[0] if show.episodes else None
    latest_job = show.jobs[0] if show.jobs else None
    return ShowOut(
        id=show.id,
        title=show.title,
        description=show.description,
        author=show.author,
        email=show.email,
        language=show.language,
        call_to_action=show.call_to_action,
        keep_episodes=show.keep_episodes,
        duration=show.duration or {},
        relevance=show.relevance or {},
        models=show.models or {},
        voice=show.voice or {},
        pronunciation=dict(show.pronunciation or {}),
        feed_token=show.feed_token,
        feed_url=feed_url_for(show),
        active=show.active,
        topics=[
            TopicOut(
                id=t.id,
                name=t.name,
                description=t.description,
                keywords=list(t.keywords or []),
                feeds=list(t.feeds or []),
                sort_order=t.sort_order,
            )
            for t in sorted(show.topics, key=lambda x: x.sort_order)
        ],
        latest_episode=(
            EpisodeSummary(
                guid=latest_ep.guid,
                date=latest_ep.date,
                title=latest_ep.title,
                duration=latest_ep.duration,
                published=latest_ep.published,
            )
            if latest_ep else None
        ),
        latest_job=job_out(latest_job) if latest_job else None,
    )
