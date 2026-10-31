"""FastAPI-app: auth, account, privé-feed en media. De podcasts zelf staan in routes.py.

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
from sqlalchemy.orm import Session

from .auth import AUTH_DEV_MODE, current_user, issue_access_token, verify_apple_identity_token
from .db import get_db, init_db
from .models import Show, User
from .routes import router
from .schemas import AppleLoginRequest, DevLoginRequest, MessageOut, TokenResponse
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


def _podcast_count(db: Session, user: User) -> int:
    return db.query(Show).filter(Show.user_id == user.id).count()


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
        has_show=_podcast_count(db, user) > 0,
        podcast_count=_podcast_count(db, user),
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
        has_show=_podcast_count(db, user) > 0,
        podcast_count=_podcast_count(db, user),
    )


# ---------- show ----------

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
        has_show=_podcast_count(db, user) > 0,
        podcast_count=_podcast_count(db, user),
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
        has_show=_podcast_count(db, user) > 0,
        podcast_count=_podcast_count(db, user),
    )


# ---------- account ----------

@app.delete("/me/account", response_model=MessageOut)
def delete_account(user: Annotated[User, Depends(current_user)], db: Session = Depends(get_db)) -> MessageOut:
    for show in db.query(Show).filter(Show.user_id == user.id).all():
        shutil.rmtree(show_dir(show.id), ignore_errors=True)
    db.delete(user)
    db.commit()
    return MessageOut(message="Account verwijderd")


app.include_router(router)


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
    if filename == "cover.jpg" and not (site_dir(show_id) / "cover.jpg").exists():
        from worker.run import refresh_feed  # omslag ontbreekt nog (nooit een feed geschreven): nu maken
        refresh_feed(show_id)
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
