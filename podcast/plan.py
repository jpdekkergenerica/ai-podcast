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
10 = het belangrijkste nieuws van de dag voor deze luisteraar; 0 = irrelevant, clickbait of reclame.
Wees streng: op een gewone dag zijn er weinig berichten met 8 of hoger. Gaan meerdere berichten over
dezelfde gebeurtenis, geef dan alleen het beste bericht een hoge score.

{listing}

Antwoord uitsluitend met JSON: {{"scores": [{{"i": 0, "score": 7}}, ...]}}"""
    raw = ask(prompt, model=model, max_tokens=2000)
    scores = [0] * len(items)
    try:
        data = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
        for row in data["scores"]:
            if 0 <= row["i"] < len(items):
                scores[row["i"]] = max(0, min(10, int(row["score"])))
    except (ValueError, KeyError, TypeError):
        print(f"Waarschuwing: kon scores voor '{topic['name']}' niet lezen, onderwerp overgeslagen")
    return scores


def plan_episode(cfg: dict) -> list[TopicPlan]:
    rel, dur = cfg["relevance"], cfg["duration"]
    plans: list[TopicPlan] = []
    for topic in cfg["topics"]:
        items = fetch_topic(topic, rel["lookback_hours"], rel["max_candidates_per_topic"])
        if not items:
            continue
        scores = score_items(topic, items, cfg["models"]["scoring"])
        best = sorted(zip(items, scores), key=lambda p: -p[1])
        chosen = [p for p in best if p[1] >= rel["min_item_score"]][: rel["max_items_per_topic"]]
        plan = TopicPlan(topic["name"], chosen, sum(s for _, s in chosen))
        print(f"{topic['name']}: {len(items)} berichten, {len(chosen)} gekozen, relevantie {plan.points}")
        if chosen:
            plans.append(plan)

    # 2 tot 4 inhoudelijke blokken houdt een solo-aflevering overzichtelijk
    plans = sorted(plans, key=lambda p: -p.points)[: rel["max_topics"]]
    for p in plans:
        p.minutes = p.points * dur["minutes_per_point"]
    total = sum(p.minutes for p in plans)
    budget = dur["max_minutes"] - dur["intro_outro_minutes"]  # ruimte voor haak, intro en synthese
    if total > budget:
        for p in plans:
            p.minutes *= budget / total
    plans.sort(key=lambda p: -p.minutes)
    print(f"Totaal: {sum(p.minutes for p in plans):.1f} minuten")
    return plans
