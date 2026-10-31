import re
from datetime import date, datetime
from zoneinfo import ZoneInfo

import trafilatura

from .llm import ask
from .plan import TopicPlan

DAYS = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
MONTHS = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus",
          "september", "oktober", "november", "december"]

SYSTEM = """Je bent de presentator van een Nederlandstalige solo-podcast, geschreven voor een tekst-naar-spraakstem. Het script moet klinken als iemand die vertelt, niet als iemand die een nieuwsbericht voorleest.
Stijl:
- Spreek de luisteraar consequent aan met "je" of "jij", alsof je tegen één persoon praat die je kent. Nooit "jullie", "beste luisteraars" of "wij".
- Gesproken taal: wissel korte, krachtige zinnen af met langere, genuanceerde. Stel af en toe een vraag. Geen kale opsomming van berichten; verbind ze tot een verhaal.
- Geen opmaak, kopjes, opsommingstekens, haakjes of regieaanwijzingen. De enige toegestane markeringen zijn de hoofdstukmarkers en pauzes zoals hieronder beschreven.
- Pauzes: schrijf `<break time="1.2s" />` vlak vóór een belangrijk kernpunt of direct na een ingewikkelde bewering, zodat de luisteraar kan nadenken. Maximaal 6 keer per aflevering.
- Schrijf getallen en bedragen uit zoals je ze uitspreekt ("twee komma vijf procent"). Afkortingen en namen schrijf je gewoon in hun normale schrijfwijze (ASML, Nvidia, ECB); de uitspraak wordt in een aparte stap geregeld. Gebruik waar het natuurlijk is liever de volledige Nederlandse naam ("de Europese Centrale Bank") dan alleen de afkorting.
Inhoud:
- Gebruik uitsluitend feiten uit het aangeleverde materiaal. Verzin niets en vul niets aan uit eigen kennis; wees eerlijk als iets onzeker is. Een duiding of takeaway mag, nieuwe feiten niet.
- Noem bedrijven en organisaties bij de eerste vermelding met hun volledige naam (bijvoorbeeld "ASM International", niet alleen "ASMI") en neem namen exact over uit het materiaal. Verwar nooit partijen met een vergelijkbare naam of afkorting; maak het onderscheid zo nodig expliciet ("ASM International, een ander bedrijf dan ASML"). Twijfel je over wie er bedoeld wordt, zeg dan wat de bron letterlijk meldt.
- Noem de bron kort in de zin ("meldt de NOS"), nooit een URL.
- Houd je aan de woordbudgetten (maximaal 10% afwijking). Gebruik natuurlijke overgangen tussen onderwerpen."""


STYLES = {
    "zakelijk": "Vertelstijl: zakelijk. Helder, feitelijk en beknopt; neutrale toon, geen uitroepen of kwinkslagen, nuchtere duiding. Je blijft wel \"je\" zeggen.",
    "informeel": "Vertelstijl: informeel. Warm en rechtstreeks, alsof je een vriend bijpraat; af en toe luchtig of een korte persoonlijke noot, maar de feiten blijven leidend.",
    "verhalend": "Vertelstijl: verhalend. Vertel het nieuws als een verhaal met een lijn: een beeldende opening per onderwerp, spanning en tegenstellingen, overgangen die de luisteraar meenemen. Verzin geen scènes of details die niet in het materiaal staan.",
}

BACKGROUND_RULE = """Is er te weinig nieuws voor het woordbudget, vul dan aan met relevante achtergrond en uitleg bij dat nieuws (context, hoe iets werkt, wat eraan voorafging). Maak die achtergrond herkenbaar als uitleg ("even terug in de tijd", "om dit te begrijpen helpt het om te weten dat …") en presenteer haar nooit als nieuws. Voeg nooit verzonnen nieuws of gebeurtenissen toe om tijd te vullen."""


def dutch_date(d: date) -> str:
    return f"{DAYS[d.weekday()]} {d.day} {MONTHS[d.month - 1]}"


def _article_text(link: str) -> str:
    try:
        raw = trafilatura.fetch_url(link)
        return (trafilatura.extract(raw) or "")[:5000] if raw else ""
    except Exception:
        return ""


def write_script(plans: list[TopicPlan], cfg: dict, today: date) -> tuple[str, str, str]:
    wpm = cfg["duration"]["words_per_minute"]
    blocks = []
    for p in plans:
        lines = [f"ONDERWERP: {p.name} — woordbudget: {round(p.minutes * wpm)} woorden"]
        for item, score in p.items:
            item.text = _article_text(item.link)
            lines.append(f"- [{item.source}] {item.title} (ca. {round(item.minutes * wpm)} woorden)\n  {item.text or item.summary}")
        blocks.append("\n".join(lines))
    material = "\n\n".join(blocks)
    cta = cfg["podcast"]["call_to_action"]
    system = SYSTEM
    if cfg.get("style") in STYLES:
        system += "\n" + STYLES[cfg["style"]]
    if cfg.get("fill_background"):
        system += "\n" + BACKGROUND_RULE
    period = ""
    if cfg.get("period"):
        start = datetime.fromtimestamp(cfg["period"]["from"], tz=ZoneInfo("Europe/Amsterdam")).date()
        period = (f"\nHet materiaal beslaat het nieuws van {dutch_date(start)} tot en met {dutch_date(today)}. "
                  "Zeg niet 'vandaag' tenzij iets echt vandaag gebeurde; benoem anders de dag of 'sinds de vorige aflevering'.\n")

    prompt = f"""Schrijf de podcastaflevering van {dutch_date(today)} van de podcast "{cfg['podcast']['title']}".{period}

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
    model = cfg["models"]["script"]
    raw = ask(prompt, model=model, system=system, max_tokens=16000,
              thinking={"type": "between_tools"})  # Sonnet 5.5: geen redeneerblok, anders slokt dat het hele tokenbudget op
    target = round(sum(p.minutes for p in plans) * wpm) + 350  # onderwerpen + opening en afsluiting
    words = len(raw.partition("\n---")[2].split())
    for _ in range(2):  # Claude schrijft vaak korter dan het budget: maximaal twee keer laten uitbreiden
        if words >= 0.9 * target:
            break
        print(f"Script te kort ({words} van ca. {target} woorden), laat uitbreiden")
        expanded = ask(f"""Hieronder staat je concept van de aflevering ({words} woorden). Het MOET ongeveer {target} woorden zijn,
dus er ontbreken ruim {target - words} woorden. Breid het uit tot die lengte: werk elk onderwerp uitgebreider uit met meer
context, achtergrond, nuance en duiding uit het MATERIAAL, en houd je aan de woordbudgetten per onderwerp. Voeg geen
feiten toe die niet in het materiaal staan en rek niet op met herhaling. Houd opbouw, hoofdstukmarkers en
antwoordformat (TITEL, SAMENVATTING, ---, script) exact gelijk.

CONCEPT:
{raw}

MATERIAAL:

{material}""", model=model, system=system, max_tokens=16000, thinking={"type": "between_tools"})
        new_words = len(expanded.partition("\n---")[2].split())
        if new_words <= words:
            break  # uitbreiding hielp niet: huidige versie houden
        raw, words = expanded, new_words
    if words > 1.1 * target:  # streefduur: hooguit 10% afwijking
        print(f"Script te lang ({words} van ca. {target} woorden), laat inkorten")
        shorter = ask(f"""Hieronder staat de aflevering ({words} woorden). Het mag hooguit {round(1.1 * target)} woorden zijn.
Kort in tot ongeveer {target} woorden: schrap herhaling en de minst belangrijke details. Behoud opbouw, hoofdstukmarkers,
de pauzes en het antwoordformat (TITEL, SAMENVATTING, ---, script) exact.

{raw}""", model=model, system=system, max_tokens=16000, thinking={"type": "between_tools"})
        short_words = len(shorter.partition("\n---")[2].split())
        if 0.9 * target <= short_words < words:
            raw, words = shorter, short_words
    print(f"Script: {words} woorden (doel ca. {target})")
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
