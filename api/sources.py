"""Eigen bronnen van een podcast: herkennen of een adres een RSS-feed of een website is, en een herkenbare naam bepalen."""
from __future__ import annotations

import re
from html import unescape
from urllib.parse import urljoin

import feedparser

from .net import UnsafeUrl, check_public_url, fetch_public

_LINK_TAG = re.compile(r"<link\b[^>]*>", re.I)


def _attr(tag: str, name: str) -> str:
    m = re.search(rf'{name}\s*=\s*["\']([^"\']*)["\']', tag, re.I)
    return unescape(m.group(1)) if m else ""


def _title(html: str) -> str:
    m = re.search(r'<meta[^>]+property=["\']og:site_name["\'][^>]+content=["\']([^"\']+)', html, re.I) or \
        re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    return re.sub(r"\s+", " ", unescape(m.group(1))).strip()[:120] if m else ""


def check_source(url: str, fetch=fetch_public, validate=check_public_url) -> dict:
    """Controleert één bron. Geeft {url, kind, name, feed_url, error}; bij een probleem staat het in `error`."""
    out = {"url": url.strip(), "kind": "website", "name": "", "feed_url": "", "error": None}
    try:
        final, ctype, text = fetch(url)  # fetch_public controleert elk adres zelf
    except UnsafeUrl as e:
        out["error"] = str(e)
        return out
    out["url"] = final
    parsed = feedparser.parse(text)
    if parsed.entries or (parsed.feed.get("title") and ("xml" in ctype or "rss" in ctype or "atom" in ctype)):
        out.update(kind="rss", feed_url=final, name=(parsed.feed.get("title") or "").strip()[:120] or final)
        return out
    # website: zoek een RSS/Atom-verwijzing in de <head>
    for tag in _LINK_TAG.findall(text):
        if "alternate" in _attr(tag, "rel").lower() and re.search(r"(rss|atom)\+xml", _attr(tag, "type"), re.I):
            candidate = urljoin(final, _attr(tag, "href"))
            try:
                validate(candidate)
            except UnsafeUrl:
                continue
            out["feed_url"] = candidate
            break
    out["name"] = _title(text) or final
    return out
