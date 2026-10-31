"""Nieuws vinden bij onderwerpen die de gebruiker als vrije tekst invoert.

1. Eigen bronnen (RSS) worden gelezen voor de nieuwsperiode.
2. Het model zoekt zelf extra nieuws op het web (webzoektool). Alleen berichten met een adres dat echt in de zoekresultaten
   stond doen mee; daarmee komt er geen verzonnen nieuws in een aflevering.
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

from . import llm
from .fetch import Item, assemble_candidates, read_feed

DISCOVERY_SYSTEM = """Je zoekt actueel nieuws voor een persoonlijke Nederlandstalige nieuwspodcast.
Selectie-eisen, in volgorde van belang:
1. Betrouwbaarheid: geef voorrang aan oorspronkelijke en redactioneel verantwoorde bronnen (nieuwsorganisaties, officiële instanties, wetenschappelijke bronnen).
   Neem geen berichten op die onbevestigde claims, geruchten of ongenuanceerde meningen als feit brengen.
2. Actualiteit: alleen berichten uit de opgegeven periode.
3. Geen dubbelen: hetzelfde nieuws uit meerdere bronnen telt één keer (kies de beste bron).
Anderstalige bronnen zijn toegestaan; schrijf titel en samenvatting altijd in het Nederlands. Verzin niets."""


def _json_items(raw: str) -> list[dict]:
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return []
    try:
        data = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return []
    items = data.get("items") if isinstance(data, dict) else None
    return [i for i in items if isinstance(i, dict)] if isinstance(items, list) else []


def _published(value: str) -> float:
    try:
        return datetime.fromisoformat(value[:10]).replace(hour=12, tzinfo=timezone.utc).timestamp()
    except (TypeError, ValueError):
        return 0.0


def discover_topic(topic_text: str, since: float, limit: int, model: str, domains: list[str] | None = None,
                   ask=llm.ask_with_search) -> list[Item]:
    """Zoekt nieuws bij één onderwerp sinds `since` (unix-tijd)."""
    since_text = datetime.fromtimestamp(since, tz=timezone.utc).strftime("%Y-%m-%d")
    prefer = ""
    if domains:
        hosts = ", ".join(sorted({urlparse(d).hostname or d for d in domains}))
        prefer = f"\nGeef extra aandacht aan deze door de luisteraar gekozen bronnen: {hosts}."
    prompt = f"""Zoek met de webzoektool het belangrijkste nieuws bij dit onderwerp: «{topic_text}»
Periode: gepubliceerd op of na {since_text}. Het onderwerp is vrije tekst van de luisteraar; lees het ruim en praktisch.{prefer}
Zoek niet meer dan nodig. Geef maximaal {limit} berichten, de belangrijkste en betrouwbaarste eerst.

Antwoord uitsluitend met JSON:
{{"items": [{{"title": "...", "summary": "twee zinnen in het Nederlands met de kernfeiten", "url": "https://...", "source": "naam van de bron", "published": "JJJJ-MM-DD"}}]}}
Is er in deze periode geen nieuws, antwoord dan {{"items": []}}."""
    text, seen = ask(prompt, model=model, system=DISCOVERY_SYSTEM)
    norm = lambda u: u.split("#")[0].rstrip("/")  # noqa: E731
    seen_norm = {norm(u) for u in seen}
    items: list[Item] = []
    for row in _json_items(text)[:limit * 2]:
        url, title = str(row.get("url", "")).strip(), re.sub(r"\s+", " ", str(row.get("title", ""))).strip()
        if not title or not url.startswith("http"):
            continue
        if norm(url) not in seen_norm:
            print(f"Waarschuwing: bericht overgeslagen, adres stond niet in de zoekresultaten ({url})")
            continue
        published = _published(str(row.get("published", "")))
        if published and published < since - 86400:
            continue
        items.append(Item(topic_text, title, str(row.get("summary", "")).strip(), url,
                          str(row.get("source", "")).strip() or (urlparse(url).hostname or url), published=published))
    return items[:limit]


def read_own_sources(feeds: list[str], since: float, per_feed: int = 15) -> list[Item]:
    """Berichten uit de eigen RSS-bronnen van de gebruiker sinds `since`. Een dode bron levert niets op, geen fout."""
    out: list[Item] = []
    for url in feeds:
        out += read_feed(url, "", since, None)[:per_feed]
    return out


def candidates_for_topic(topic: dict, cfg: dict, own: list[Item], limit: int, discover=discover_topic) -> list[Item]:
    """Eigen bronnen en zelf gevonden nieuws samen, zonder dubbelen, nieuwste eerst."""
    since = cfg["period"]["from"]
    found = discover(topic["name"], since, limit, cfg["models"]["script"], cfg.get("sources", {}).get("domains") or None)
    mine = [Item(topic["name"], i.title, i.summary, i.link, i.source, published=i.published) for i in own]
    return assemble_candidates([mine, found], limit * 2)
