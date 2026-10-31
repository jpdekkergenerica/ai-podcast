"""Tests voor de multi-tenant API: podcasts, validatie per veld, tenant-isolatie, planning, bronnen, omslag, stemmen,
meldingen en de worker (eerste aflevering, retries, overslaan).

Gebruik (vanuit de projectmap):  python -m tests.test_api
Geen netwerk en geen API-sleutels; een tijdelijke SQLite-database en opslagmap.
"""
import io
import os
import subprocess
import sys
import tempfile
from datetime import date, datetime, timedelta, timezone
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

import httpx  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

from api import push, routes, voices  # noqa: E402
from api.db import SessionLocal, init_db  # noqa: E402
from api.main import app  # noqa: E402
from api.models import Episode, Job, Show  # noqa: E402
from api.schedule import due_publication, next_publication  # noqa: E402

init_db()
client = TestClient(app)


def login(sub: str) -> dict:
    res = client.post("/auth/dev", json={"apple_sub": sub, "email": f"{sub}@example.com"})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def payload(**extra) -> dict:
    base = {"title": "Mijn podcast", "topics": ["AI-regelgeving in Europa"], "duration_minutes": 10,
            "voice_id": "voice-1", "voice_name": "Fenna", "style": "informeel"}
    return {**base, **extra}


def make(headers: dict, **extra) -> dict:
    res = client.post("/me/podcasts", headers=headers, json=payload(**extra))
    assert res.status_code == 201, res.text
    return res.json()


def feed_path(p: dict) -> str:
    return p["feed_url"].replace("http://testserver", "")


def jobs_of(podcast_id: str) -> list[Job]:
    db = SessionLocal()
    try:
        return list(db.query(Job).filter(Job.show_id == podcast_id).order_by(Job.created_at).all())
    finally:
        db.close()


def png_bytes(w: int, h: int, color="purple") -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, "PNG")
    return buf.getvalue()


# ---------- toegang ----------

def test_login_vereist() -> None:
    assert client.get("/me/podcasts").status_code == 401
    assert client.get("/me/podcasts", headers={"Authorization": "Bearer rommel"}).status_code == 401


def test_start_weigert_zonder_geheim_buiten_dev() -> None:
    env = {k: v for k, v in os.environ.items() if k not in ("AUTH_DEV_MODE", "API_JWT_SECRET")}
    res = subprocess.run([sys.executable, "-c", "import api.auth"], cwd=ROOT, env=env, capture_output=True)
    assert res.returncode != 0 and b"API_JWT_SECRET" in res.stderr


# ---------- podcasts ----------

def test_aanmaken_start_direct_de_eerste_aflevering() -> None:
    h = login("aanmaken")
    assert client.get("/me/podcasts", headers=h).json() == []
    p = make(h)
    assert p["title"] == "Mijn podcast" and [t["text"] for t in p["topics"]] == ["AI-regelgeving in Europa"]
    assert p["duration_minutes"] == 10 and p["style"] == "informeel" and p["voice"] == {"voice_id": "voice-1", "name": "Fenna"}
    jobs = jobs_of(p["id"])
    assert [(j.trigger, j.status) for j in jobs] == [("initial", "queued")]  # geen aparte generatieknop nodig
    assert p["status"]["code"] == "running" and p["status"]["label"] == "Bezig"
    assert p["schedule"]["enabled"] is True and p["next_run"]["timezone"] == "Europe/Amsterdam"
    assert client.get(f"/me/podcasts/{p['id']}", headers=h).json()["id"] == p["id"]


def test_meerdere_podcasts_met_eigen_instellingen() -> None:
    h = login("meerdere")
    a = make(h, title="Tech", duration_minutes=5, style="zakelijk")
    b = make(h, title="Sport", topics=["Eredivisie", "Formule 1"], duration_minutes=20, style="verhalend",
             schedule={"days": [0, 1, 2, 3, 4], "time": "18:00"})
    listed = client.get("/me/podcasts", headers=h).json()
    assert [p["title"] for p in listed] == ["Tech", "Sport"]
    assert a["feed_url"] != b["feed_url"]
    assert (listed[1]["duration_minutes"], listed[1]["style"], len(listed[1]["topics"])) == (20, "verhalend", 2)
    assert listed[1]["schedule"]["days"] == [0, 1, 2, 3, 4] and listed[0]["schedule"]["days"] == list(range(7))


def test_variabel_aantal_onderwerpen_en_opschonen() -> None:
    h = login("onderwerpen")
    p = make(h, topics=["  Klimaat   en energie ", "", "klimaat en energie", "Ruimtevaart"])
    assert [t["text"] for t in p["topics"]] == ["Klimaat en energie", "Ruimtevaart"]  # leeg en dubbel valt weg
    res = client.patch(f"/me/podcasts/{p['id']}", headers=h, json={"topics": ["Een", "Twee", "Drie", "Vier", "Vijf", "Zes"]})
    assert len(res.json()["topics"]) == 6


def test_validatie_per_veld() -> None:
    h = login("validatie")
    cases = {
        "title": payload(title="  "),
        "topics": payload(topics=["", "  "]),
        "duration_minutes": payload(duration_minutes=7),
        "voice": payload(voice_id=""),
        "style": payload(style="grappig"),
        "schedule": payload(schedule={"days": [9]}),
    }
    for field, body in cases.items():
        res = client.post("/me/podcasts", headers=h, json=body)
        assert res.status_code == 400, (field, res.text)
        assert field in res.json()["detail"]["fields"], (field, res.json())
    # alles tegelijk fout: alle velden komen terug, en er is niets half aangemaakt
    res = client.post("/me/podcasts", headers=h, json={})
    assert set(res.json()["detail"]["fields"]) >= {"title", "topics", "duration_minutes", "voice", "style"}
    assert client.get("/me/podcasts", headers=h).json() == []
    for minutes in (5, 10, 15, 20):
        assert client.post("/me/podcasts", headers=h, json=payload(title=f"{minutes} min", duration_minutes=minutes)).status_code == 201


def test_tenant_isolatie() -> None:
    a, b = login("iso-a"), login("iso-b")
    pa = make(a, title="Van A")
    pb = make(b, title="Van B")
    assert [p["title"] for p in client.get("/me/podcasts", headers=b).json()] == ["Van B"]
    for method, path in (("get", ""), ("patch", ""), ("delete", ""), ("post", "/pause"), ("post", "/resume"),
                         ("get", "/episodes"), ("post", "/rotate-feed-token"), ("delete", "/cover")):
        res = client.request(method, f"/me/podcasts/{pa['id']}{path}", headers=b, json={} if method in ("patch", "post") else None)
        assert res.status_code == 404, (method, path, res.status_code)
    assert client.get(f"/me/podcasts/{pa['id']}", headers=a).json()["title"] == "Van A"
    # het token van B opent de feed of media van A niet
    token_b = pb["feed_url"].split("token=")[1]
    assert client.get(f"/feeds/{pa['id']}.xml?token={token_b}").status_code == 404
    assert client.get(f"/media/{pa['id']}/cover.jpg?token={token_b}").status_code == 404


def test_wijzigen_geldt_voor_later_en_start_geen_extra_generatie() -> None:
    h = login("wijzigen")
    p = make(h)
    before = len(jobs_of(p["id"]))
    res = client.patch(f"/me/podcasts/{p['id']}", headers=h, json={
        "title": "Nieuwe naam", "topics": ["Iets anders"], "duration_minutes": 15, "style": "zakelijk",
        "voice_id": "voice-2", "voice_name": "Daan", "schedule": {"time": "19:30"}})
    assert res.status_code == 200, res.text
    out = res.json()
    assert (out["title"], out["duration_minutes"], out["style"], out["voice"]["name"], out["schedule"]["time"]) == \
        ("Nieuwe naam", 15, "zakelijk", "Daan", "19:30")
    assert len(jobs_of(p["id"])) == before
    assert client.patch(f"/me/podcasts/{p['id']}", headers=h, json={"duration_minutes": 12}).json()["detail"]["fields"].keys() == {"duration_minutes"}


def test_pauzeren_hervatten_verwijderen() -> None:
    h = login("beheer")
    p = make(h)
    res = client.post(f"/me/podcasts/{p['id']}/pause", headers=h).json()
    assert res["paused"] and res["status"]["code"] == "paused" and res["next_run"] is None
    res = client.post(f"/me/podcasts/{p['id']}/resume", headers=h).json()
    assert not res["paused"] and res["next_run"] is not None
    assert client.get(feed_path(p)).status_code == 200
    assert client.delete(f"/me/podcasts/{p['id']}", headers=h).status_code == 200
    assert client.get(f"/me/podcasts/{p['id']}", headers=h).status_code == 404
    assert client.get(feed_path(p)).status_code == 404
    assert not (Path(os.environ["STORAGE_ROOT"]) / p["id"]).exists()


def test_feed_en_token_rotatie() -> None:
    h = login("token")
    p = make(h)
    res = client.get(feed_path(p))
    assert res.status_code == 200 and "xml" in res.headers["content-type"], res.text
    assert client.get(f"/feeds/{p['id']}.xml?token=fout").status_code == 404
    assert client.get(f"/feeds/{p['id']}.xml").status_code == 422
    rotated = client.post(f"/me/podcasts/{p['id']}/rotate-feed-token", headers=h).json()
    assert rotated["feed_url"] != p["feed_url"]
    assert client.get(feed_path(p)).status_code == 404 and client.get(feed_path(rotated)).status_code == 200


def test_geen_pad_uit_de_sitemap() -> None:
    a, b = login("pad-a"), login("pad-b")
    pa, pb = make(a), make(b)
    secret = Path(os.environ["STORAGE_ROOT"]) / pb["id"] / "geheim.txt"
    secret.write_text("niet voor A")
    token_b = pb["feed_url"].split("token=")[1]
    for evil in ("..%2fgeheim.txt", "%2e%2e/geheim.txt", "../geheim.txt"):
        res = client.get(f"/shows/{pb['id']}/site/{evil}?token={token_b}")
        assert res.status_code in (404, 400) and "niet voor A" not in res.text, (evil, res.status_code)
    assert client.get(f"/media/{pa['id']}/..%2f..%2f{pb['id']}%2fgeheim.txt?token={pa['feed_url'].split('token=')[1]}").status_code in (400, 404)


def test_account_verwijderen_ruimt_alle_podcasts_op() -> None:
    h = login("weg")
    ps = [make(h, title="Een"), make(h, title="Twee")]
    assert client.delete("/me/account", headers=h).status_code == 200
    assert client.get("/me/podcasts", headers=h).status_code == 401
    for p in ps:
        assert client.get(feed_path(p)).status_code == 404
        assert not (Path(os.environ["STORAGE_ROOT"]) / p["id"]).exists()
    assert client.get("/me/podcasts", headers=login("weg")).json() == []


# ---------- planning ----------

AMS = "Europe/Amsterdam"


def utc(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)


def test_planning_validatie_en_voorinstellingen() -> None:
    h = login("planning")
    p = make(h)
    url = f"/me/podcasts/{p['id']}"
    for bad in ({"days": []}, {"days": [7]}, {"days": ["ma"]}, {"time": "25:00"}, {"time": "7:00"}, {"timezone": "Mars/Olympus"},
                {"every_days": 1}, {"every_days": 31}, {"every_days": "elke dag"}, {"enabled": "ja"}):
        res = client.patch(url, headers=h, json={"schedule": bad})
        assert res.status_code == 400 and "schedule" in res.json()["detail"]["fields"], (bad, res.text)
    presets = {"werkdagen": {"days": [0, 1, 2, 3, 4]}, "wekelijks": {"days": [5]}, "elke 3 dagen": {"every_days": 3}}
    for name, sched in presets.items():
        res = client.patch(url, headers=h, json={"schedule": {**sched, "time": "18:30"}})
        assert res.status_code == 200, (name, res.text)
        assert res.json()["next_run"] and res.json()["schedule"]["time"] == "18:30"


def test_planning_rekenregels() -> None:
    daily = {"days": list(range(7)), "time": "07:00", "timezone": AMS}
    # 2026-11-02 is een maandag, Amsterdam = UTC+1: 07:00 lokaal is 06:00 UTC; de generatie start 45 minuten eerder
    assert due_publication(daily, None, utc(2026, 11, 2, 5, 10)) is None  # 06:10 lokaal: te vroeg
    assert due_publication(daily, None, utc(2026, 11, 2, 5, 20)) == date(2026, 11, 2)  # 06:20 lokaal: voorbereiding begint
    assert due_publication(daily, None, utc(2026, 11, 2, 7, 50)) == date(2026, 11, 2)  # 08:50: nog binnen de inhaalruimte
    assert due_publication(daily, None, utc(2026, 11, 2, 9, 10)) is None  # 10:10: te laat
    assert due_publication(daily, date(2026, 11, 2), utc(2026, 11, 2, 6, 0)) is None  # vandaag is al gedaan
    # werkdagen: zaterdag niet, maandag wel
    weekdays = {**daily, "days": [0, 1, 2, 3, 4]}
    assert due_publication(weekdays, None, utc(2026, 10, 31, 6, 0)) is None  # za
    assert due_publication(weekdays, None, utc(2026, 11, 2, 6, 0)) == date(2026, 11, 2)  # ma
    # kort na middernacht klaarstaan: de voorbereiding begint de avond ervoor
    night = {**daily, "time": "00:20"}
    assert due_publication(night, None, utc(2026, 11, 1, 23, 10)) == date(2026, 11, 2)  # 00:10 lokaal op 2 nov
    # eigen interval: pas na het interval
    every3 = {**daily, "every_days": 3}
    assert due_publication(every3, date(2026, 11, 2), utc(2026, 11, 4, 6, 0)) is None
    assert due_publication(every3, date(2026, 11, 2), utc(2026, 11, 5, 6, 0)) == date(2026, 11, 5)
    # volgende publicatie
    assert next_publication(daily, None, utc(2026, 11, 2, 6, 30)).isoformat() == "2026-11-03T07:00:00+01:00"
    assert next_publication(weekdays, date(2026, 10, 30), utc(2026, 10, 31, 12, 0)).isoformat() == "2026-11-02T07:00:00+01:00"
    assert next_publication({**daily, "enabled": False}, None, utc(2026, 11, 2, 6, 30)) is None
    # zomertijd: 07:00 lokaal is dan 05:00 UTC
    assert next_publication(daily, None, utc(2026, 7, 1, 3, 0)).astimezone(timezone.utc).hour == 5


def test_worker_zet_alleen_aan_de_beurt_zijnde_podcasts_klaar() -> None:
    from worker.run import enqueue_due
    db = SessionLocal()
    db.query(Show).update({Show.active: False})  # alleen de podcasts van deze test doen mee
    db.commit()
    db.close()
    a, b, c = login("plan-a"), login("plan-b"), login("plan-c")
    pa = make(a, schedule={"days": [0], "time": "07:00"})
    pb = make(b, schedule={"days": [1], "time": "07:00"})
    pc = make(c, schedule={"days": [0], "time": "07:00"})
    db = SessionLocal()
    db.query(Show).filter(Show.id.in_([pa["id"], pb["id"], pc["id"]])).update({Show.active: True}, synchronize_session=False)
    db.query(Job).filter(Job.show_id.in_([pa["id"], pb["id"], pc["id"]])).update({Job.status: "succeeded"}, synchronize_session=False)
    db.commit()
    db.close()
    client.post(f"/me/podcasts/{pc['id']}/pause", headers=c)

    maandag = lambda uur, minuut: utc(2026, 11, 2, uur, minuut)  # NL = UTC+1
    assert enqueue_due(maandag(5, 0)) == 0   # 06:00 lokaal: nog niet
    assert enqueue_due(maandag(9, 10)) == 0  # 10:10 lokaal: inhaalruimte voorbij
    assert enqueue_due(maandag(6, 0)) == 1   # alleen a: gekozen dag en tijd (b is dinsdag, c is gepauzeerd)
    assert enqueue_due(maandag(6, 10)) == 0  # a heeft een openstaande run
    assert [j.trigger for j in jobs_of(pa["id"])][-1] == "schedule"
    assert [j.trigger for j in jobs_of(pb["id"])] == ["initial"] and [j.trigger for j in jobs_of(pc["id"])] == ["initial"]


# ---------- eigen bronnen ----------

def test_eigen_bronnen_optioneel_met_naam_en_foutmelding() -> None:
    results = {
        "https://nieuws.example/rss": {"url": "https://nieuws.example/rss", "kind": "rss", "name": "Nieuws", "feed_url": "https://nieuws.example/rss", "error": None},
        "https://kapot.example": {"url": "https://kapot.example", "kind": "website", "name": "", "feed_url": "", "error": "De website is niet bereikbaar of reageert te traag"},
    }
    original = routes.check_source
    routes.check_source = lambda url: results[url]
    try:
        h = login("bronnen")
        zonder = make(h, title="Zonder bronnen")
        assert zonder["sources"] == []  # optioneel
        p = make(h, sources=["https://nieuws.example/rss", "https://kapot.example", "https://nieuws.example/rss"])
        by_url = {s["url"]: s for s in p["sources"]}
        assert len(p["sources"]) == 2 and by_url["https://nieuws.example/rss"]["name"] == "Nieuws"
        assert by_url["https://kapot.example"]["error"].startswith("De website is niet bereikbaar")  # fout blokkeert het opslaan niet
        res = client.patch(f"/me/podcasts/{p['id']}", headers=h, json={"sources": ["https://nieuws.example/rss"]})
        assert [s["url"] for s in res.json()["sources"]] == ["https://nieuws.example/rss"]
        bad = client.post("/me/podcasts", headers=h, json=payload(sources=["ftp://x.nl", "file:///etc/passwd"]))
        assert bad.status_code == 400 and "sources" in bad.json()["detail"]["fields"]
    finally:
        routes.check_source = original


def test_bron_controle_weigert_interne_adressen() -> None:
    h = login("ssrf")
    for url in ("http://127.0.0.1:8000/health", "http://localhost/x", "http://169.254.169.254/latest/meta-data", "file:///etc/passwd"):
        res = client.post("/me/sources/check", headers=h, json={"url": url})
        assert res.status_code == 200 and res.json()["error"], (url, res.json())


# ---------- omslag ----------

def test_omslag_standaard_upload_vervangen_en_verwijderen() -> None:
    import base64
    h = login("omslag")
    p = make(h)
    assert p["has_custom_cover"] is False
    default = client.get(p["cover_url"].replace("http://testserver", ""))
    assert default.status_code == 200 and default.headers["content-type"].startswith("image/jpeg")  # standaardomslag, geen upload nodig

    ok = client.post(f"/me/podcasts/{p['id']}/cover", headers=h, json={"image": "data:image/png;base64," + base64.b64encode(png_bytes(1000, 800)).decode()})
    assert ok.status_code == 200 and ok.json()["has_custom_cover"] and ok.json()["cover_url"] != p["cover_url"]
    img = Image.open(io.BytesIO(client.get(ok.json()["cover_url"].replace("http://testserver", "")).content))
    assert img.size == (1400, 1400)  # vierkant uitgesneden
    feed_img = Image.open(Path(os.environ["STORAGE_ROOT"]) / p["id"] / "site" / "cover.jpg")
    assert feed_img.size == (1400, 1400)  # de eigen afbeelding staat in de feed

    for junk in ("geen-afbeelding", base64.b64encode(b"%PDF-1.4 niet echt").decode(), base64.b64encode(png_bytes(200, 200)).decode()):
        res = client.post(f"/me/podcasts/{p['id']}/cover", headers=h, json={"image": junk})
        assert res.status_code == 400, junk
    still = client.get(f"/me/podcasts/{p['id']}", headers=h).json()
    assert still["has_custom_cover"] and still["cover_url"] == ok.json()["cover_url"]  # mislukte upload laat de oude intact

    gone = client.delete(f"/me/podcasts/{p['id']}/cover", headers=h).json()
    assert gone["has_custom_cover"] is False
    assert Image.open(Path(os.environ["STORAGE_ROOT"]) / p["id"] / "site" / "cover.jpg").size == (3000, 3000)  # terug naar standaard


# ---------- stemmen ----------

def test_stemmen_zoeken_en_tijdelijke_storing() -> None:
    h = login("stemmen")
    voices._cache.update(at=0.0, voices=[])
    key = os.environ.pop("ELEVENLABS_API_KEY", None)
    res = client.get("/me/voices", headers=h)
    assert res.status_code == 503 and "tijdelijk" in res.json()["detail"]

    transport = httpx.MockTransport(lambda req: httpx.Response(200, json={"voices": [
        {"voice_id": "v-b", "name": "Daan", "preview_url": "https://x/daan.mp3", "labels": {"gender": "male", "accent": "dutch"}},
        {"voice_id": "v-a", "name": "Fenna", "description": "Warm en helder", "preview_url": "https://x/fenna.mp3"}]}))
    os.environ["ELEVENLABS_API_KEY"] = "test"
    try:
        listed = voices.list_voices(client=httpx.Client(transport=transport))
        assert [v["name"] for v in listed] == ["Daan", "Fenna"] and listed[0]["description"] == "male, dutch"
        assert [v["name"] for v in client.get("/me/voices?q=fen", headers=h).json()] == ["Fenna"]
        # een onbekende stem wordt geweigerd zodra de lijst bekend is; een bekende werkt
        bad = client.post("/me/podcasts", headers=h, json=payload(voice_id="bestaat-niet"))
        assert bad.status_code == 400 and "voice" in bad.json()["detail"]["fields"]
        assert client.post("/me/podcasts", headers=h, json=payload(voice_id="v-a", voice_name="Fenna")).status_code == 201
        # storing: de laatst bekende lijst blijft bruikbaar
        broken = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(500)))
        assert len(voices.list_voices(client=broken, now=1e12)) == 2
    finally:
        voices._cache.update(at=0.0, voices=[])
        if key is None:
            os.environ.pop("ELEVENLABS_API_KEY", None)
        else:
            os.environ["ELEVENLABS_API_KEY"] = key


# ---------- afleveringen ----------

def test_aflevering_lijst_en_detail_met_bronnen_per_onderwerp() -> None:
    h = login("afleveringen")
    p = make(h, topics=["Klimaat", "Ruimtevaart"])
    db = SessionLocal()
    db.add(Episode(show_id=p["id"], guid="episode-1", date="2026-11-02", published="2026-11-02T07:00:00+01:00", title="Wat betekent het nieuwe klimaatakkoord?",
                   blurb="Korte samenvatting.", summary="Lange beschrijving.", file="a.mp3", duration=601,
                   sources=[{"topic": "Klimaat", "title": "Akkoord", "link": "https://nos.nl/a", "source": "NOS"},
                            {"topic": "Ruimtevaart", "title": "Raket", "link": "https://nu.nl/b", "source": "NU.nl"},
                            {"topic": "Klimaat", "title": "Reactie", "link": "https://nos.nl/c", "source": "NOS"}],
                   period_start="2026-11-01T07:00", period_end="2026-11-02T06:30"))
    db.commit()
    db.close()
    listed = client.get(f"/me/podcasts/{p['id']}/episodes", headers=h).json()
    assert [(e["title"], e["duration"], e["status"]) for e in listed] == [("Wat betekent het nieuwe klimaatakkoord?", 601, "published")]
    detail = client.get(f"/me/podcasts/{p['id']}/episodes/episode-1", headers=h).json()
    assert detail["summary"] == "Korte samenvatting." and detail["period_start"].startswith("2026-11-01")
    assert [(g["topic"], len(g["items"])) for g in detail["sources"]] == [("Klimaat", 2), ("Ruimtevaart", 1)]
    assert detail["sources"][0]["items"][0]["link"] == "https://nos.nl/a"
    assert client.get(f"/me/podcasts/{p['id']}/episodes/bestaat-niet", headers=h).status_code == 404
    assert client.get(f"/me/podcasts/{p['id']}", headers=h).json()["status"]["code"] in ("running", "published")


# ---------- meldingen ----------

def _apns_key() -> str:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    return ec.generate_private_key(ec.SECP256R1()).private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()


def test_meldingen_voorkeuren_toestellen_en_versturen() -> None:
    h = login("meldingen")
    state = client.get("/me", headers=h).json()
    assert state["notify_new"] and state["notify_failed"] and not state["push_registered"]
    token = "a" * 64
    assert client.post("/me/devices", headers=h, json={"token": token}).json()["push_registered"] is True
    assert client.post("/me/devices", headers=h, json={"token": token}).json()["push_registered"] is True  # idempotent
    assert client.post("/me/devices", headers=h, json={"token": "kort"}).status_code == 422

    os.environ.update(APNS_KEY_ID="KEY123", APNS_TEAM_ID="TEAM123456", APNS_BUNDLE_ID="nl.generica.personalpodcast", APNS_AUTH_KEY=_apns_key())
    calls: list[dict] = []
    status = {"code": 200}

    def handler(req: httpx.Request) -> httpx.Response:
        calls.append({"url": str(req.url), "topic": req.headers["apns-topic"], "auth": req.headers["authorization"]})
        return httpx.Response(status["code"])

    fake = httpx.Client(transport=httpx.MockTransport(handler))
    db = SessionLocal()
    try:
        from api.models import User
        user = db.query(User).filter(User.apple_sub == "meldingen").one()
        assert push.notify(db, user, "new_episode", "Nieuw", "Titel", client=fake) == 1
        assert calls[0]["url"].endswith(f"/3/device/{token}") and calls[0]["topic"] == "nl.generica.personalpodcast" and calls[0]["auth"].startswith("bearer ")
        # beide typen zijn afzonderlijk uit te zetten
        client.patch("/me/notifications", headers=h, json={"notify_new": False})
        db.refresh(user)
        assert push.notify(db, user, "new_episode", "Nieuw", "Titel", client=fake) == 0
        assert push.notify(db, user, "failed", "Mislukt", "Uitleg", client=fake) == 1
        client.patch("/me/notifications", headers=h, json={"notify_new": True, "notify_failed": False})
        db.refresh(user)
        assert push.notify(db, user, "failed", "Mislukt", "Uitleg", client=fake) == 0
        # een ongeldig toestel wordt opgeruimd
        status["code"] = 410
        assert push.notify(db, user, "new_episode", "Nieuw", "Titel", client=fake) == 0
        db.refresh(user)
        assert user.devices == []
    finally:
        db.close()
        for k in ("APNS_KEY_ID", "APNS_TEAM_ID", "APNS_BUNDLE_ID", "APNS_AUTH_KEY"):
            os.environ.pop(k, None)
    assert push.notify(SessionLocal(), type("U", (), {"notify_new": True, "notify_failed": True, "devices": [1]})(), "failed", "x", "y") == 0  # zonder configuratie niets


# ---------- worker: eerste aflevering, retries, overslaan ----------

def _fake_episode(store, cfg, stamp="2026-11-02-0700") -> dict:
    ep = {"guid": f"episode-{stamp}", "date": "2026-11-02", "published": "2026-11-02T07:00:00+01:00", "title": "Een concrete vraag?",
          "summary": "s", "blurb": "b", "tag": "t", "file": f"{stamp}.mp3", "size": 1, "duration": 600, "chapters": [], "sources": []}
    store.save_episode(ep)
    return ep


def test_worker_eerste_aflevering_melding_retries_en_overslaan() -> None:
    import worker.run as wr
    sent: list[tuple[str, str]] = []
    original_build, original_notify = wr.build, wr.push.notify
    wr.push.notify = lambda db, user, kind, title, body, data=None, client=None: sent.append((kind, title)) or 1
    try:
        db = SessionLocal()
        db.query(Job).update({Job.status: "succeeded"})  # jobs van andere tests doen hier niet mee
        db.commit()
        db.close()
        h = login("worker")
        # 1. succes: aflevering opgeslagen, melding verstuurd
        p = make(h, title="Succes")
        wr.build = lambda cfg, out, no_tts, store=None: _fake_episode(store, cfg)
        assert wr.process_next(50, now=utc(2026, 11, 2, 6, 0)) == 1
        job = [j for j in jobs_of(p["id"])][0]
        assert job.status == "succeeded" and job.attempts == 1
        assert ("new_episode", "Nieuwe aflevering: Succes") in sent
        st = client.get(f"/me/podcasts/{p['id']}", headers=h).json()
        assert st["status"]["code"] == "published" and st["latest_episode"]["title"] == "Een concrete vraag?"

        # 2. tijdelijke fout: opnieuw proberen met uitstel, daarna pas een melding over de mislukte generatie
        q = make(h, title="Storing")
        wr.build = lambda cfg, out, no_tts, store=None: (_ for _ in ()).throw(RuntimeError("ElevenLabs timeout"))
        t0 = utc(2026, 11, 2, 6, 0)
        wr.process_next(50, now=t0)
        job = jobs_of(q["id"])[0]
        assert (job.status, job.attempts) == ("queued", 1) and job.run_after is not None
        assert client.get(f"/me/podcasts/{q['id']}", headers=h).json()["status"]["detail"] == "We proberen het opnieuw…"
        assert not any(k == "failed" for k, _ in sent)  # nog geen melding bij een herstelpoging
        wr.process_next(50, now=t0 + timedelta(minutes=5))  # te vroeg: wacht tot run_after
        assert jobs_of(q["id"])[0].attempts == 1
        wr.process_next(50, now=t0 + timedelta(hours=1))
        wr.process_next(50, now=t0 + timedelta(hours=3))
        job = jobs_of(q["id"])[0]
        assert (job.status, job.attempts) == ("failed", 3)
        assert [k for k, t in sent if "Storing" in t] == ["failed"]  # precies één melding
        st = client.get(f"/me/podcasts/{q['id']}", headers=h).json()["status"]
        assert st["code"] == "failed" and "eerdere afleveringen blijven beschikbaar" in st["detail"].lower() and "timeout" not in st["detail"].lower()

        # 3. geen nieuw nieuws: overgeslagen met uitleg, geen melding, geen aflevering
        r = make(h, title="Stil")
        wr.build = lambda cfg, out, no_tts, store=None: None
        wr.process_next(50, now=t0)
        job = jobs_of(r["id"])[0]
        assert job.status == "skipped" and "geen nieuw nieuws" in job.error.lower()
        st = client.get(f"/me/podcasts/{r['id']}", headers=h).json()
        assert st["status"]["code"] == "skipped" and st["latest_episode"] is None
        assert not any("Stil" in t for _, t in sent)
    finally:
        wr.build, wr.push.notify = original_build, original_notify


def main() -> None:
    tests = [value for name, value in globals().items() if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print("OK", test.__name__)
    print(f"OK: {len(tests)} tests")


if __name__ == "__main__":
    main()
