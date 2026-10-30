"""Tests voor ronde 1: kandidaatverdeling, JSON die de run stopt, en de tijdverdeling.

Gebruik (vanuit de projectmap):  python -m tests.test_round1
Geen netwerk en geen API-sleutel.
"""
import re
import socket
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import podcast.fetch as fetch  # noqa: E402
import podcast.llm as llm  # noqa: E402
from podcast.llm import ask_json  # noqa: E402
from podcast.fetch import Item, assemble_candidates, cap_feed, per_feed_cap, read_feed  # noqa: E402
from podcast.plan import drop_repeats, minutes_for, score_items, select  # noqa: E402
from podcast.pronounce import detect  # noqa: E402


class Scripted:
    def __init__(self, answers: list[str]):
        self.answers = list(answers)
        self.prompts: list[str] = []

    def __call__(self, prompt, **kwargs):
        self.prompts.append(prompt)
        if not self.answers:
            raise AssertionError("onverwachte extra modelaanroep")
        return self.answers.pop(0)

    @property
    def calls(self) -> int:
        return len(self.prompts)


@contextmanager
def patch_ask(answers: list[str]):
    scripted = Scripted(answers)
    original = llm.ask
    llm.ask = scripted
    try:
        yield scripted
    finally:
        llm.ask = original


def item(topic: str, title: str, link: str = "", published: float = 0.0, source: str = "") -> Item:
    return Item(topic, title, "samenvatting", link or f"https://{topic}/{title}", source or topic,
                published=published)


def cfg(**relevance) -> dict:
    base = {
        "relevance": {
            "min_item_score": 3,
            "coverage_min_score": 6,
            "topic_decay": 0.7,
            "max_topics": 5,
            "max_items_per_topic": 8,
        },
        "duration": {
            "item_minutes_floor": 1.0,
            "item_minutes_top": 3.0,
            "max_stretch": 2.0,
        },
    }
    base["relevance"].update(relevance)
    return base


def topic_dict() -> dict:
    return {"name": "Dakloosheid", "description": "opvang in Nederland"}


# --- kandidaten ---

def test_per_feed_cap() -> None:
    assert per_feed_cap(1, 25) == 25
    assert per_feed_cap(2, 25) == 13
    assert per_feed_cap(5, 25) == 5
    assert per_feed_cap(12, 25) == 3


def test_cap_feed_houdt_de_nieuwste() -> None:
    old = item("T", "oud", published=10)
    mid = item("T", "midden", published=20)
    undated = item("T", "zonder-datum", published=0)
    newest = item("T", "nieuw", published=30)
    kept = cap_feed([old, undated, mid, newest], 2)
    assert [it.title for it in kept] == ["nieuw", "midden"]


def test_assemble_sorteert_en_ontdubbelt() -> None:
    first = item("T", "eerste", link="https://x/1", published=10, source="NOS")
    newer = item("T", "zelfde", link="https://x/1", published=90, source="NU")
    other = item("T", "ander", link="https://x/2", published=50, source="AD")
    merged = assemble_candidates([[first, other], [newer]], 10)
    assert [it.link for it in merged] == ["https://x/2", "https://x/1"]
    assert merged[1].source == "NOS"


def test_read_feed_filtert_op_trefwoord_en_datum() -> None:
    now = 1_700_000_000

    def parse(url):
        return SimpleNamespace(feed={"title": "NOS"}, entries=[
            {"title": "Dakloos in <b>Groningen</b>", "summary": "opvang", "link": "https://x/1",
             "published_parsed": time.gmtime(now)},
            {"title": "Voetbal", "summary": "wedstrijd", "link": "https://x/2",
             "published_parsed": time.gmtime(now)},
            {"title": "Oude daklozenopvang", "summary": "", "link": "https://x/3",
             "published_parsed": time.gmtime(now - 10_000)},
            {"title": "Dakloos zonder datum", "summary": "", "link": "https://x/4"},
        ])

    items = read_feed("https://nos.example/rss", "Dakloosheid", now - 3600,
                      re.compile("daklo", re.I), parse=parse)
    assert [it.link for it in items] == ["https://x/1", "https://x/4"]
    assert items[0].title == "Dakloos in Groningen"
    assert items[0].source == "NOS"
    assert items[0].published == now


def test_read_feed_dode_feed_is_leeg() -> None:
    def parse(url):
        raise TimeoutError("traag")

    assert read_feed("https://dood.example/rss", "T", 0, None, parse=parse) == []


def test_fetch_topic_geeft_elke_feed_een_plaats() -> None:
    """Zonder plafond per feed vullen de vier nieuwste van A de lijst. Met plafond komt B mee."""
    feed_a = [item("T", f"a{n}", link=f"https://a/{n}", published=float(n), source="A")
              for n in (100, 99, 98, 97)]
    feed_b = [item("T", f"b{n}", link=f"https://b/{n}", published=float(n), source="B")
              for n in (50, 49)]
    feeds = {"https://a.example/rss": feed_a, "https://b.example/rss": feed_b}

    def fake(url, topic_name, cutoff, pattern):
        return list(feeds[url])

    original = fetch.read_feed
    before = socket.getdefaulttimeout()
    fetch.read_feed = fake
    try:
        items = fetch.fetch_topic(
            {"name": "T", "feeds": ["https://a.example/rss", "  ", "https://b.example/rss"]},
            96, 4,
        )
    finally:
        fetch.read_feed = original
    assert socket.getdefaulttimeout() == before
    assert [it.link for it in items] == ["https://a/100", "https://a/99", "https://b/50", "https://b/49"]


def test_fetch_topic_herstelt_timeout_bij_fout() -> None:
    def fake(url, topic_name, cutoff, pattern):
        raise RuntimeError("kapot")

    original = fetch.read_feed
    before = socket.getdefaulttimeout()
    fetch.read_feed = fake
    try:
        try:
            fetch.fetch_topic({"name": "T", "feeds": ["https://a.example/rss"]}, 96, 4)
        except RuntimeError as e:
            assert "kapot" in str(e)
        else:
            raise AssertionError("een kapotte feedlezer had moeten doorwerken naar de aanroeper")
    finally:
        fetch.read_feed = original
    assert socket.getdefaulttimeout() == before


def test_fetch_topic_zonder_feeds() -> None:
    assert fetch.fetch_topic({"name": "T", "feeds": []}, 96, 25) == []
    assert fetch.fetch_topic({"name": "T", "feeds": ["  "]}, 96, 25) == []


# --- JSON ---

def test_ask_json_repareert_een_keer() -> None:
    with patch_ask(['{"scores": {"i": 0}}', '{"scores": [{"i": 0, "score": 4}]}']) as scripted:
        data = ask_json("beoordeel", model="m", required="scores", kind=list)
    assert data["scores"][0]["score"] == 4
    assert scripted.calls == 2
    assert "geldige JSON" in scripted.prompts[1]


def test_ask_json_stopt_na_tweede_mislukking() -> None:
    with patch_ask(["geen json", "nog steeds geen json"]):
        try:
            ask_json("beoordeel", model="m", required="scores", kind=list)
        except RuntimeError as e:
            assert "scores" in str(e)
        else:
            raise AssertionError("twee onleesbare antwoorden hadden de aanroep moeten stoppen")


def test_ontbrekende_score_blijft_onbekend() -> None:
    raw = '{"scores": [{"i": 0, "score": 8}]}'
    items = [item("T", "een"), item("T", "twee")]
    with patch_ask([raw]) as scripted:
        scores = score_items(topic_dict(), items, "m", "Nederland")
    assert scores == [8, None]
    assert scripted.calls == 1


def test_score_nul_blijft_nul() -> None:
    raw = '{"scores": [{"i": 0, "score": 0}]}'
    with patch_ask([raw]):
        scores = score_items(topic_dict(), [item("T", "een")], "m", "Nederland")
    assert scores == [0]


def test_score_zonder_leesbare_rijen_stopt() -> None:
    with patch_ask(['{"scores": [{"i": 0, "score": true}]}']):
        try:
            score_items(topic_dict(), [item("T", "een")], "m", "Nederland")
        except RuntimeError as e:
            assert "geen leesbare scores" in str(e)
        else:
            raise AssertionError("een antwoord zonder echte score had moeten stoppen")


def test_herhalingscontrole_stopt() -> None:
    pool = [(item("T", "een"), 8), (item("T", "twee"), 7)]
    with patch_ask(["geen json", "nog steeds geen json"]):
        try:
            drop_repeats(pool, [], "m")
        except RuntimeError as e:
            assert "schrappen" in str(e)
        else:
            raise AssertionError("een mislukte herhalingscontrole had de run moeten stoppen")


def test_herhalingscontrole_slaat_ongeldige_nummers_over() -> None:
    pool = [(item("T", "een"), 8), (item("T", "twee"), 7), (item("T", "drie"), 6)]
    with patch_ask(['{"schrappen": [1, "x", true]}']):
        kept = drop_repeats(pool, [], "m")
    assert [it.title for it, _ in kept] == ["een", "drie"]


def test_herhalingscontrole_slaat_model_over_bij_een_bericht() -> None:
    pool = [(item("T", "een"), 8)]
    with patch_ask([]) as scripted:
        assert drop_repeats(pool, [], "m") == pool
    assert scripted.calls == 0


def test_uitspraak_stopt_na_twee_onleesbare_antwoorden() -> None:
    with patch_ask(["geen", "geen"]):
        try:
            detect("ASML stijgt", {}, "m")
        except RuntimeError as e:
            assert "uitspraak" in str(e)
        else:
            raise AssertionError("een onleesbare uitspraaklijst had moeten stoppen")


def test_uitspraak_na_reparatie() -> None:
    with patch_ask(["tekst", '{"uitspraak": {"ASML": "aa-es-em-el", "app": "app"}}']) as scripted:
        found = detect("ASML stijgt via een app", {}, "m")
    assert found == {"ASML": "aa-es-em-el"}
    assert scripted.calls == 2


# --- tijdverdeling ---

def test_minutes_for_lineair() -> None:
    dur = cfg()["duration"]
    assert minutes_for(10, dur, 3) == 3.0
    assert minutes_for(3, dur, 3) == 1.0
    assert minutes_for(0, dur, 3) == 1.0
    assert minutes_for(12, dur, 3) == 3.0
    assert minutes_for(6, dur, 3) == 1 + 2 * (6 - 3) / (10 - 3)


def test_select_decay_laat_een_tweede_onderwerp_mee() -> None:
    pool = [
        (item("A", "groot"), 10),
        (item("A", "vervolg"), 9),
        (item("A", "nog-een"), 9),
        (item("B", "ander"), 8),
    ]
    strict = cfg(coverage_min_score=10)
    plans = select(pool, 8, strict)
    by = {p.name: [score for _, score in p.items] for p in plans}
    assert by == {"A": [10, 9], "B": [8]}

    without = cfg(coverage_min_score=10, topic_decay=0)
    only_a = select([
        (item("A", "groot"), 10),
        (item("A", "vervolg"), 9),
        (item("A", "nog-een"), 9),
        (item("B", "ander"), 8),
    ], 8, without)
    assert [p.name for p in only_a] == ["A"]
    assert [score for _, score in only_a[0].items] == [10, 9, 9]


def test_select_max_topics_en_max_items() -> None:
    pool = [(item(name, "bericht"), 10) for name in ("A", "B", "C")]
    plans = select(pool, 100, cfg(max_topics=2))
    assert [p.name for p in plans] == ["A", "B"]

    many = [(item("A", f"n{i}"), 10) for i in range(5)]
    capped = select(many, 100, cfg(max_items_per_topic=2))
    assert len(capped) == 1 and len(capped[0].items) == 2


def test_select_rekt_hooguit_max_stretch_en_schaalt_terug() -> None:
    stretched = select([(item("A", "een"), 10)], 20, cfg())
    assert stretched[0].minutes == 6.0

    both = select([(item("A", "een"), 10), (item("B", "twee"), 10)], 4, cfg())
    assert abs(sum(p.minutes for p in both) - 4) < 1e-9
    assert {p.name for p in both} == {"A", "B"}


def test_select_leeg() -> None:
    assert select([], 10, cfg()) == []


def main() -> None:
    tests = [value for name, value in globals().items() if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("OK", test.__name__)
    print(f"OK: {len(tests)} tests")


if __name__ == "__main__":
    main()
