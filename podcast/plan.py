import json
from dataclasses import dataclass, field

from .fetch import Item, fetch_topic
from .llm import ask


@dataclass
class TopicPlan:
    name: str
    items: list[tuple[Item, int]] = field(default_factory=list)
    points: int = 0
    minutes: float = 0.0


def score_items(topic: dict, items: list[Item], model: str) -> list[int]:
    listing = "\n".join(f"{i}. [{it.source}] {it.title} — {it.summary[:300]}" for i, it in enumerate(items))
    prompt = f"""Interessegebied: {topic['name']}
Wat de luisteraar hierin interessant vindt: {topic['description']}

Beoordeel elk nieuwsbericht van 0 tot 10 op relevantie voor dit interessegebied én nieuwswaarde.
Gebruik een absolute schaal, zodat scores tussen interessegebieden vergelijkbaar zijn:
9-10 = groot nieuws met verregaande gevolgen, dat de hele nieuwsdag bepaalt; 7-8 = duidelijk belangrijk;
5-6 = interessant maar niet urgent; 3-4 = marginaal; 0-2 = irrelevant, clickbait of reclame.
Wees streng: op een gewone dag zijn er weinig berichten met 8 of hoger. Gaan meerdere berichten over
dezelfde gebeurtenis, geef dan alleen het beste bericht een hoge score.

{listing}

Antwoord uitsluitend met JSON: {{"scores": [{{"i": 0, "score": 7}}, ...]}}"""
    raw = ask(prompt, model=model, max_tokens=4000)
    scores = [0] * len(items)
    try:
        data = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
        for row in data["scores"]:
            if 0 <= row["i"] < len(items):
                scores[row["i"]] = max(0, min(10, int(row["score"])))
    except (ValueError, KeyError, TypeError):
        print(f"Waarschuwing: kon scores voor '{topic['name']}' niet lezen, onderwerp overgeslagen")
    return scores


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


def plan_episode(cfg: dict) -> list[TopicPlan]:
    rel, dur = cfg["relevance"], cfg["duration"]
    pool: list[tuple[Item, int]] = []
    for topic in cfg["topics"]:
        items = fetch_topic(topic, rel["lookback_hours"], rel["max_candidates_per_topic"])
        if not items:
            continue
        scores = score_items(topic, items, cfg["models"]["scoring"])
        usable = [(it, s) for it, s in zip(items, scores) if s >= rel["min_item_score"]]
        print(f"{topic['name']}: {len(items)} berichten, {len(usable)} bruikbaar, "
              f"hoogste score {max(scores)}")
        pool += usable

    pool.sort(key=lambda p: -p[1])  # stabiel: bij gelijke score blijft de volgorde van de config
    seen: set[str] = set()
    unique = []
    for item, score in pool:  # hetzelfde bericht in twee onderwerpen: alleen de eerste (hoogste score)
        key = item.link or item.title
        if key not in seen:
            seen.add(key)
            unique.append((item, score))

    budget = dur["max_minutes"] - dur["intro_outro_minutes"]  # ruimte voor haak, intro en synthese
    plans = select(unique, budget, cfg)
    for p in plans:
        print(f"  {p.name}: {len(p.items)} berichten, {p.minutes:.1f} min")
    print(f"Totaal: {sum(p.minutes for p in plans):.1f} van {budget:.1f} minuten")
    return plans
