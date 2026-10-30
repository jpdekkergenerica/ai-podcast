"""Hoofdstukken, transcript en shownotes per aflevering, afgeleid van wat build in episodes.json bewaart."""
import html
import json
import re

AI_NOTE = "Deze aflevering is automatisch met AI samengesteld en wordt ingesproken door een synthetische stem."


def _hms(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def _vtt_time(seconds: float) -> str:
    ms = round(seconds * 1000)
    return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d}.{ms % 1000:03d}"


def plain(text: str) -> str:
    """Script zonder pauzetags en markers, zoals een luisteraar het leest."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>|\[\[[^\]]*\]\]", " ", text)).strip()


def chapters_json(ep: dict) -> str | None:
    """Podcasting 2.0 hoofdstukken (JSON); None als de aflevering geen hoofdstukken bewaard heeft."""
    if not ep.get("chapters"):
        return None
    return json.dumps({"version": "1.2.0", "chapters": [
        {"startTime": round(c["start"]), "title": c["title"]} for c in ep["chapters"]]},
        ensure_ascii=False, indent=2)


def transcript_vtt(ep: dict, max_chars: int = 180) -> str | None:
    """WebVTT-transcript. De tijden per zin zijn een schatting: de spreektijd van een hoofdstuk wordt naar
    lengte over zijn zinnen verdeeld."""
    if not ep.get("chapters"):
        return None
    cues = []
    for c in ep["chapters"]:
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", plain(c["text"])) if s]
        groups, cur = [], ""
        for s in sentences:
            if cur and len(cur) + len(s) + 1 > max_chars:
                groups.append(cur)
                cur = s
            else:
                cur = f"{cur} {s}".strip()
        if cur:
            groups.append(cur)
        total = sum(len(g) for g in groups) or 1
        t = c["start"]
        for g in groups:
            end = t + (c["end"] - c["start"]) * len(g) / total
            cues.append(f"{_vtt_time(t)} --> {_vtt_time(end)}\n{g}")
            t = end
    return "WEBVTT\n\n" + "\n\n".join(cues) + "\n"


def shownotes_html(ep: dict) -> str:
    """HTML-shownotes voor content:encoded: samenvatting, hoofdstukken en bronnen met links."""
    esc = html.escape
    if not ep.get("chapters"):  # oudere aflevering: de platte beschrijving netjes in alinea's
        return "".join(f"<p>{esc(p)}</p>" for p in ep["summary"].split("\n\n"))
    parts = [f"<p>{esc(ep['blurb'])}</p>", "<h3>Hoofdstukken</h3><ul>"]
    parts += [f"<li>{_hms(c['start'])} {esc(c['title'])}</li>" for c in ep["chapters"]]
    parts.append("</ul>")
    by_topic: dict[str, list[dict]] = {}
    for s in ep.get("sources", []):
        by_topic.setdefault(s["topic"], []).append(s)
    if by_topic:
        parts.append("<h3>Bronnen</h3>")
        for topic, rows in by_topic.items():
            parts.append(f"<p><strong>{esc(topic)}</strong></p><ul>")
            parts += [f'<li><a href="{esc(r["link"])}">{esc(r["title"])}</a> ({esc(r["source"])})</li>' for r in rows]
            parts.append("</ul>")
    parts.append(f"<p><em>{esc(AI_NOTE)}</em></p>")
    return "".join(parts)
