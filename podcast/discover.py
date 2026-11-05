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
from zoneinfo import ZoneInfo
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


NL = ZoneInfo("Europe/Amsterdam")


def _published(value: str) -> float:
    try:
        return datetime.fromisoformat(value[:10]).replace(hour=12, tzinfo=timezone.utc).timestamp()
    except (TypeError, ValueError):
        return 0.0


def _published_at(value: str) -> tuple[float, bool]:
    """(tijdstip, op de minuut bekend?). Met een tijd erbij (JJJJ-MM-DDTUU:MM) rekenen we exact; alleen een datum geldt als
    'ergens op die dag' (we weten niet of het voor of na de grens was)."""
    text = str(value or "").strip()
    if len(text) > 10 and "T" in text:
        try:
            moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return (moment if moment.tzinfo else moment.replace(tzinfo=NL)).timestamp(), True
        except ValueError:
            pass
    return _published(text), False


def discover_topic(topic_text: str, since: float, limit: int, model: str, domains: list[str] | None = None,
                   ask=llm.ask_with_search) -> list[Item]:
    """Zoekt nieuws bij één onderwerp sinds `since` (unix-tijd)."""
    start = datetime.fromtimestamp(since, tz=NL)
    since_text = start.strftime("%Y-%m-%d om %H:%M") + " (Nederlandse tijd)"
    prefer = ""
    if domains:
        hosts = ", ".join(sorted({urlparse(d).hostname or d for d in domains}))
        prefer = f"\nGeef extra aandacht aan deze door de luisteraar gekozen bronnen: {hosts}."
    prompt = f"""Zoek met de webzoektool het belangrijkste nieuws bij dit onderwerp: «{topic_text}»
Periode: gepubliceerd na {since_text}; nieuws van daarvoor telt niet mee. Het onderwerp is vrije tekst van de luisteraar; lees het ruim en praktisch.{prefer}
Zoek niet meer dan nodig. Geef maximaal {limit} berichten, de belangrijkste en betrouwbaarste eerst.

Antwoord uitsluitend met JSON:
{{"items": [{{"title": "...", "summary": "twee zinnen in het Nederlands met de kernfeiten", "url": "https://...", "source": "naam van de bron", "published": "JJJJ-MM-DD, of JJJJ-MM-DDTUU:MM als het tijdstip bekend is"}}]}}
Is er in deze periode geen nieuws, antwoord dan {{"items": []}}."""
    text, seen = ask(prompt, model=model, system=DISCOVERY_SYSTEM)
    for attempt in (2, 3):
        # Zoekresultaten gevonden maar toch een lege of onleesbare lijst: het model liep vast, geen echte nieuwsloze periode.
        if _json_items(text) or not seen:
            break
        print(f"[zoeken] poging {attempt}: {len(seen)} adressen gevonden maar het antwoord bevatte geen berichten ({text[:80]!r})")
        text, seen = ask(prompt + "\nAntwoord uitsluitend met de JSON, zonder toelichting, en gebruik alleen berichten uit je zoekresultaten.",
                         model=model, system=DISCOVERY_SYSTEM)
    norm = lambda u: u.split("#")[0].rstrip("/")  # noqa: E731
    seen_norm = {norm(u) for u in seen}
    items: list[Item] = []
    rows = _json_items(text)[:limit * 2]
    dropped = {"geen adres": 0, "adres niet in zoekresultaten": 0, "voor de periode": 0}
    for row in rows:
        url, title = str(row.get("url", "")).strip(), re.sub(r"\s+", " ", str(row.get("title", ""))).strip()
        if not title or not url.startswith("http"):
            dropped["geen adres"] += 1
            continue
        if norm(url) not in seen_norm:
            print(f"Waarschuwing: bericht overgeslagen, adres stond niet in de zoekresultaten ({url})")
            dropped["adres niet in zoekresultaten"] += 1
            continue
        published, exact = _published_at(row.get("published", ""))
        if published:
            if exact and published < since:
                dropped["voor de periode"] += 1
                continue  # vóór het begin van de periode (op de minuut)
            if not exact and datetime.fromtimestamp(published, tz=NL).date() < start.date():
                dropped["voor de periode"] += 1
                continue  # alleen een datum: de dag van de grens zelf doet nog mee
        items.append(Item(topic_text, title, str(row.get("summary", "")).strip(), url,
                          str(row.get("source", "")).strip() or (urlparse(url).hostname or url), published=published))
    if rows:
        print(f"[zoeken] '{topic_text[:60]}' sinds {since_text}: model gaf {len(rows)} berichten, {len(items)} bruikbaar, "
              f"{len(seen)} adressen in zoekresultaten" + ("; afgevallen: " + ", ".join(f"{k} {v}" for k, v in dropped.items() if v) if len(items) < len(rows) else ""))
    else:  # niets bruikbaars in het antwoord: laat zien hoe het antwoord begon en eindigde (afgekapt? geen JSON? leeg?)
        print(f"[zoeken] '{topic_text[:60]}' sinds {since_text}: GEEN berichten uit het antwoord ({len(seen)} adressen in zoekresultaten, "
              f"antwoord {len(text)} tekens). Begin: {text[:150]!r} Einde: {text[-150:]!r}")
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
