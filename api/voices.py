"""Stemmen die ElevenLabs aanbiedt. De sleutel staat centraal op de server; de app voert nooit een API-sleutel in."""
from __future__ import annotations

import os
import time

import httpx

API = "https://api.elevenlabs.io/v1/voices"
TTL = 600  # seconden dat een lijst vers genoeg is

_cache: dict = {"at": 0.0, "voices": []}


class VoicesUnavailable(RuntimeError):
    pass


def _shape(v: dict) -> dict:
    labels = v.get("labels") or {}
    return {
        "voice_id": v["voice_id"],
        "name": v.get("name", ""),
        "description": v.get("description") or ", ".join(x for x in (labels.get("gender"), labels.get("age"), labels.get("accent")) if x),
        "preview_url": v.get("preview_url") or "",
    }


def list_voices(client: httpx.Client | None = None, now: float | None = None) -> list[dict]:
    """Alle beschikbare stemmen. Bij een storing: de laatst bekende lijst, anders VoicesUnavailable."""
    now = time.time() if now is None else now
    if _cache["voices"] and now - _cache["at"] < TTL:
        return _cache["voices"]
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    try:
        if not key:
            raise VoicesUnavailable("Geen ElevenLabs-sleutel ingesteld op de server")
        own = client is None
        client = client or httpx.Client(timeout=15.0)
        try:
            res = client.get(API, headers={"xi-api-key": key})
            res.raise_for_status()
            voices = sorted((_shape(v) for v in res.json().get("voices", [])), key=lambda v: v["name"].lower())
        finally:
            if own:
                client.close()
    except (httpx.HTTPError, ValueError, KeyError, VoicesUnavailable) as e:
        if _cache["voices"]:
            return _cache["voices"]  # tijdelijk niet op te halen: bestaande keuze en lijst blijven bruikbaar
        raise VoicesUnavailable("Stemmen zijn tijdelijk niet beschikbaar") from e
    _cache.update(at=now, voices=voices)
    return voices


def known_voice_ids() -> set[str]:
    """Bekende stemmen uit de cache (leeg als er nog niets is opgehaald); voor een zachte controle bij opslaan."""
    return {v["voice_id"] for v in _cache["voices"]}
