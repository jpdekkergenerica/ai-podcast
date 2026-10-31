"""Tests voor de multi-tenant API: auth, tenant-isolatie, show-levenscyclus, limieten, feed-toegang.

Gebruik (vanuit de projectmap):  python -m tests.test_api
Geen netwerk en geen API-sleutels; een tijdelijke SQLite-database en opslagmap.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_TMP = tempfile.mkdtemp(prefix="podcast-api-test-")
os.environ.update({
    "DATABASE_URL": f"sqlite:///{_TMP}/test.db",
    "STORAGE_ROOT": f"{_TMP}/storage",
    "AUTH_DEV_MODE": "1",
    "WORKER_INLINE": "0",
    "PUBLIC_BASE_URL": "http://testserver",
})

from fastapi.testclient import TestClient  # noqa: E402

from api.db import init_db  # noqa: E402
from api.main import app  # noqa: E402

init_db()
client = TestClient(app)

TOPIC = {"name": "Tech", "keywords": ["ai"], "feeds": ["https://example.com/rss"]}


def login(sub: str) -> dict:
    res = client.post("/auth/dev", json={"apple_sub": sub, "email": f"{sub}@example.com"})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def make_show(headers: dict, title: str = "Mijn show", **extra) -> dict:
    res = client.post("/me/show", headers=headers, json={"title": title, "topics": [TOPIC], **extra})
    assert res.status_code == 200, res.text
    return res.json()


def feed_path(show: dict) -> str:
    return f"/feeds/{show['id']}.xml?token={show['feed_token']}"


def test_login_vereist() -> None:
    assert client.get("/me/show").status_code == 401
    assert client.get("/me/show", headers={"Authorization": "Bearer rommel"}).status_code == 401


def test_start_weigert_zonder_geheim_buiten_dev() -> None:
    env = {k: v for k, v in os.environ.items() if k not in ("AUTH_DEV_MODE", "API_JWT_SECRET")}
    res = subprocess.run([sys.executable, "-c", "import api.auth"], cwd=ROOT, env=env, capture_output=True)
    assert res.returncode != 0 and b"API_JWT_SECRET" in res.stderr


def test_show_levenscyclus() -> None:
    h = login("levenscyclus")
    assert client.get("/me/show", headers=h).status_code == 404
    show = make_show(h)
    assert show["title"] == "Mijn show" and len(show["topics"]) == 1
    assert client.post("/me/show", headers=h, json={"title": "tweede"}).status_code == 409

    res = client.patch("/me/show", headers=h, json={
        "title": "Nieuw",
        "topics": [TOPIC, {"name": "Sport", "feeds": ["https://example.com/sport"]}],
    })
    assert res.status_code == 200
    assert res.json()["title"] == "Nieuw"
    assert [t["name"] for t in res.json()["topics"]] == ["Tech", "Sport"]

    res = client.patch("/me/show", headers=h, json={"topics": [TOPIC]})
    assert [t["name"] for t in res.json()["topics"]] == ["Tech"]


def test_tenant_isolatie() -> None:
    a, b = login("iso-a"), login("iso-b")
    show_a = make_show(a, "Van A")
    assert client.get("/me/show", headers=b).status_code == 404
    show_b = make_show(b, "Van B")
    assert show_b["id"] != show_a["id"]
    assert client.get("/me/show", headers=a).json()["title"] == "Van A"
    assert client.get("/me/jobs", headers=b).json() == []

    # token van B opent de feed of media van A niet
    assert client.get(f"/feeds/{show_a['id']}.xml?token={show_b['feed_token']}").status_code == 404
    assert client.get(f"/media/{show_a['id']}/x.mp3?token={show_b['feed_token']}").status_code == 404
    assert client.get(f"/shows/{show_a['id']}/site/feed.xml?token={show_b['feed_token']}").status_code == 404

    # B's wijzigingen raken A niet
    client.patch("/me/show", headers=b, json={"title": "B hernoemd"})
    assert client.get("/me/show", headers=a).json()["title"] == "Van A"


def test_validatie_onderwerpen() -> None:
    h = login("validatie")
    bad_topics = [
        [{"name": "", "feeds": ["https://x.nl/rss"]}],
        [{"name": "Geen feed", "feeds": []}],
        [{"name": "Rare feed", "feeds": ["file:///etc/passwd"]}],
        [{"name": "Rare feed", "feeds": ["ftp://x.nl/rss"]}],
        [{"name": f"T{i}", "feeds": ["https://x.nl/rss"]} for i in range(13)],
    ]
    for topics in bad_topics:
        res = client.post("/me/show", headers=h, json={"title": "x", "topics": topics})
        assert res.status_code == 400, (topics, res.text)
    assert client.get("/me/show", headers=h).status_code == 404  # niets half aangemaakt

    res = client.post("/me/feed-test", headers=h, json={"feeds": ["file:///etc/passwd"]})
    assert res.status_code == 400


def test_duur_is_begrensd() -> None:
    h = login("duur")
    make_show(h)
    assert client.patch("/me/show", headers=h, json={"duration": {"max_minutes": 600}}).status_code == 400
    assert client.patch("/me/show", headers=h, json={"duration": {"max_minutes": 0}}).status_code == 400
    assert client.patch("/me/show", headers=h, json={"duration": {"max_minutes": 10}}).status_code == 200
    assert client.post("/me/build", headers=h, json={"max_minutes": 99}).status_code == 400


def test_handmatige_build_limiet_per_dag() -> None:
    h = login("build")
    make_show(h)
    assert client.post("/me/build", headers=h, json={}).status_code == 200
    jobs = client.get("/me/jobs", headers=h).json()
    assert [j["status"] for j in jobs] == ["queued"]
    assert client.post("/me/build", headers=h, json={}).status_code == 429


def test_feed_token_en_rotatie() -> None:
    h = login("token")
    show = make_show(h)
    res = client.get(feed_path(show))
    assert res.status_code == 200, res.text
    assert "xml" in res.headers["content-type"]
    assert client.get(f"/feeds/{show['id']}.xml?token=fout").status_code == 404
    assert client.get(f"/feeds/{show['id']}.xml").status_code == 422  # token verplicht

    rotated = client.post("/me/show/rotate-feed-token", headers=h).json()
    assert rotated["feed_token"] != show["feed_token"]
    assert client.get(feed_path(show)).status_code == 404
    assert client.get(feed_path(rotated)).status_code == 200


def test_geen_pad_uit_de_sitemap() -> None:
    a, b = login("pad-a"), login("pad-b")
    show_a, show_b = make_show(a), make_show(b)
    client.get(feed_path(show_b))  # maakt de site-map van B aan
    secret = Path(os.environ["STORAGE_ROOT"]) / show_b["id"] / "geheim.txt"
    secret.write_text("niet voor A")
    assert client.get(f"/shows/{show_b['id']}/site/feed.xml?token={show_b['feed_token']}").status_code == 200
    for evil in ("..%2fgeheim.txt", "%2e%2e/geheim.txt", "../geheim.txt"):
        res = client.get(f"/shows/{show_b['id']}/site/{evil}?token={show_b['feed_token']}")
        assert res.status_code in (404, 400) and "niet voor A" not in res.text, (evil, res.status_code)
    assert client.get(f"/media/{show_a['id']}/..%2f..%2f{show_b['id']}%2fgeheim.txt?token={show_a['feed_token']}").status_code in (400, 404)


def test_account_verwijderen() -> None:
    h = login("weg")
    show = make_show(h)
    assert client.get(feed_path(show)).status_code == 200
    assert client.delete("/me/account", headers=h).status_code == 200
    assert client.get("/me/show", headers=h).status_code == 401
    assert client.get(feed_path(show)).status_code == 404
    assert not (Path(os.environ["STORAGE_ROOT"]) / show["id"]).exists()
    # opnieuw inloggen geeft een schone start
    assert client.get("/me/show", headers=login("weg")).status_code == 404

def test_planning_validatie() -> None:
    h = login("planning-validatie")
    show = make_show(h)
    assert show["schedule"]["enabled"] is False  # standaard uit: geen ongevraagde kosten
    bad = [
        {"enabled": True, "days": []},
        {"days": [7]},
        {"days": ["ma"]},
        {"time": "25:00"},
        {"time": "7:00"},
        {"timezone": "Mars/Olympus"},
        {"enabled": "ja"},
    ]
    for sched in bad:
        res = client.patch("/me/show", headers=h, json={"schedule": sched})
        assert res.status_code == 400, (sched, res.text)
    res = client.patch("/me/show", headers=h, json={"schedule": {"enabled": True, "days": [4, 0, 0, 2], "time": "18:30"}})
    assert res.status_code == 200, res.text
    assert res.json()["schedule"] == {"enabled": True, "days": [0, 2, 4], "time": "18:30", "timezone": "Europe/Amsterdam"}


def test_planning_per_gebruiker_in_de_worker() -> None:
    from datetime import datetime, timezone
    from worker.run import enqueue_due

    maandag = lambda uur, minuut: datetime(2026, 11, 2, uur, minuut, tzinfo=timezone.utc)  # 2026-11-02 is een maandag, NL = UTC+1
    a, b, c = login("plan-a"), login("plan-b"), login("plan-c")
    make_show(a); make_show(b); make_show(c)
    client.patch("/me/show", headers=a, json={"schedule": {"enabled": True, "days": [0], "time": "07:00"}})
    client.patch("/me/show", headers=b, json={"schedule": {"enabled": True, "days": [1], "time": "07:00"}})
    # c laat de planning uit

    assert enqueue_due(maandag(5, 59)) == 0   # 06:59 lokaal: nog niet
    assert enqueue_due(maandag(9, 10)) == 0   # 10:10 lokaal: venster van 2 uur voorbij
    assert enqueue_due(maandag(6, 10)) == 1   # alleen a: gekozen dag en tijd
    assert enqueue_due(maandag(6, 20)) == 0   # a heeft vandaag al een geplande run
    assert [j["trigger"] for j in client.get("/me/jobs", headers=a).json()] == ["schedule"]
    assert client.get("/me/jobs", headers=b).json() == []
    assert client.get("/me/jobs", headers=c).json() == []


def test_planning_zet_geen_tweede_job_naast_een_openstaande() -> None:
    from datetime import datetime, timezone
    from worker.run import enqueue_due

    h = login("plan-open")
    make_show(h)
    client.patch("/me/show", headers=h, json={"schedule": {"enabled": True, "days": [0, 1, 2, 3, 4, 5, 6], "time": "07:00", "timezone": "UTC"}})
    assert client.post("/me/build", headers=h, json={}).status_code == 200  # handmatige job staat open
    assert enqueue_due(datetime(2026, 11, 2, 7, 5, tzinfo=timezone.utc)) == 0


def main() -> None:
    tests = [value for name, value in globals().items() if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("OK", test.__name__)
    print(f"OK: {len(tests)} tests")


if __name__ == "__main__":
    main()
