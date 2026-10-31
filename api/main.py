"""FastAPI-app: auth, show-CRUD, privé-feed, media, jobs.

Start lokaal:
  export AUTH_DEV_MODE=1
  pip install -r requirements-api.txt
  python -m api.main
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload

from podcast.feed_test import test_feeds as probe_feeds

from .auth import AUTH_DEV_MODE, current_user, issue_access_token, verify_apple_identity_token
from .db import get_db, init_db
from .defaults import (
    DEFAULT_CALL_TO_ACTION,
    DEFAULT_DURATION,
    DEFAULT_MODELS,
    DEFAULT_RELEVANCE,
    DEFAULT_VOICE,
)
from .limits import assert_can_enqueue_manual, clamp_max_minutes, validate_duration, validate_topics
from .models import Job, Show, Topic, User, new_feed_token
from .schemas import (
    AppleLoginRequest,
    BuildRequest,
    DevLoginRequest,
    FeedTestRequest,
    MessageOut,
    ShowCreate,
    ShowOut,
    ShowUpdate,
    TokenResponse,
)
from .serializers import job_out, show_out
from .storage import audio_path, site_dir, show_dir

app = FastAPI(title="yourownpod API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=False,  # bearer-token in header, geen cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    Path("data").mkdir(exist_ok=True)


def _user_show(db: Session, user: User) -> Show | None:
    return (
        db.query(Show)
        .options(joinedload(Show.topics), joinedload(Show.episodes), joinedload(Show.jobs))
        .filter(Show.user_id == user.id)
        .order_by(Show.created_at.asc())
        .first()
    )


def _require_show(db: Session, user: User) -> Show:
    show = _user_show(db, user)
    if show is None:
        raise HTTPException(404, "Nog geen show — maak er eerst een aan")
    return show


def _replace_topics(db: Session, show: Show, topics_in: list) -> None:
    validate_topics(topics_in)
    show.topics.clear()
    db.flush()
    for i, t in enumerate(topics_in):
        show.topics.append(Topic(
            name=t.name.strip(),
            description=(t.description or "").strip(),
            keywords=[k.strip() for k in t.keywords if k.strip()],
            feeds=[f.strip() for f in t.feeds if f.strip()],
            sort_order=t.sort_order if t.sort_order else i,
        ))


def _show_by_token(db: Session, show_id: str, token: str) -> Show:
    show = db.get(Show, show_id)
    if show is None or show.feed_token != token:
        raise HTTPException(404, "Feed niet gevonden")
    return show


# ---------- auth ----------

@app.post("/auth/apple", response_model=TokenResponse)
def auth_apple(body: AppleLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    claims = verify_apple_identity_token(body.identity_token)
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(400, "Apple-token mist sub")
    email = body.email or claims.get("email")
    user = db.query(User).filter(User.apple_sub == sub).one_or_none()
    if user is None:
        user = User(apple_sub=sub, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    elif email and not user.email:
        user.email = email
        db.commit()
    return TokenResponse(
        access_token=issue_access_token(user),
        user_id=user.id,
        has_show=_user_show(db, user) is not None,
    )


@app.post("/auth/dev", response_model=TokenResponse)
def auth_dev(body: DevLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if not AUTH_DEV_MODE:
        raise HTTPException(403, "Dev-login staat uit")
    user = db.query(User).filter(User.apple_sub == body.apple_sub).one_or_none()
    if user is None:
        user = User(apple_sub=body.apple_sub, email=body.email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return TokenResponse(
        access_token=issue_access_token(user),
        user_id=user.id,
        has_show=_user_show(db, user) is not None,
    )


# ---------- show ----------

@app.get("/me/show", response_model=ShowOut)
def get_show(user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> ShowOut:
    return show_out(_require_show(db, user))


@app.post("/me/show", response_model=ShowOut)
def create_show(
    body: ShowCreate,
    user: Annotated[User, Depends(current_user)],
    db: Session = Depends(get_db),
) -> ShowOut:
    if _user_show(db, user) is not None:
        raise HTTPException(409, "Je hebt al een show (v1: één per account)")
    if body.topics:
        validate_topics(body.topics)
    show = Show(
        user_id=user.id,
        title=body.title.strip(),
        description=body.description.strip(),
        author=body.author.strip() or "yourownpod",
        email=body.email.strip(),
        language=body.language or "nl",
        call_to_action=body.call_to_action or DEFAULT_CALL_TO_ACTION,
        duration=dict(DEFAULT_DURATION),
        relevance=dict(DEFAULT_RELEVANCE),
        models=dict(DEFAULT_MODELS),
        voice=dict(DEFAULT_VOICE),
        pronunciation={},
    )
    db.add(show)
    db.flush()
    if body.topics:
        _replace_topics(db, show, body.topics)
    db.commit()
    show = _require_show(db, user)
    return show_out(show)


@app.patch("/me/show", response_model=ShowOut)
def update_show(
    body: ShowUpdate,
    user: Annotated[User, Depends(current_user)],
    db: Session = Depends(get_db),
) -> ShowOut:
    show = _require_show(db, user)
    data = body.model_dump(exclude_unset=True)
    topics = data.pop("topics", None)
    if data.get("duration") is not None:
        validate_duration(data["duration"])
    for key, value in data.items():
        setattr(show, key, value)
    if topics is not None:
        _replace_topics(db, show, body.topics or [])
    db.commit()
    return show_out(_require_show(db, user))


@app.post("/me/show/rotate-feed-token", response_model=ShowOut)
def rotate_token(user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> ShowOut:
    show = _require_show(db, user)
    show.feed_token = new_feed_token()
    db.commit()
    return show_out(_require_show(db, user))


@app.delete("/me/account", response_model=MessageOut)
def delete_account(user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> MessageOut:
    show = _user_show(db, user)
    if show is not None:
        shutil.rmtree(show_dir(show.id), ignore_errors=True)
    db.delete(user)
    db.commit()
    return MessageOut(message="Account verwijderd")


# ---------- feeds test / jobs ----------

@app.post("/me/feed-test")
def feed_test(
    body: FeedTestRequest,
    user: Annotated[User, Depends(current_user)],
) -> list[dict]:
    _ = user
    validate_topics([{"name": body.name or "test", "feeds": body.feeds}])
    return probe_feeds(
        {"name": body.name, "keywords": body.keywords, "feeds": body.feeds},
        body.lookback_hours,
    )


@app.post("/me/build", response_model=MessageOut)
def enqueue_build(
    body: BuildRequest,
    user: Annotated[User, Depends(current_user)],
    db: Session = Depends(get_db),
) -> MessageOut:
    show = _require_show(db, user)
    assert_can_enqueue_manual(db, show)
    clamp_max_minutes(body.max_minutes, show)
    if body.max_minutes is not None:
        duration = dict(show.duration or DEFAULT_DURATION)
        duration["max_minutes"] = float(body.max_minutes)
        show.duration = duration
    job = Job(show_id=show.id, status="queued", trigger="manual")
    db.add(job)
    db.commit()
    # synchrone verwerking in DEV; anders wacht de worker-poll
    if os.environ.get("WORKER_INLINE", "0") == "1":
        from worker.run import process_job
        process_job(job.id)
        return MessageOut(message="Build gestart en verwerkt")
    return MessageOut(message="Build in de wachtrij")


@app.get("/me/jobs")
def list_jobs(user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)):
    show = _require_show(db, user)
    jobs = db.query(Job).filter(Job.show_id == show.id).order_by(Job.created_at.desc()).limit(20).all()
    return [job_out(j) for j in jobs]


# ---------- private feed + media ----------

@app.get("/feeds/{show_id}.xml")
def private_feed(show_id: str, token: str = Query(...), db: Session = Depends(get_db)):
    show = _show_by_token(db, show_id, token)
    feed_file = site_dir(show.id) / "feed.xml"
    if not feed_file.exists():
        # lege feed genereren zodat Apple kan abonneren vóór de eerste aflevering
        from worker.run import refresh_feed
        refresh_feed(show.id)
    if not feed_file.exists():
        raise HTTPException(404, "Feed nog niet beschikbaar")
    return FileResponse(feed_file, media_type="application/rss+xml")


@app.get("/media/{show_id}/{filename}")
def private_media(show_id: str, filename: str, token: str = Query(...), db: Session = Depends(get_db)):
    if "/" in filename or ".." in filename:
        raise HTTPException(400, "Ongeldige bestandsnaam")
    _show_by_token(db, show_id, token)
    path = audio_path(show_id, filename)
    if not path.exists():
        # chapters/transcripts onder site/
        alt = site_dir(show_id) / filename
        if alt.exists():
            return FileResponse(alt)
        nested = None
        for folder in ("chapters", "transcripts", "audio"):
            candidate = site_dir(show_id) / folder / filename if folder != "audio" else audio_path(show_id, filename)
            if candidate.exists():
                nested = candidate
                break
        if nested is None:
            raise HTTPException(404, "Bestand niet gevonden")
        path = nested
    return FileResponse(path)


@app.get("/shows/{show_id}/site/{path:path}")
def private_site(show_id: str, path: str, token: str = Query(...), db: Session = Depends(get_db)):
    _show_by_token(db, show_id, token)
    root = site_dir(show_id).resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise HTTPException(404)
    return FileResponse(target)


@app.get("/privacy", response_class=HTMLResponse)
def privacy() -> str:
    return """<!doctype html><html lang="nl"><meta charset="utf-8">
<title>Privacy — yourownpod</title>
<body style="font-family:system-ui;max-width:40rem;margin:2rem auto;padding:0 1rem;line-height:1.5">
<h1>Privacy</h1>
<p>Deze app bewaart je Apple-accountidentificatie, e-mailadres (indien gedeeld),
podcast-instellingen, RSS-feeds die je opgeeft, en gegenereerde afleveringen.</p>
<p>Audio wordt gemaakt via Anthropic (script) en ElevenLabs (stem). We delen geen
persoonsgegevens voor advertenties.</p>
<p>Je kunt je account en alle data verwijderen in de app onder Account → Verwijder account.</p>
</body></html>"""


@app.get("/health")
def health() -> dict:
    return {"ok": True, "dev_auth": AUTH_DEV_MODE}


_APP_DIR = Path(__file__).resolve().parent.parent / "app"
if _APP_DIR.is_dir():
    app.mount("/app", StaticFiles(directory=str(_APP_DIR), html=True), name="config-app")


def main() -> None:
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), reload=False)


if __name__ == "__main__":
    main()
