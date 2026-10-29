from datetime import date

import trafilatura

from .llm import ask
from .plan import TopicPlan

DAYS = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
MONTHS = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus",
          "september", "oktober", "november", "december"]

SYSTEM = """Je bent de presentator van een dagelijkse Nederlandstalige nieuwspodcast, geschreven om voor te lezen door een tekst-naar-spraakstem.
Regels:
- Schrijf gesproken taal: korte zinnen, direct, warm maar zakelijk. Geen opmaak, kopjes, opsommingstekens, haakjes of regieaanwijzingen.
- Schrijf getallen, bedragen en afkortingen uit zoals je ze uitspreekt ("twee komma vijf procent", "de Europese Centrale Bank").
- Gebruik uitsluitend feiten uit het aangeleverde materiaal. Verzin niets en vul niets aan uit eigen kennis; wees eerlijk als iets onzeker is.
- Noem de bron kort in de zin ("meldt de NOS"), nooit een URL.
- Houd je per onderwerp aan het opgegeven woordbudget (maximaal 10% afwijking). Gebruik natuurlijke overgangen tussen onderwerpen."""


def dutch_date(d: date) -> str:
    return f"{DAYS[d.weekday()]} {d.day} {MONTHS[d.month - 1]}"


def _article_text(link: str) -> str:
    try:
        raw = trafilatura.fetch_url(link)
        return (trafilatura.extract(raw) or "")[:2500] if raw else ""
    except Exception:
        return ""


def write_script(plans: list[TopicPlan], cfg: dict, today: date) -> tuple[str, str, str]:
    wpm = cfg["duration"]["words_per_minute"]
    blocks = []
    for p in plans:
        lines = [f"ONDERWERP: {p.name} — woordbudget: {round(p.minutes * wpm)} woorden"]
        for item, score in p.items:
            item.text = _article_text(item.link)
            lines.append(f"- [{item.source}] {item.title}\n  {item.text or item.summary}")
        blocks.append("\n".join(lines))
    material = "\n\n".join(blocks)

    prompt = f"""Schrijf de podcastaflevering van {dutch_date(today)}, titel van de podcast: "{cfg['podcast']['title']}".
Begin met een korte begroeting met de datum en een zin over wat er aan bod komt, sluit af met één korte afsluiting.
De onderwerpen staan in volgorde van belang; behandel ze in die volgorde.

Gebruik exact dit antwoordformat:
TITEL: <pakkende titel van max. 70 tekens, zonder datum>
SAMENVATTING: <één of twee zinnen voor in de podcast-app>
---
<het volledige uitgesproken script>

MATERIAAL:

{material}"""
    raw = ask(prompt, model=cfg["models"]["script"], system=SYSTEM, max_tokens=8000)
    head, _, script = raw.partition("\n---")
    title = summary = ""
    for line in head.splitlines():
        if line.startswith("TITEL:"):
            title = line.removeprefix("TITEL:").strip()
        elif line.startswith("SAMENVATTING:"):
            summary = line.removeprefix("SAMENVATTING:").strip()
    if not script.strip():
        raise RuntimeError("Claude gaf geen script terug in het verwachte formaat:\n" + raw[:500])
    return title or dutch_date(today), summary, script.strip()
