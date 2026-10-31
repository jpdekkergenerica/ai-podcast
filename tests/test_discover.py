"""Tests voor nieuws bij vrije-tekstonderwerpen, de stijlen en de nieuwsperiode.

Gebruik (vanuit de projectmap):  python -m tests.test_discover
Geen netwerk en geen API-sleutel.
"""
import json
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import podcast.discover as discover  # noqa: E402
import podcast.llm as llm  # noqa: E402
import podcast.plan as plan  # noqa: E402
import podcast.script as script  # noqa: E402
from podcast.fetch import Item  # noqa: E402

NOW = time.time()
DAY = 86400


def fake_search(items: list[dict], seen: list[str]):
    calls = []

    def ask(prompt, *, model, system="", max_tokens=8000, max_uses=5):
        calls.append({"prompt": prompt, "system": system, "model": model})
        return json.dumps({"items": items}), set(seen)

    ask.calls = calls
    return ask


def row(title, url, published, source="NOS"):
    return {"title": title, "summary": "Twee zinnen.", "url": url, "source": source, "published": published}


def iso(days_ago: float) -> str:
    return datetime.fromtimestamp(NOW - days_ago * DAY, tz=timezone.utc).strftime("%Y-%m-%d")


def test_alleen_adressen_uit_de_zoekresultaten_doen_mee() -> None:
    ask = fake_search(
        [row("Echt bericht", "https://nos.nl/a/", iso(0.5)),
         row("Verzonnen bericht", "https://verzonnen.example/x", iso(0.5)),
         row("Te oud", "https://nos.nl/oud", iso(9))],
        ["https://nos.nl/a", "https://nos.nl/oud"])
    items = discover.discover_topic("AI-regelgeving", NOW - 2 * DAY, 8, "model", ask=ask)
    assert [i.title for i in items] == ["Echt bericht"]  # verzonnen adres en bericht van vóór de periode vallen af
    assert items[0].topic == "AI-regelgeving" and items[0].source == "NOS"
    prompt = ask.calls[0]["prompt"]
    assert "AI-regelgeving" in prompt and discover.datetime.fromtimestamp(NOW - 2 * DAY, tz=timezone.utc).strftime("%Y-%m-%d") in prompt
    assert "betrouwbaar" in ask.calls[0]["system"].lower() and "Verzin niets" in ask.calls[0]["system"]


def test_kapotte_of_lege_modeluitvoer_geeft_geen_nieuws_en_geen_fout() -> None:
    for raw in ("geen json", '{"items": "nee"}', '{"items": []}', ""):
        ask = lambda prompt, **kw: (raw, set())  # noqa: E731
        assert discover.discover_topic("X", NOW - DAY, 5, "m", ask=ask) == []


def test_eigen_bronnen_en_gevonden_nieuws_worden_gecombineerd_zonder_dubbelen() -> None:
    own = [Item("", "Uit eigen bron", "s", "https://eigen.example/1", "Eigen", published=NOW - 3600),
           Item("", "Dubbel", "s", "https://nos.nl/a", "Eigen", published=NOW - 7200)]
    ask = fake_search([row("Dubbel", "https://nos.nl/a", iso(0.2)), row("Extra", "https://nu.nl/b", iso(0.3), "NU.nl")],
                      ["https://nos.nl/a", "https://nu.nl/b"])
    cfg = {"period": {"from": NOW - 2 * DAY}, "models": {"script": "m"}, "sources": {"domains": ["https://blog.example/"]}}
    got = discover.candidates_for_topic({"name": "Thema"}, cfg, own, 10,
                                        discover=lambda *a, **k: discover.discover_topic(*a, ask=ask, **k))
    assert sorted(i.title for i in got) == ["Dubbel", "Extra", "Uit eigen bron"]
    assert all(i.topic == "Thema" for i in got)
    assert "blog.example" in ask.calls[0]["prompt"]  # website zonder feed krijgt extra aandacht


class Scripted:
    def __init__(self, answers):
        self.answers, self.prompts = list(answers), []

    def __call__(self, prompt, **kw):
        self.prompts.append(prompt)
        return self.answers.pop(0)


class NoStore:
    def load_covered(self, today, days):
        return []


def cfg(**extra):
    base = {
        "relevance": {"min_item_score": 3, "coverage_min_score": 6, "topic_decay": 0.7, "max_topics": 5, "max_items_per_topic": 8,
                      "focus": "", "repeat_days": 7, "max_candidates_per_topic": 10, "lookback_hours": 48},
        "duration": {"max_minutes": 10.0, "item_minutes_top": 3.0, "item_minutes_floor": 1.0, "max_stretch": 3.0,
                     "intro_outro_minutes": 2.5, "words_per_minute": 150},
        "models": {"scoring": "s", "script": "c"},
        "topics": [{"name": "Klimaat", "description": "Klimaat", "keywords": [], "feeds": [], "free_text": True}],
        "sources": {"feeds": [], "domains": []},
        "period": {"from": NOW - DAY, "to": NOW},
    }
    base.update(extra)
    return base


def run_plan(items, answers):
    scripted = Scripted(answers)
    original, original_find = llm.ask, plan.candidates_for_topic
    llm.ask = scripted
    plan.candidates_for_topic = lambda topic, c, own, limit: items
    try:
        return plan.plan_episode(cfg(), date(2026, 11, 2), store=NoStore()), scripted
    finally:
        llm.ask, plan.candidates_for_topic = original, original_find


def test_vrije_tekst_onderwerp_wordt_gescoord_zonder_regiobeperking_met_betrouwbaarheid() -> None:
    items = [Item("Klimaat", "Groot akkoord", "s", "https://nos.nl/1", "NOS"), Item("Klimaat", "Gerucht", "s", "https://x.example/2", "X")]
    plans, scripted = run_plan(items, ['{"scores": [{"i": 0, "score": 8}, {"i": 1, "score": 2}]}', '{"schrappen": []}'])
    assert [(p.name, [i.title for i, _ in p.items]) for p in plans] == [("Klimaat", ["Groot akkoord"])]
    prompt = scripted.prompts[0]
    assert "Betrouwbaarheid" in prompt and "Regionale focus" not in prompt  # geen ongevraagde Nederland-beperking


def test_geen_nieuws_geeft_geen_aflevering() -> None:
    plans, scripted = run_plan([], [])
    assert plans == [] and scripted.prompts == []  # niets te beoordelen: geen modelaanroepen, aflevering wordt overgeslagen


def test_stijl_periode_en_achtergrond_in_het_script() -> None:
    plans = [plan.TopicPlan("Klimaat", [(Item("Klimaat", "Akkoord", "s", "https://nos.nl/1", "NOS", minutes=3.0), 8)], 8, 3.0)]
    long_text = "woord " * 1400
    answers = {"zakelijk": f"TITEL: Wat is het akkoord?\nSAMENVATTING: Kort.\n---\n{long_text}"}
    original, original_text = script.ask, script._article_text
    script._article_text = lambda link: "Tekst van het artikel."
    try:
        for style in ("zakelijk", "informeel", "verhalend"):
            seen = {}

            def fake(prompt, *, model, system="", max_tokens=0, thinking=None, _seen=seen):
                _seen.setdefault("system", system)
                _seen.setdefault("prompt", prompt)
                return answers["zakelijk"]

            script.ask = fake
            c = cfg(style=style, fill_background=True, podcast={"title": "Mijn podcast", "call_to_action": "Deel dit."})
            script.write_script(plans, c, date(2026, 11, 2))
            assert script.STYLES[style] in seen["system"], style
            assert "achtergrond" in seen["system"].lower() and "nooit verzonnen nieuws" in seen["system"].lower()
            assert "tot en met" in seen["prompt"] and "Zeg niet 'vandaag'" in seen["prompt"]  # periode sinds de vorige aflevering
        # zonder stijl en achtergrond (de oude CLI-config) verandert het script niet
        seen = {}
        script.ask = lambda prompt, *, model, system="", **kw: seen.setdefault("system", system) and answers["zakelijk"]
        script.write_script(plans, cfg(podcast={"title": "T", "call_to_action": "c"}, period=None), date(2026, 11, 2))
        assert seen["system"] == script.SYSTEM
    finally:
        script.ask, script._article_text = original, original_text


def test_te_lang_script_wordt_ingekort() -> None:
    plans = [plan.TopicPlan("Klimaat", [(Item("Klimaat", "Akkoord", "s", "https://nos.nl/1", "NOS", minutes=3.0), 8)], 8, 3.0)]
    target = round(3.0 * 150) + 350
    too_long = "TITEL: T\nSAMENVATTING: S\n---\n" + "woord " * int(target * 1.4)
    right = "TITEL: T\nSAMENVATTING: S\n---\n" + "woord " * target
    answers = [too_long, right]
    calls = []
    original, original_text = script.ask, script._article_text
    script._article_text = lambda link: ""
    script.ask = lambda prompt, **kw: calls.append(prompt) or answers.pop(0)
    try:
        _, _, text = script.write_script(plans, cfg(podcast={"title": "T", "call_to_action": "c"}, period=None), date(2026, 11, 2))
        assert len(calls) == 2 and "hooguit" in calls[1] and len(text.split()) == target  # één inkortronde, binnen 10% van de streefduur
    finally:
        script.ask, script._article_text = original, original_text


def main() -> None:
    tests = [value for name, value in globals().items() if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("OK", test.__name__)
    print(f"OK: {len(tests)} tests")


if __name__ == "__main__":
    main()
