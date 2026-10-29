import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from feedgen.feed import FeedGenerator
from PIL import Image, ImageDraw, ImageFont

EPISODES = Path("episodes.json")


def load_episodes() -> list[dict]:
    return json.loads(EPISODES.read_text()) if EPISODES.exists() else []


def save_episode(ep: dict) -> None:
    eps = [e for e in load_episodes() if e["guid"] != ep["guid"]] + [ep]
    eps.sort(key=lambda e: e["date"], reverse=True)
    EPISODES.write_text(json.dumps(eps, ensure_ascii=False, indent=2) + "\n")


def _urls(cfg: dict) -> tuple[str, str, str]:
    repo = os.environ.get("GITHUB_REPOSITORY") or cfg["podcast"]["repository"]
    owner, name = repo.split("/")
    site = f"https://{owner}.github.io/{name}"
    return site, f"https://github.com/{owner}/{name}/releases/download", repo


def _hms(seconds: int) -> str:
    return f"{seconds // 3600}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def make_cover(title: str, dest: Path) -> None:
    size = 1600
    img = Image.new("RGB", (size, size), "#1f3a5f")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=170)
    words, lines, cur = title.split(), [], ""
    for w in words:
        if cur and draw.textlength(f"{cur} {w}", font=font) > size - 240:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    lines.append(cur)
    y = (size - len(lines) * 200) // 2
    for line in lines:
        draw.text(((size - draw.textlength(line, font=font)) / 2, y), line, fill="white", font=font)
        y += 200
    img.save(dest, "JPEG", quality=90)


def write_site(cfg: dict, site_dir: Path) -> None:
    p = cfg["podcast"]
    site, media, _ = _urls(cfg)
    site_dir.mkdir(parents=True, exist_ok=True)
    make_cover(p["title"], site_dir / "cover.jpg")

    fg = FeedGenerator()
    fg.load_extension("podcast")
    fg.title(p["title"])
    fg.description(p["description"])
    fg.link(href=site, rel="alternate")
    fg.link(href=f"{site}/feed.xml", rel="self")
    fg.language(p["language"])
    fg.podcast.itunes_author(p["author"])
    fg.podcast.itunes_owner(name=p["author"], email=p["email"])
    fg.podcast.itunes_image(f"{site}/cover.jpg")
    fg.podcast.itunes_category("News", "Daily News")
    fg.podcast.itunes_explicit("no")

    tz = ZoneInfo("Europe/Amsterdam")
    for ep in load_episodes():
        fe = fg.add_entry(order="append")
        fe.id(ep["guid"])
        fe.guid(ep["guid"], permalink=False)
        fe.title(ep["title"])
        fe.description(ep["summary"])
        fe.pubDate(datetime.fromisoformat(ep["date"]).replace(hour=6, tzinfo=tz))
        fe.enclosure(f"{media}/{ep['tag']}/{ep['file']}", str(ep["size"]), "audio/mpeg")
        fe.podcast.itunes_duration(_hms(ep["duration"]))
    fg.rss_file(str(site_dir / "feed.xml"), pretty=True)
    print(f"Feed geschreven: {site}/feed.xml ({len(load_episodes())} afleveringen)")
