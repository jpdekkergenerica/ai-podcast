"""Feed-probe zonder UI-afhankelijkheden (geen ruamel.yaml)."""
import calendar
import re
import socket
import time
from concurrent.futures import ThreadPoolExecutor

import feedparser


def test_feeds(topic: dict, lookback_hours: float) -> list[dict]:
    keywords = [k for k in topic.get("keywords", []) if k.strip()]
    pattern = re.compile("|".join(keywords), re.I) if keywords else None
    cutoff = time.time() - lookback_hours * 3600
    socket.setdefaulttimeout(20)

    def one(url: str) -> dict:
        try:
            feed = feedparser.parse(url)
        except Exception as e:  # noqa: BLE001
            return {"url": url, "error": str(e)}
        status = feed.get("status")
        if not feed.entries:
            return {"url": url, "status": status, "total": 0, "recent": 0, "matches": 0, "samples": [],
                    "error": f"geen berichten (status {status})"}
        recent = [e for e in feed.entries
                  if not (e.get("published_parsed") or e.get("updated_parsed"))
                  or calendar.timegm(e.get("published_parsed") or e.get("updated_parsed")) >= cutoff]
        hit = [e for e in recent if not pattern or pattern.search(f"{e.get('title', '')} {e.get('summary', '')}")]
        return {"url": url, "status": status, "total": len(feed.entries), "recent": len(recent),
                "matches": len(hit), "samples": [e.get("title", "")[:90] for e in hit[:3]]}

    with ThreadPoolExecutor(6) as pool:
        return list(pool.map(one, [f for f in topic.get("feeds", []) if f.strip()]))
