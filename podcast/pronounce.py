import json
import re
from pathlib import Path

from .llm import ask

STORE = Path("pronunciation.json")

PROMPT = """Je bereidt een Nederlands podcastscript voor op een tekst-naar-spraakstem. De stem leest afkortingen,
buitenlandse namen en cijfers vaak verkeerd voor (bijvoorbeeld een afkorting als woord in plaats van letter voor letter).

Zoek in de tekst de termen die een Nederlandse stem waarschijnlijk fout uitspreekt, en geef per term de schrijfwijze
die wel goed klinkt, zodat de voorlezer het uitspreekt zoals een Nederlandse nieuwslezer dat zou doen.

Neem ALLEEN termen op uit deze categorieën:
1. Afkortingen die in het Nederlands letter voor letter worden gezegd: schrijf de Nederlandse letternamen met koppeltekens
   (aa, bee, cee, dee, ee, ef, gee, haa, ie, jee, kaa, el, em, en, oo, pee, kuu, er, es, tee, uu, vee, wee, iks, ij, zet).
   Voorbeelden: ASML -> "aa-es-em-el", ECB -> "ee-cee-bee".
2. Afkortingen die als gewoon woord worden uitgesproken: schrijf ze met alleen een beginhoofdletter, zodat ze niet worden
   gespeld. Voorbeelden: NOS -> "Nos", NAVO -> "Navo", UNESCO -> "Unesco". Een stem leest ze anders letter voor letter.
3. Symbolen, eenheden en cijfercombinaties (%, €, km/u, "2G", "mld."): schrijf uit zoals je ze zegt.
4. Buitenlandse bedrijfs- en productnamen waarvan de Nederlandse uitspraak sterk afwijkt van de spelling.

Neem NOOIT op (een stem leest ze zelf goed, en een herschrijving maakt het slechter):
- gewone Nederlandse woorden, ingeburgerde leenwoorden (app, podcast, computer, intensive care) en gewone woorden in kleine letters;
- landen, steden en plaatsnamen (China, Zeist), ook buitenlandse;
- Nederlandse of bekende persoonsnamen en namen van media en organisaties die als woord klinken;
- termen die je alleen anders schrijft maar niet anders uitspreekt.
Twijfel je, laat de term dan weg: liever te weinig dan te veel. De term moet exact zo in de tekst staan (hoofdlettergevoelig).
Maximaal 40 termen, de belangrijkste eerst.

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
            and k != v and not (k.lower() == v.lower() and not k.isupper()) and re.search(r"[A-Z0-9]", k) and len(k) <= 40 and k in text and k not in known}


SAFE = re.compile(r"^[A-Z0-9][A-Z0-9.&-]*(\.nl|\.com)?$|^\d")


def persistable(new: dict[str, str]) -> dict[str, str]:
    """Alleen afkortingen, cijfercombinaties en domeinnamen worden bewaard; namen en woorden bepaalt Claude steeds
    opnieuw, zodat een eenmalige misser niet elke volgende aflevering vergiftigt."""
    return {k: v for k, v in new.items() if SAFE.match(k)}


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
