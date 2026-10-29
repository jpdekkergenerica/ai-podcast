import re
from datetime import date

import trafilatura

from .llm import ask
from .plan import TopicPlan

DAYS = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
MONTHS = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus",
          "september", "oktober", "november", "december"]

SYSTEM = """Je bent de presentator van een dagelijkse Nederlandstalige solo-podcast, geschreven voor een tekst-naar-spraakstem. Het script moet klinken als iemand die vertelt, niet als iemand die een nieuwsbericht voorleest.
Stijl:
- Spreek de luisteraar consequent aan met "je" of "jij", alsof je tegen één persoon praat die je kent. Nooit "jullie", "beste luisteraars" of "wij".
- Gesproken taal: wissel korte, krachtige zinnen af met langere, genuanceerde. Stel af en toe een vraag. Geen kale opsomming van berichten; verbind ze tot een verhaal.
- Geen opmaak, kopjes, opsommingstekens, haakjes of regieaanwijzingen. De enige toegestane markeringen zijn de hoofdstukmarkers en pauzes zoals hieronder beschreven.
- Pauzes: schrijf `<break time="1.2s" />` vlak vóór een belangrijk kernpunt of direct na een ingewikkelde bewering, zodat de luisteraar kan nadenken. Maximaal 6 keer per aflevering.
- Schrijf getallen, bedragen en afkortingen uit zoals je ze uitspreekt ("twee komma vijf procent", "de Europese Centrale Bank").
Inhoud:
- Gebruik uitsluitend feiten uit het aangeleverde materiaal. Verzin niets en vul niets aan uit eigen kennis; wees eerlijk als iets onzeker is. Een duiding of takeaway mag, nieuwe feiten niet.
- Noem de bron kort in de zin ("meldt de NOS"), nooit een URL.
- Houd je aan de woordbudgetten (maximaal 10% afwijking). Gebruik natuurlijke overgangen tussen onderwerpen."""


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
    cta = cfg["podcast"]["call_to_action"]

    prompt = f"""Schrijf de podcastaflevering van {dutch_date(today)} van de podcast "{cfg['podcast']['title']}".

Opbouw, in deze volgorde:
1. OPENING (ca. 110-130 woorden): begin direct met de haak. Binnen ongeveer 45 seconden weet de luisteraar wat de centrale vraag of het grootste verhaal van vandaag is, waarom dat nú relevant is en wat het luisteren oplevert. Geen opwarmpraatje en niet beginnen met "welkom bij". Pas daarna één korte zin als showintro (de podcastnaam en de datum).
2. ONDERWERPBLOKKEN, in de volgorde van het materiaal (belangrijkste eerst). Bouw elk blok zo op: wat er speelt en waarom nu; context of een concreet voorbeeld; het kernpunt; de complicatie, onzekerheid of het tegenargument; en sluit af met één zin takeaway (wat betekent dit voor jou, of wat houd je in de gaten).
3. AFSLUITING (ca. 180-250 woorden): een beknopte synthese van de belangrijkste inzichten van vandaag, en daarna precies één concrete oproep tot actie: "{cta}". Geen tweede of derde oproep.

Hoofdstukmarkers: begin elk onderdeel met een aparte regel `[[HOOFDSTUK: titel]]`. Titel maximaal 40 tekens, beschrijvend (bijvoorbeeld "Midterms: wie staat er voor?"). Het eerste hoofdstuk heet "Opening", het laatste "Samenvatting".

Gebruik exact dit antwoordformat:
TITEL: <de concrete vraag of kwestie waarop deze aflevering antwoord geeft, zoals iemand het zou opzoeken; max. 70 tekens; zonder podcastnaam, datum of afleveringsnummer>
SAMENVATTING: <maximaal twee volledige zinnen; de eerste 250 tekens noemen direct de kernantwoorden en onderwerpen; herhaal de titel niet; geen trefwoordenlijst>
---
<het volledige uitgesproken script met hoofdstukmarkers>

MATERIAAL:

{material}"""
    raw = ask(prompt, model=cfg["models"]["script"], system=SYSTEM, max_tokens=16000)
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


def split_chapters(script: str) -> list[tuple[str, str]]:
    """Splitst het script op hoofdstukmarkers in (titel, tekst); zonder markers is het één hoofdstuk."""
    parts = re.split(r"^\s*\[\[HOOFDSTUK:\s*(.+?)\s*\]\]\s*$", script, flags=re.M)
    chapters = [("Opening", parts[0].strip())] if parts[0].strip() else []
    for i in range(1, len(parts), 2):
        text = parts[i + 1].strip()
        if text:
            chapters.append((parts[i][:45], text))
    return chapters or [("Aflevering", script)]
