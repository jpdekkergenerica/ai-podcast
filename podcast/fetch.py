import calendar
import html
import re
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import feedparser

# Zelfde grenzen als de feedtest op de instellingenpagina.
FEED_TIMEOUT = 20
FEED_WORKERS = 6


@dataclass
class Item:
    topic: str
    title: str
    summary: str
    link: str
    source: str
    text: str = ""
    minutes: float = 0.0  # spreektijd die dit bericht in de aflevering krijgt
    published: float = 0.0  # unix-tijd; 0 als de feed geen datum meestuurt


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def per_feed_cap(n_feeds: int, limit: int) -> int:
    """Hooguit zoveel berichten per feed vóór de gezamenlijke sortering.

    Eén bron kan de kandidatenlijst daarmee niet alleen vullen. Bij één feed blijft het
    plafond gelijk aan het totaal.
    """
    if n_feeds <= 1:
        return max(0, limit)
    return max(1, (limit + n_feeds - 1) // n_feeds)


def cap_feed(items: list[Item], cap: int) -> list[Item]:
    """De nieuwste `cap` berichten. Zonder datum blijven ze in feedvolgorde achteraan."""
    if cap <= 0:
        return []
    return sorted(items, key=lambda it: it.published, reverse=True)[:cap]


def assemble_candidates(per_feed: list[list[Item]], limit: int) -> list[Item]:
    """Voegt de feeds samen: dubbele link valt weg (de eerdere feed wint), nieuwste eerst, dan `limit`."""
    seen: set[str] = set()
    merged: list[Item] = []
    for batch in per_feed:
        for item in batch:
            key = item.link or item.title
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    merged.sort(key=lambda it: it.published, reverse=True)
    return merged[:limit]


def _published(entry) -> float:
    ts = entry.get("published_parsed") or entry.get("updated_parsed")
    return float(calendar.timegm(ts)) if ts else 0.0


def read_feed(url: str, topic_name: str, cutoff: float, pattern: re.Pattern | None,
              parse=feedparser.parse) -> list[Item]:
    """Leest één feed. Een time-out of een dode feed levert een lege lijst, geen fout voor de hele run."""
    try:
        feed = parse(url)
        entries = list(feed.entries)
        source = _clean(feed.feed.get("title", "")) or url
    except Exception as e:  # noqa: BLE001
        print(f"Waarschuwing: feed niet gelezen ({url}): {e}")
        return []
    seen: set[str] = set()
    items: list[Item] = []
    for entry in entries:
        try:
            published = _published(entry)
            if published and published < cutoff:
                continue
            link = entry.get("link", "")
            title = _clean(entry.get("title", ""))
            summary = _clean(entry.get("summary", ""))
            if not title or link in seen:
                continue
            if pattern and not pattern.search(f"{title} {summary}"):
                continue
            seen.add(link)
            items.append(Item(topic_name, title, summary, link, source, published=published))
        except Exception as e:  # noqa: BLE001
            print(f"Waarschuwing: bericht overgeslagen ({url}): {e}")
    return items


def _load_feeds(urls: list[str], topic_name: str, cutoff: float, pattern: re.Pattern | None) -> list[list[Item]]:
    old = socket.getdefaulttimeout()
    socket.setdefaulttimeout(FEED_TIMEOUT)
    try:
        workers = min(FEED_WORKERS, len(urls))
        with ThreadPoolExecutor(workers) as pool:
            return list(pool.map(lambda url: read_feed(url, topic_name, cutoff, pattern), urls))
    finally:
        socket.setdefaulttimeout(old)


def fetch_topic(topic: dict, lookback_hours: int, limit: int) -> list[Item]:
    """Kandidaten voor één onderwerp: per feed een plafond, dan op datum, dan het totaalplafond."""
    urls = [u.strip() for u in topic.get("feeds", []) if str(u).strip()]
    if not urls or limit <= 0:
        return []
    keywords = topic.get("keywords")
    pattern = re.compile("|".join(keywords), re.I) if keywords else None  # regex-fragmenten, bijv. "\\bdaklo"
    cutoff = time.time() - lookback_hours * 3600
    cap = per_feed_cap(len(urls), limit)
    capped = [cap_feed(batch, cap) for batch in _load_feeds(urls, topic["name"], cutoff, pattern)]
    return assemble_candidates(capped, limit)
