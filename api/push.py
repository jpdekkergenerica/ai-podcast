"""Pushmeldingen via APNs (HTTP/2, token-authenticatie). Zonder APNS_*-instellingen wordt er niets verstuurd."""
from __future__ import annotations

import json
import os
import time

import httpx
import jwt
from sqlalchemy.orm import Session

from .models import Device, User

PROD_HOST = "https://api.push.apple.com"
SANDBOX_HOST = "https://api.sandbox.push.apple.com"

_token_cache: dict = {"jwt": "", "at": 0.0}


def configured() -> bool:
    return all(os.environ.get(k) for k in ("APNS_KEY_ID", "APNS_TEAM_ID", "APNS_AUTH_KEY", "APNS_BUNDLE_ID"))


def _auth_token(now: float | None = None) -> str:
    now = time.time() if now is None else now
    if _token_cache["jwt"] and now - _token_cache["at"] < 40 * 60:  # Apple wil een token tussen 20 en 60 minuten oud
        return _token_cache["jwt"]
    token = jwt.encode({"iss": os.environ["APNS_TEAM_ID"], "iat": int(now)},
                       os.environ["APNS_AUTH_KEY"].replace("\\n", "\n"), algorithm="ES256",
                       headers={"kid": os.environ["APNS_KEY_ID"]})
    _token_cache.update(jwt=token, at=now)
    return token


def _send(client: httpx.Client, device_token: str, title: str, body: str, data: dict) -> int:
    host = SANDBOX_HOST if os.environ.get("APNS_USE_SANDBOX") == "1" else PROD_HOST
    payload = {"aps": {"alert": {"title": title, "body": body}, "sound": "default"}, **data}
    res = client.post(f"{host}/3/device/{device_token}", content=json.dumps(payload), headers={
        "authorization": f"bearer {_auth_token()}",
        "apns-topic": os.environ["APNS_BUNDLE_ID"],
        "apns-push-type": "alert",
    })
    return res.status_code


def notify(db: Session, user: User, kind: str, title: str, body: str, data: dict | None = None,
           client: httpx.Client | None = None) -> int:
    """Stuurt een melding naar alle toestellen van de gebruiker als die dit type aan heeft. Geeft het aantal verzonden meldingen.

    kind: "new_episode" of "failed". Een ongeldig toestel-token wordt verwijderd. Fouten breken de aanroeper nooit af."""
    if kind == "new_episode" and not user.notify_new:
        return 0
    if kind == "failed" and not user.notify_failed:
        return 0
    if not configured() or not user.devices:
        return 0
    sent = 0
    own = client is None
    client = client or httpx.Client(http2=True, timeout=10.0)
    try:
        for device in list(user.devices):
            try:
                status = _send(client, device.token, title, body, data or {})
            except (httpx.HTTPError, KeyError, jwt.PyJWTError) as e:
                print(f"Waarschuwing: push mislukt ({e})")
                continue
            if status == 200:
                sent += 1
            elif status in (400, 410):  # BadDeviceToken / Unregistered
                db.delete(device)
        db.commit()
    finally:
        if own:
            client.close()
    return sent
