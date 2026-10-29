import calendar
import html
import re
import time
from dataclasses import dataclass

import feedparser


@dataclass
class Item:
    topic: str
    title: str
    summary: str
    link: str
    source: str
    text: str = ""


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def fetch_topic(topic: dict, lookback_hours: int, limit: int) -> list[Item]:
    cutoff = time.time() - lookback_hours * 3600
    seen: set[str] = set()
    items: list[Item] = []
    for url in topic["feeds"]:
        feed = feedparser.parse(url)
        source = _clean(feed.feed.get("title", "")) or url
        for e in feed.entries:
            ts = e.get("published_parsed") or e.get("updated_parsed")
            if ts and calendar.timegm(ts) < cutoff:
                continue
            link = e.get("link", "")
            title = _clean(e.get("title", ""))
            if not title or link in seen:
                continue
            seen.add(link)
            items.append(Item(topic["name"], title, _clean(e.get("summary", "")), link, source))
    return items[:limit]
