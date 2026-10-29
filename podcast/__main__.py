import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from mutagen.mp3 import MP3

from .feed import save_episode, write_site
from .plan import plan_episode
from .script import write_script
from .tts import synthesize


def build(cfg: dict, out: Path, no_tts: bool) -> None:
    out.mkdir(parents=True, exist_ok=True)
    today = datetime.now(ZoneInfo("Europe/Amsterdam")).date()
    plans = plan_episode(cfg)
    if not plans:
        print("Geen relevant nieuws vandaag, geen aflevering.")
        return

    title, summary, script = write_script(plans, cfg, today)
    (out / "script.txt").write_text(script)
    print(f"\n{title}\n{summary}\n({len(script.split())} woorden)")
    if no_tts:
        print("\n" + script)
        return

    filename = f"{today.isoformat()}.mp3"
    mp3 = out / filename
    synthesize(script, cfg, mp3)
    save_episode({
        "guid": f"episode-{today.isoformat()}",
        "date": today.isoformat(),
        "title": title,
        "summary": summary,
        "tag": f"ep-{today.isoformat()}",
        "file": filename,
        "size": mp3.stat().st_size,
        "duration": int(MP3(mp3).info.length),
    })
    (out / "tag.txt").write_text(f"ep-{today.isoformat()}")


def main() -> None:
    ap = argparse.ArgumentParser(prog="podcast")
    ap.add_argument("command", choices=["build", "feed"])
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out", default="out")
    ap.add_argument("--no-tts", action="store_true", help="alleen het script maken (geen ElevenLabs-kosten, geen feed)")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())
    out = Path(args.out)
    if args.command == "build":
        build(cfg, out, args.no_tts)
    if not args.no_tts:
        write_site(cfg, out / "site")


if __name__ == "__main__":
    main()
