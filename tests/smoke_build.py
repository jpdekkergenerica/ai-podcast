"""Rooktest van de volledige build-route met nagebootste Claude en ElevenLabs.

Gebruik (vanuit de projectmap, ffmpeg nodig):  python -m tests.smoke_build
Draait in een tijdelijke map, dus raakt episodes.json, covered.json en pronunciation.json niet aan.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from podcast import __main__ as app  # noqa: E402
from podcast.fetch import Item  # noqa: E402
from podcast.plan import TopicPlan  # noqa: E402


def main() -> None:
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text())
    cfg["podcast"]["repository"] = "x/y"
    tmp = Path(tempfile.mkdtemp())
    os.chdir(tmp)
    for i, f in enumerate((330, 220)):
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"sine=f={f}:d=6", "-ac", "1",
                        "-ar", "44100", "-b:a", "128k", f"s{i}.mp3"], check=True)

    item = Item("Onderwerp", "Kop", "samenvatting", "https://x/1", "Bron")
    item.minutes = 2.0
    plans = [TopicPlan("Onderwerp", [(item, 7)], 7, 2.0)]
    chapters = [("Opening", "Tekst een"), ("Onderwerp: nieuws", "Tekst twee"), ("Samenvatting", "Slot")]
    audio = iter([Path("s0.mp3").read_bytes(), Path("s1.mp3").read_bytes(), Path("s0.mp3").read_bytes()])

    app.plan_episode = lambda cfg, today: plans
    app.write_script = lambda plans, cfg, today: ("Titel?", "Samenvatting.", "script")
    app.split_chapters = lambda script: chapters
    app.prepare = lambda chapters, cfg: ([t for _, t in chapters], {"ASML": "aa-es-em-el"})
    app.synthesize = lambda text, cfg: next(audio)

    app.build(cfg, Path("out"), no_tts=False)
    app.write_site(cfg, Path("out/site"))

    ep = json.loads(Path("episodes.json").read_text())[0]
    tag = Path("out/tag.txt").read_text()
    assert ep["tag"] == tag and ep["file"] == f"{tag.removeprefix('ep-')}.mp3", ep
    assert Path("out", ep["file"]).exists() and ep["size"] == Path("out", ep["file"]).stat().st_size
    assert ep["guid"] == f"episode-{tag.removeprefix('ep-')}" and ep["duration"] > 10
    assert json.loads(Path("pronunciation.json").read_text()) == {"ASML": "aa-es-em-el"}
    assert json.loads(Path("covered.json").read_text())[0]["title"] == "Kop"
    feed = Path("out/site/feed.xml").read_text()
    assert f"/audio/{ep['file']}" in feed and ep["guid"] in feed
    stamp = tag.removeprefix("ep-")
    assert [c["title"] for c in ep["chapters"]] == [c[0] for c in chapters] and ep["sources"][0]["link"] == "https://x/1"
    assert json.loads(Path(f"out/site/chapters/{stamp}.json").read_text())["chapters"][1]["title"] == "Onderwerp: nieuws"
    vtt = Path(f"out/site/transcripts/{stamp}.vtt").read_text()
    assert vtt.startswith("WEBVTT") and "Tekst twee" in vtt
    assert "podcast:chapters" in feed and "podcast:transcript" in feed and 'href="https://x/1"' in feed
    print("OK: build, opslaan en feed kloppen ->", ep["guid"], f"{ep['duration']} s")


if __name__ == "__main__":
    main()
