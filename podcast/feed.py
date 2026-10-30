import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from feedgen.feed import FeedGenerator
from lxml import etree
from PIL import Image, ImageDraw, ImageFont

from .extras import chapters_json, shownotes_html, transcript_vtt
from .store import DEFAULT_STORE, ShowStore


def load_episodes(store: ShowStore | None = None) -> list[dict]:
    return (store or DEFAULT_STORE).load_episodes()


def save_episode(ep: dict, store: ShowStore | None = None) -> None:
    (store or DEFAULT_STORE).save_episode(ep)


def _urls(cfg: dict) -> tuple[str, str, str]:
    if cfg.get("podcast", {}).get("site_url"):
        site = cfg["podcast"]["site_url"].rstrip("/")
        return site, f"{site}/media", ""
    repo = os.environ.get("GITHUB_REPOSITORY") or cfg["podcast"]["repository"]
    owner, name = repo.split("/")
    site = f"https://{owner}.github.io/{name}"
    return site, f"https://github.com/{owner}/{name}/releases/download", repo


def _hms(seconds: int) -> str:
    return f"{seconds // 3600}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


FONTS = ["/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONTS:
        try:
            return ImageFont.truetype(path, size, index=1) if path.endswith(".ttc") else ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def make_cover(title: str, dest: Path) -> None:
    """3000x3000 JPEG, hoog contrast, één beeldmerk en grote titel binnen de veilige marge (leesbaar op 100x100)."""
    custom = Path("assets/cover.jpg")
    if custom.exists():
        dest.write_bytes(custom.read_bytes())
        return
    size, margin = 3000, 450
    img = Image.new("RGB", (size, size), "#12161f")
    draw = ImageDraw.Draw(img)
    cx, cy, r = size // 2, 1000, 600
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#ff7a3d")
    for i, h in enumerate([220, 440, 760, 960, 620, 840, 360, 200]):
        x = cx - 4 * 100 + i * 100 + 15
        draw.rounded_rectangle((x, cy - h // 2, x + 60, cy + h // 2), radius=30, fill="#12161f")

    fs = 400
    while True:
        font, lines, cur = _font(fs), [], ""
        for w in title.split():
            if cur and draw.textlength(f"{cur} {w}", font=font) > size - 2 * margin:
                lines.append(cur)
                cur = w
            else:
                cur = f"{cur} {w}".strip()
        lines.append(cur)
        if len(lines) * fs * 1.15 <= 800 or fs < 150:
            break
        fs -= 20
    y = 1850
    for line in lines:
        draw.text(((size - draw.textlength(line, font=font)) / 2, y), line, fill="#ffc94d", font=font)
        y += int(fs * 1.15)
    img.save(dest, "JPEG", quality=85)


def write_site(cfg: dict, site_dir: Path, store: ShowStore | None = None,
               audio_url_for=None) -> None:
    """Schrijft cover, feed.xml, chapters en transcripts.

    audio_url_for(ep) → absolute URL naar de mp3; standaard GitHub Pages /audio/.
    """
    p = cfg["podcast"]
    site, media, _ = _urls(cfg)
    token = p.get("feed_token") or ""
    q = f"?token={token}" if token else ""
    site_dir.mkdir(parents=True, exist_ok=True)
    make_cover(p["title"], site_dir / "cover.jpg")
    # Apple onthoudt artwork per URL: een versie in de bestandsnaam zorgt dat een nieuwe cover wordt opgehaald
    digest = hashlib.sha1((site_dir / "cover.jpg").read_bytes()).hexdigest()[:8]
    cover = f"cover-{digest}.jpg"
    (site_dir / cover).write_bytes((site_dir / "cover.jpg").read_bytes())

    fg = FeedGenerator()
    fg.load_extension("podcast")
    fg.title(p["title"])
    fg.description(p["description"])
    fg.link(href=site, rel="alternate")
    feed_self = p.get("feed_url") or f"{site}/feed.xml"
    fg.link(href=feed_self, rel="self")
    fg.language(p["language"])
    fg.podcast.itunes_author(p["author"])
    fg.podcast.itunes_owner(name=p["author"], email=p["email"])
    fg.podcast.itunes_image(f"{site}/{cover}{q}")
    fg.podcast.itunes_category("News", "Daily News")
    fg.podcast.itunes_explicit("no")

    tz = ZoneInfo("Europe/Amsterdam")
    episodes = load_episodes(store)[: p.get("keep_episodes", 14)]
    if audio_url_for is None:
        audio_url_for = lambda ep: f"{site}/audio/{ep['file']}{q}"
    for ep in episodes:
        fe = fg.add_entry(order="append")
        fe.id(ep["guid"])
        fe.guid(ep["guid"], permalink=False)
        fe.title(ep["title"])
        fe.description(ep["summary"])
        published = datetime.fromisoformat(ep.get("published") or ep["date"]).replace(tzinfo=None)
        fe.pubDate(published.replace(tzinfo=tz) if "published" in ep else published.replace(hour=6, tzinfo=tz))
        fe.enclosure(audio_url_for(ep), str(ep["size"]), "audio/mpeg")
        fe.podcast.itunes_duration(_hms(ep["duration"]))
        fe.content(shownotes_html(ep), type="CDATA")
    _write_feed(fg, episodes, site, site_dir, query=q)
    print(f"Feed geschreven: {feed_self} ({len(episodes)} afleveringen)")


PODCAST_NS = "https://podcastindex.org/namespace/1.0"


def _write_feed(fg: FeedGenerator, episodes: list[dict], site: str, site_dir: Path,
                query: str = "") -> None:
    """Schrijft feed.xml met per aflevering podcast:chapters en podcast:transcript (feedgen kent die niet)."""
    old = etree.fromstring(fg.rss_str(pretty=True))
    root = etree.Element(old.tag, attrib=dict(old.attrib), nsmap={**old.nsmap, "podcast": PODCAST_NS})
    root.extend(list(old))
    items = root.find("channel").findall("item")
    for item, ep in zip(items, episodes):
        stamp = ep["file"].removesuffix(".mp3")
        for folder, name, content, kind, tag in (
            ("chapters", f"{stamp}.json", chapters_json(ep), "application/json+chapters", "chapters"),
            ("transcripts", f"{stamp}.vtt", transcript_vtt(ep), "text/vtt", "transcript"),
        ):
            if content is None:
                continue
            (site_dir / folder).mkdir(exist_ok=True)
            (site_dir / folder / name).write_text(content, encoding="utf-8")
            el = etree.SubElement(item, f"{{{PODCAST_NS}}}{tag}")
            el.set("url", f"{site}/{folder}/{name}{query}")
            el.set("type", kind)
            if tag == "transcript":
                el.set("language", "nl")
    etree.indent(root)
    (site_dir / "feed.xml").write_bytes(etree.tostring(root, xml_declaration=True, encoding="UTF-8"))
