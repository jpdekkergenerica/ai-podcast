import json
import re
from pathlib import Path

from .llm import ask

STORE = Path("pronunciation.json")

PROMPT = """Je bereidt een Nederlands podcastscript voor op een tekst-naar-spraakstem. De stem leest afkortingen,
buitenlandse namen en cijfers vaak verkeerd voor (bijvoorbeeld een afkorting als woord in plaats van letter voor letter).

Zoek in de tekst de termen die een Nederlandse stem waarschijnlijk fout uitspreekt, en geef per term de schrijfwijze
die wel goed klinkt, zodat de voorlezer het uitspreekt zoals een Nederlandse nieuwslezer dat zou doen.

Regels:
- Afkorting die in het Nederlands letter voor letter wordt gezegd: schrijf de Nederlandse letternamen met koppeltekens
  (aa, bee, cee, dee, ee, ef, gee, haa, ie, jee, kaa, el, em, en, oo, pee, kuu, er, es, tee, uu, vee, wee, iks, ij, zet).
  Voorbeelden: ASML -> "aa-es-em-el", ECB -> "ee-cee-bee".
- Afkorting die als woord wordt gezegd (zoals NAVO, AOW): alleen opnemen als een stem die vermoedelijk fout leest; schrijf dan fonetisch.
- Buitenlandse bedrijfs-, product-, plaats- en persoonsnamen: schrijf fonetisch in Nederlandse spelling zoals een Nederlander ze uitspreekt.
- Symbolen, eenheden, cijfercombinaties en afgekorte woorden (%, €, km/u, "2G", "bijv.", "mld."): schrijf uit zoals je ze zegt.
- Gewone Nederlandse woorden, en termen die een stem al goed leest, neem je NIET op. Wijzig niets anders aan de tekst.
- De term moet exact zo in de tekst staan (hoofdlettergevoelig). Maximaal 60 termen, de belangrijkste eerst.

Deze termen zijn al vastgelegd, noem ze niet opnieuw:
{known}

TEKST:
{text}

Antwoord uitsluitend met JSON: {{"uitspraak": {{"term": "gesproken vorm", ...}}}}"""


def load_learned() -> dict[str, str]:
    return json.loads(STORE.read_text()) if STORE.exists() else {}


def save_learned(learned: dict[str, str]) -> None:
    STORE.write_text(json.dumps(dict(sorted(learned.items())), ensure_ascii=False, indent=1) + "\n")


def detect(text: str, known: dict[str, str], model: str) -> dict[str, str]:
    """Vraagt Claude welke termen in de tekst een Nederlandse stem waarschijnlijk fout uitspreekt."""
    prompt = PROMPT.format(known=", ".join(sorted(known)) or "(geen)", text=text)
    raw = ask(prompt, model=model, max_tokens=4000, thinking={"type": "between_tools"})
    try:
        data = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])["uitspraak"]
    except (ValueError, KeyError, TypeError):
        print("Waarschuwing: kon de uitspraaklijst niet lezen, geen uitspraakcorrecties toegepast")
        return {}
    return {k: v for k, v in data.items()
            if isinstance(k, str) and isinstance(v, str) and k.strip() and v.strip()
            and k.lower() != v.lower() and len(k) <= 40 and k in text and k not in known}


def apply(text: str, mapping: dict[str, str]) -> str:
    if not mapping:
        return text
    terms = sorted(mapping, key=len, reverse=True)  # langste eerst: "AI-tool" voor "AI"
    pattern = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(t) for t in terms) + r")(?!\w)")
    return pattern.sub(lambda m: mapping[m.group(0)], text)


def prepare(chapters: list[tuple[str, str]], cfg: dict) -> tuple[list[str], dict[str, str]]:
    """Geeft de uitgesproken tekst per hoofdstuk en de nieuw geleerde termen.
    Prioriteit: config (`pronunciation`) > eerder geleerd > nieuw. Hoofdstuktitels blijven ongewijzigd."""
    fixed = {**load_learned(), **cfg.get("pronunciation", {})}
    full = "\n\n".join(text for _, text in chapters)
    new = detect(full, fixed, cfg["models"]["script"])
    mapping = {**new, **fixed}
    return [apply(text, mapping) for _, text in chapters], new
