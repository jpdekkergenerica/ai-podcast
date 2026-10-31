from dataclasses import dataclass, field
from datetime import date

from .discover import candidates_for_topic, read_own_sources
from .fetch import Item, fetch_topic
from .llm import ask_json
from .store import DEFAULT_STORE, ShowStore


@dataclass
class TopicPlan:
    name: str
    items: list[tuple[Item, int]] = field(default_factory=list)
    points: int = 0
    minutes: float = 0.0


def score_items(topic: dict, items: list[Item], model: str, focus: str) -> list[int | None]:
    listing = "\n".join(f"{i}. [{it.source}] {it.title} — {it.summary[:300]}" for i, it in enumerate(items))
    focus_rule = (f"Regionale focus: {focus}. Een bericht zonder duidelijke link met {focus} (geen Nederlandse organisatie,\n"
                  f"bedrijf, beleid, regio of gevolgen voor mensen in Nederland) krijgt maximaal 3.") if focus else ""
    prompt = f"""Interessegebied: {topic['name']}
Wat de luisteraar hierin interessant vindt: {topic['description']}

Beoordeel elk nieuwsbericht van 0 tot 10 op relevantie voor dit interessegebied én nieuwswaarde.
Gebruik een absolute schaal, zodat scores tussen interessegebieden vergelijkbaar zijn:
9-10 = groot nieuws met verregaande gevolgen, dat de hele nieuwsdag bepaalt; 7-8 = duidelijk belangrijk;
5-6 = interessant maar niet urgent; 3-4 = marginaal; 0-2 = irrelevant, clickbait of reclame.
Wees streng: op een gewone dag zijn er weinig berichten met 8 of hoger. Gaan meerdere berichten over
dezelfde gebeurtenis, geef dan alleen het beste bericht een hoge score.
Betrouwbaarheid telt mee: een bericht dat vooral onbevestigde claims, geruchten of reclame bevat, of dat afkomstig is van een
onbetrouwbare bron, krijgt maximaal 4. Oorspronkelijke en redactioneel verantwoorde bronnen gaan voor.
{focus_rule}

{listing}

Antwoord uitsluitend met JSON: {{"scores": [{{"i": 0, "score": 7}}, ...]}}"""
    data = ask_json(prompt, model=model, max_tokens=4000, required="scores", kind=list)
    scores: list[int | None] = [None] * len(items)
    for row in data["scores"]:
        if not isinstance(row, dict):
            continue
        try:
            i, score = int(row["i"]), int(row["score"])
        except (KeyError, TypeError, ValueError):
            continue
        if isinstance(row["i"], bool) or isinstance(row["score"], bool):
            continue
        if 0 <= i < len(items):
            scores[i] = max(0, min(10, score))
    if items and not any(s is not None for s in scores):
        raise RuntimeError(f"geen leesbare scores voor '{topic['name']}' ({len(items)} berichten)")
    missing = sum(s is None for s in scores)
    if missing:
        print(f"Waarschuwing: {missing} van {len(items)} berichten zonder score voor '{topic['name']}', "
              "die doen niet mee")
    return scores


def load_covered(today: date, days: int, store: ShowStore | None = None) -> list[dict]:
    """Berichten uit eerdere afleveringen van de laatste `days` dagen, vandaag meegerekend."""
    return (store or DEFAULT_STORE).load_covered(today, days)


def save_covered(today: date, plans: list["TopicPlan"], keep_days: int = 14,
                 store: ShowStore | None = None) -> None:
    (store or DEFAULT_STORE).save_covered(today, plans, keep_days=keep_days)


def drop_repeats(pool: list[tuple[Item, int]], covered: list[dict], model: str) -> list[tuple[Item, int]]:
    """Schrapt berichten die over hetzelfde nieuws gaan als een ander bericht (ook van een andere bron) of
    als iets wat de afgelopen dagen al is besproken. Een onderwerp mag wel terugkomen, met nieuw nieuws."""
    old_links = {c["link"] for c in covered}
    pool = [(it, s) for it, s in pool if it.link not in old_links]
    if len(pool) < 2 and not covered:
        return pool
    listing = "\n".join(f"{i}. [{it.topic}, score {s}] {it.title} — {it.summary[:150]}"
                        for i, (it, s) in enumerate(pool))
    old = "\n".join(f"- {c['title']}" for c in covered[-80:]) or "(niets)"
    prompt = f"""Je helpt een dagelijkse nieuwspodcast herhaling te voorkomen.
Geef de nummers van de kandidaten die geschrapt moeten worden, omdat ze:
1. over precies dezelfde gebeurtenis of hetzelfde nieuws gaan als een ander kandidaat, ook als de bron of
   de formulering anders is (bewaar alleen het bericht met de hoogste score; bij gelijke score het laagste nummer), of
2. dezelfde gebeurtenis opnieuw melden die in de lijst AL BESPROKEN staat, zonder wezenlijk nieuwe feiten of ontwikkeling.
Het thema van een bericht mag terugkomen; het gaat om hetzelfde nieuws. Een vervolg met nieuwe feiten schrap je niet.

AL BESPROKEN:
{old}

KANDIDATEN:
{listing}

Antwoord uitsluitend met JSON: {{"schrappen": [3, 7]}}"""
    data = ask_json(prompt, model=model, max_tokens=4000, required="schrappen", kind=list)
    drop: set[int] = set()
    for i in data["schrappen"]:
        if isinstance(i, bool):
            continue
        try:
            drop.add(int(i))
        except (TypeError, ValueError):
            continue
    print(f"Herhaling geschrapt: {len(drop & set(range(len(pool))))} van {len(pool)} berichten")
    return [p for i, p in enumerate(pool) if i not in drop]


def minutes_for(score: int, dur: dict, floor: int) -> float:
    """Spreektijd voor een bericht: loopt lineair van item_minutes_floor (laagste score) tot item_minutes_top (10)."""
    lo, hi = dur["item_minutes_floor"], dur["item_minutes_top"]
    return lo + (hi - lo) * (max(floor, min(10, score)) - floor) / (10 - floor)


def select(pool: list[tuple[Item, int]], budget: float, cfg: dict) -> list[TopicPlan]:
    """Vult de beschikbare tijd met de meest impactvolle berichten, over alle onderwerpen heen.

    Impact bepaalt zowel of een bericht meedoet als hoeveel tijd het krijgt; de tijd van een onderwerp is
    daarmee vanzelf de som van zijn berichten (veel en/of belangrijk nieuws = meer tijd). Daarna wordt alles
    geschaald zodat het totaal precies het budget is (hooguit max_stretch keer uitgebreider)."""
    rel, dur = cfg["relevance"], cfg["duration"]
    floor = rel["min_item_score"]
    chosen: list[tuple[Item, int, float]] = []
    per_topic: dict[str, int] = {}
    left = list(pool)
    total = 0.0

    def can_add(item: Item) -> bool:
        if item.topic not in per_topic and len(per_topic) >= rel["max_topics"]:
            return False
        return per_topic.get(item.topic, 0) < rel["max_items_per_topic"]

    def add(item: Item, score: int) -> None:
        nonlocal total
        left.remove((item, score))
        per_topic[item.topic] = per_topic.get(item.topic, 0) + 1
        t = minutes_for(score, dur, floor)
        chosen.append((item, score, t))
        total += t

    # 1. dekking: elk onderwerp met voldoende relevant nieuws krijgt eerst zijn beste bericht
    seeds: dict[str, tuple[Item, int]] = {}
    for item, score in pool:  # gesorteerd, dus de eerste per onderwerp is de beste
        if score >= rel["coverage_min_score"]:
            seeds.setdefault(item.topic, (item, score))
    for item, score in sorted(seeds.values(), key=lambda p: -p[1]):
        if total < budget and can_add(item):
            add(item, score)

    # 2. rest op impact, met afnemende meerwaarde: elk extra bericht van een onderwerp telt iets minder zwaar,
    #    zodat een zwaar onderwerp veel tijd krijgt zonder alle anderen te verdringen
    while total < budget:
        options = [(score - rel["topic_decay"] * per_topic.get(item.topic, 0), item, score)
                   for item, score in left if can_add(item)]
        if not options:
            break
        _, item, score = max(options, key=lambda o: o[0])
        add(item, score)
    if not chosen:
        return []

    factor = min(budget / total, dur["max_stretch"])
    plans: dict[str, TopicPlan] = {}
    for item, score, t in chosen:
        item.minutes = t * factor
        plan = plans.setdefault(item.topic, TopicPlan(item.topic))
        plan.items.append((item, score))
        plan.points += score
        plan.minutes += item.minutes
    return sorted(plans.values(), key=lambda p: -p.minutes)


def plan_episode(cfg: dict, today: date, store: ShowStore | None = None) -> list[TopicPlan]:
    rel, dur = cfg["relevance"], cfg["duration"]
    store = store or DEFAULT_STORE
    pool: list[tuple[Item, int]] = []
    own = read_own_sources(cfg.get("sources", {}).get("feeds", []), cfg["period"]["from"]) \
        if any(t.get("free_text") for t in cfg["topics"]) else []
    for topic in cfg["topics"]:
        if topic.get("free_text"):
            items = candidates_for_topic(topic, cfg, own, rel["max_candidates_per_topic"])
        else:
            items = fetch_topic(topic, rel["lookback_hours"], rel["max_candidates_per_topic"])
        if not items:
            continue
        scores = score_items(topic, items, cfg["models"]["scoring"], rel["focus"])
        usable = [(it, s) for it, s in zip(items, scores) if s is not None and s >= rel["min_item_score"]]
        known = [s for s in scores if s is not None]
        print(f"{topic['name']}: {len(items)} berichten, {len(usable)} bruikbaar, "
              f"hoogste score {max(known)}")
        pool += usable

    pool.sort(key=lambda p: -p[1])  # stabiel: bij gelijke score blijft de volgorde van de config
    seen: set[str] = set()
    unique = []
    for item, score in pool:  # hetzelfde bericht in twee onderwerpen: alleen de eerste (hoogste score)
        key = item.link or item.title
        if key not in seen:
            seen.add(key)
            unique.append((item, score))
    unique = drop_repeats(unique, store.load_covered(today, rel["repeat_days"]), cfg["models"]["scoring"])

    budget = dur["max_minutes"] - dur["intro_outro_minutes"]  # ruimte voor haak, intro en synthese
    plans = select(unique, budget, cfg)
    for p in plans:
        print(f"  {p.name}: {len(p.items)} berichten, {p.minutes:.1f} min")
    print(f"Totaal: {sum(p.minutes for p in plans):.1f} van {budget:.1f} minuten")
    return plans
