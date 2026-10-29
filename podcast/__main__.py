import argparse
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from .audio import master, seconds_for, tag_chapters
from .feed import save_episode, write_site
from .plan import TopicPlan, plan_episode, save_covered
from .pronounce import load_learned, prepare, save_learned
from .script import split_chapters, write_script
from .tts import synthesize

AI_NOTE = "Deze aflevering is automatisch met AI samengesteld en wordt ingesproken door een synthetische stem."


def describe(summary: str, chapters: list[str], plans: list[TopicPlan]) -> str:
    """De eerste 250 tekens (de samenvatting) zijn wat apps tonen; daarna de rest."""
    sources = sorted({item.source for p in plans for item, _ in p.items})
    return (f"{summary}\n\nIn deze aflevering: {'; '.join(chapters)}.\n\n"
            f"Bronnen: {', '.join(sources)}.\n\n{AI_NOTE}")


def build(cfg: dict, out: Path, no_tts: bool) -> None:
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(ZoneInfo("Europe/Amsterdam"))
    today = now.date()
    plans = plan_episode(cfg, today)
    if not plans:
        print("Geen relevant nieuws vandaag, geen aflevering.")
        return

    title, summary, script = write_script(plans, cfg, today)
    chapters = split_chapters(script)
    (out / "script.txt").write_text(script)
    print(f"\n{title}\n{summary}\n({len(script.split())} woorden, {len(chapters)} hoofdstukken)")
    spoken, new_terms = prepare(chapters, cfg)  # uitspraak: afkortingen, buitenlandse namen, symbolen
    (out / "script_uitgesproken.txt").write_text("\n\n".join(spoken))
    print("Uitspraak (nieuw): " + (", ".join(f"{k} -> {v}" for k, v in new_terms.items()) or "geen"))
    if no_tts:
        print("\n" + "\n\n".join(spoken))
        return
    save_learned({**load_learned(), **new_terms})

    audio = [synthesize(text, cfg) for text in spoken]
    # unieke id per run: een opnieuw gemaakte aflevering van dezelfde dag moet voor apps een nieuwe aflevering zijn
    stamp = now.strftime("%Y-%m-%d-%H%M")
    raw, mp3 = out / f"{stamp}.raw.mp3", out / f"{stamp}.mp3"
    raw.write_bytes(b"".join(audio))
    master(raw, mp3)

    starts, t = [], 0.0
    for chunk in audio:
        starts.append(t)
        t += seconds_for(len(chunk))
    ends = starts[1:] + [t]
    duration = round(seconds_for(mp3.stat().st_size))
    tag_chapters(mp3, [(c[0], round(s * 1000), round(e * 1000)) for c, s, e in zip(chapters, starts, ends)])

    save_episode({
        "guid": f"episode-{stamp}",
        "date": today.isoformat(),
        "published": now.isoformat(timespec="seconds"),
        "title": title,
        "summary": describe(summary, [c[0] for c in chapters], plans),
        "tag": f"ep-{stamp}",
        "file": mp3.name,
        "size": mp3.stat().st_size,
        "duration": duration,
    })
    save_covered(today, plans)
    (out / "tag.txt").write_text(f"ep-{stamp}")


def main() -> None:
    ap = argparse.ArgumentParser(prog="podcast")
    ap.add_argument("command", choices=["build", "feed", "ui"])
    ap.add_argument("--port", type=int, default=8765, help="poort voor de instellingenpagina (ui)")
    ap.add_argument("--no-browser", action="store_true", help="de instellingenpagina niet automatisch openen (ui)")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--out", default="out")
    ap.add_argument("--no-tts", action="store_true", help="alleen het script maken (geen ElevenLabs-kosten, geen feed)")
    args = ap.parse_args()

    if args.command == "ui":
        from .ui import serve  # alleen nodig voor de pagina (ruamel.yaml)
        return serve(args.port, open_browser=not args.no_browser)

    cfg = yaml.safe_load(Path(args.config).read_text())
    if os.environ.get("MAX_MINUTES", "").strip():  # override vanuit de workflow-invoer
        cfg["duration"]["max_minutes"] = float(os.environ["MAX_MINUTES"])
        print(f"Duur overschreven: {cfg['duration']['max_minutes']} minuten")
    out = Path(args.out)
    if args.command == "build":
        build(cfg, out, args.no_tts)
    if not args.no_tts:
        write_site(cfg, out / "site")


if __name__ == "__main__":
    main()
