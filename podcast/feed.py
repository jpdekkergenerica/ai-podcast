import hashlib
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
    eps = [e for e in load_episodes() if e["date"] != ep["date"]] + [ep]  # één aflevering per dag; opnieuw draaien vervangt
    eps.sort(key=lambda e: e["date"], reverse=True)
    EPISODES.write_text(json.dumps(eps, ensure_ascii=False, indent=2) + "\n")


def _urls(cfg: dict) -> tuple[str, str, str]:
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


def write_site(cfg: dict, site_dir: Path) -> None:
    p = cfg["podcast"]
    site, media, _ = _urls(cfg)
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
    fg.link(href=f"{site}/feed.xml", rel="self")
    fg.language(p["language"])
    fg.podcast.itunes_author(p["author"])
    fg.podcast.itunes_owner(name=p["author"], email=p["email"])
    fg.podcast.itunes_image(f"{site}/{cover}")
    fg.podcast.itunes_category("News", "Daily News")
    fg.podcast.itunes_explicit("no")

    tz = ZoneInfo("Europe/Amsterdam")
    for ep in load_episodes():
        fe = fg.add_entry(order="append")
        fe.id(ep["guid"])
        fe.guid(ep["guid"], permalink=False)
        fe.title(ep["title"])
        fe.description(ep["summary"])
        published = datetime.fromisoformat(ep.get("published") or ep["date"]).replace(tzinfo=None)
        fe.pubDate(published.replace(tzinfo=tz) if "published" in ep else published.replace(hour=6, tzinfo=tz))
        fe.enclosure(f"{media}/{ep['tag']}/{ep['file']}", str(ep["size"]), "audio/mpeg")
        fe.podcast.itunes_duration(_hms(ep["duration"]))
    fg.rss_file(str(site_dir / "feed.xml"), pretty=True)
    print(f"Feed geschreven: {site}/feed.xml ({len(load_episodes())} afleveringen)")
