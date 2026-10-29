"""Lokale instellingenpagina: `python -m podcast ui` opent http://127.0.0.1:8765.

Alleen bereikbaar vanaf deze computer. Wijzigt config.yaml (met behoud van commentaar) en pronunciation.json,
en kan committen/pushen en de GitHub-workflow starten (via git en de gh-opdracht).
"""
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import calendar
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import feedparser
import yaml
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

ROOT = Path.cwd()
PAGE = Path(__file__).with_name("ui_page.html")
TRACKED = ["config.yaml", "pronunciation.json"]  # bestanden die de pagina mag committen

ryaml = YAML()
ryaml.preserve_quotes = True
ryaml.width = 4096
ryaml.indent(mapping=2, sequence=4, offset=2)


class ApiError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


# ---------- config ----------

def read_config() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text())


def _coerce(current, value):
    """Behoudt het type van de bestaande waarde (getal blijft getal, tekst blijft tekst)."""
    if isinstance(current, bool):
        return bool(value)
    if isinstance(current, (int, float)):
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ApiError(f"'{value}' is geen getal")
        return int(number) if isinstance(current, int) and number == int(number) else number
    return str(value)


def _topic_node(topic: dict) -> CommentedMap:
    node = CommentedMap()
    node["name"] = DoubleQuotedScalarString(topic["name"].strip())
    node["description"] = DoubleQuotedScalarString(topic.get("description", "").strip())
    keywords = [k.strip() for k in topic.get("keywords", []) if k.strip()]
    if keywords:
        seq = CommentedSeq(DoubleQuotedScalarString(k) for k in keywords)
        seq.fa.set_flow_style()
        node["keywords"] = seq
    node["feeds"] = CommentedSeq(f.strip() for f in topic.get("feeds", []) if f.strip())
    return node


def write_config(payload: dict) -> list[str]:
    """Past alleen aan wat is gewijzigd; geeft de gewijzigde onderdelen terug."""
    path = ROOT / "config.yaml"
    doc = ryaml.load(path.read_text())
    changed = []

    for dotted, value in payload.get("values", {}).items():
        *parents, last = dotted.split(".")
        node = doc
        for p in parents:
            node = node[p]
        current = node.get(last)
        new = _coerce(current, value)
        if new != current:
            node[last] = new
            changed.append(dotted)

    topics = payload.get("topics")
    if topics is not None:
        for t in topics:
            if not t.get("name", "").strip():
                raise ApiError("Elk onderwerp heeft een naam nodig")
            if not [f for f in t.get("feeds", []) if f.strip()]:
                raise ApiError(f"Onderwerp '{t['name']}' heeft minstens één feed nodig")
        for t in topics:  # ongeldige regex meteen melden, in plaats van pas bij de run
            for k in t.get("keywords", []):
                try:
                    re.compile(k)
                except re.error as e:
                    raise ApiError(f"Trefwoord '{k}' bij '{t['name']}' is geen geldige regex: {e}")
        plain = [{"name": t["name"].strip(), "description": t.get("description", "").strip(),
                  "keywords": [k.strip() for k in t.get("keywords", []) if k.strip()],
                  "feeds": [f.strip() for f in t.get("feeds", []) if f.strip()]} for t in topics]
        current = [{"name": t["name"], "description": t.get("description", ""),
                    "keywords": list(t.get("keywords") or []), "feeds": list(t["feeds"])}
                   for t in read_config()["topics"]]
        if plain != current:
            doc["topics"] = CommentedSeq(_topic_node(t) for t in topics)
            changed.append("topics")

    pron = payload.get("pronunciation")
    if pron is not None and pron != (read_config().get("pronunciation") or {}):
        node = doc.get("pronunciation")
        if node is None:
            doc["pronunciation"] = node = CommentedMap()
        for k in [k for k in node if k not in pron]:  # op zijn plaats aanpassen: commentaar blijft staan
            del node[k]
        for k, v in pron.items():
            if node.get(k) != v:
                node[k] = DoubleQuotedScalarString(v)
        changed.append("pronunciation")

    if changed:
        with path.open("w") as f:
            ryaml.dump(doc, f)
        yaml.safe_load(path.read_text())  # moet nog steeds geldige yaml zijn
    return changed


def learned_path() -> Path:
    return ROOT / "pronunciation.json"


# ---------- opdrachten ----------

def run(cmd: list[str], timeout: int = 60, check: bool = True) -> str:
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise ApiError(f"'{cmd[0]}' is niet geïnstalleerd")
    except subprocess.TimeoutExpired:
        raise ApiError(f"'{' '.join(cmd[:3])}' duurde te lang")
    out = (p.stdout + p.stderr).strip()
    if check and p.returncode != 0:
        raise ApiError(out or f"'{cmd[0]}' faalde")
    return out


def git_status() -> dict:
    dirty = run(["git", "status", "--porcelain", "--", *TRACKED], check=False)
    try:
        unpushed = int(run(["git", "rev-list", "--count", "@{u}..HEAD"], check=False) or 0)
    except ValueError:
        unpushed = 0
    return {"dirty": [line.split(maxsplit=1)[-1] for line in dirty.splitlines() if line.strip()], "unpushed": unpushed}


def publish(message: str) -> str:
    message = (message or "Instellingen aangepast").strip()[:200]
    run(["git", "add", "--", *TRACKED])
    staged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode != 0
    if staged:
        run(["git", "commit", "-m", message])
    elif git_status()["unpushed"] == 0:
        return "Niets te publiceren: alles staat al op GitHub."
    run(["git", "pull", "--rebase", "--autostash"], timeout=120)
    run(["git", "push"], timeout=120)
    return "Gepubliceerd: de volgende run gebruikt deze instellingen."


def trigger(feed_only: bool, max_minutes) -> str:
    if git_status()["dirty"] or git_status()["unpushed"]:
        raise ApiError("Er zijn wijzigingen die nog niet op GitHub staan. Publiceer ze eerst; "
                       "de workflow gebruikt de instellingen uit GitHub.")
    cmd = ["gh", "workflow", "run", "daily.yml"]
    if feed_only:
        cmd += ["-f", "feed_only=true"]
    elif max_minutes not in (None, ""):
        cmd += ["-f", f"max_minutes={float(max_minutes):g}"]
    run(cmd)
    return "Workflow gestart. Volg de voortgang hieronder."


def list_runs() -> list[dict]:
    out = run(["gh", "run", "list", "--limit", "8", "--json", "databaseId,status,conclusion,createdAt,event,url"])
    return json.loads(out)


def preview() -> str:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise ApiError("ANTHROPIC_API_KEY ontbreekt in de omgeving waarin de pagina draait. "
                       "Start de pagina opnieuw met: export ANTHROPIC_API_KEY=... && python -m podcast ui")
    return run([sys.executable, "-m", "podcast", "build", "--no-tts", "--out", "out/preview"], timeout=900, check=False)[-12000:]


def episodes() -> list[dict]:
    p = ROOT / "episodes.json"
    return json.loads(p.read_text()) if p.exists() else []


def delete_episode(guid: str) -> str:
    keep = [e for e in episodes() if e["guid"] != guid]
    victim = next((e for e in episodes() if e["guid"] == guid), None)
    if victim is None:
        raise ApiError("Aflevering niet gevonden", 404)
    run(["gh", "release", "delete", victim["tag"], "--yes", "--cleanup-tag"], check=False)
    (ROOT / "episodes.json").write_text(json.dumps(keep, ensure_ascii=False, indent=2) + "\n")
    run(["git", "add", "episodes.json"])
    run(["git", "commit", "-m", f"Aflevering verwijderd: {victim['title'][:80]}"])
    run(["git", "pull", "--rebase", "--autostash"], timeout=120)
    run(["git", "push"], timeout=120)
    run(["gh", "workflow", "run", "daily.yml", "-f", "feed_only=true"])
    return "Aflevering verwijderd; de feed wordt opnieuw gepubliceerd."


def test_feeds(topic: dict, lookback_hours: float) -> list[dict]:
    keywords = [k for k in topic.get("keywords", []) if k.strip()]
    pattern = re.compile("|".join(keywords), re.I) if keywords else None
    cutoff = time.time() - lookback_hours * 3600
    socket.setdefaulttimeout(20)

    def one(url: str) -> dict:
        try:
            feed = feedparser.parse(url)
        except Exception as e:  # noqa: BLE001
            return {"url": url, "error": str(e)}
        status = feed.get("status")
        if not feed.entries:
            return {"url": url, "status": status, "total": 0, "recent": 0, "matches": 0, "samples": [],
                    "error": f"geen berichten (status {status})"}
        recent = [e for e in feed.entries
                  if not (e.get("published_parsed") or e.get("updated_parsed"))
                  or calendar.timegm(e.get("published_parsed") or e.get("updated_parsed")) >= cutoff]
        hit = [e for e in recent if not pattern or pattern.search(f"{e.get('title', '')} {e.get('summary', '')}")]
        return {"url": url, "status": status, "total": len(feed.entries), "recent": len(recent),
                "matches": len(hit), "samples": [e.get("title", "")[:90] for e in hit[:3]]}

    with ThreadPoolExecutor(6) as pool:
        return list(pool.map(one, [f for f in topic.get("feeds", []) if f.strip()]))


# ---------- http ----------

def make_handler(token: str, port: int):
    allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # stil
            pass

        def _send(self, status: int, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", f"{ctype}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _guard(self) -> bool:
            if self.headers.get("Host") not in allowed_hosts:  # beschermt tegen DNS-rebinding
                self._send(403, {"error": "Host niet toegestaan"})
                return False
            return True

        def do_GET(self):
            if not self._guard():
                return
            if self.path == "/":
                html = PAGE.read_text().replace("__TOKEN__", token)
                return self._send(200, html.encode(), "text/html")
            self._api("GET")

        def do_POST(self):
            if not self._guard():
                return
            self._api("POST")

        def _api(self, method: str):
            if not self.path.startswith("/api/"):
                return self._send(404, {"error": "niet gevonden"})
            if self.headers.get("X-Token") != token:
                return self._send(403, {"error": "ongeldig token; open de pagina opnieuw"})
            body = {}
            if method == "POST":
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length) or b"{}")
            try:
                self._send(200, route(method, self.path[5:], body))
            except ApiError as e:
                self._send(e.status, {"error": str(e)})
            except Exception as e:  # noqa: BLE001
                self._send(500, {"error": f"{type(e).__name__}: {e}"})

    return Handler


def route(method: str, path: str, body: dict):
    if method == "GET":
        if path == "state":
            learned = json.loads(learned_path().read_text()) if learned_path().exists() else {}
            return {"config": read_config(), "learned": learned, "git": git_status(),
                    "episodes": [{k: e[k] for k in ("guid", "date", "title", "duration")} for e in episodes()],
                    "has_gh": shutil.which("gh") is not None}
        if path == "runs":
            return list_runs()
        raise ApiError("onbekend", 404)
    if path == "save":
        changed = write_config(body)
        if "learned" in body:
            learned_path().write_text(json.dumps(dict(sorted(body["learned"].items())), ensure_ascii=False, indent=1) + "\n")
            changed.append("learned")
        return {"changed": changed, "git": git_status()}
    if path == "test-feeds":
        return test_feeds(body["topic"], float(body.get("lookback_hours", 72)))
    if path == "publish":
        return {"message": publish(body.get("message", "")), "git": git_status()}
    if path == "run":
        return {"message": trigger(bool(body.get("feed_only")), body.get("max_minutes"))}
    if path == "preview":
        return {"output": preview()}
    if path == "delete-episode":
        return {"message": delete_episode(body["guid"])}
    raise ApiError("onbekend", 404)


def serve(port: int = 8765, open_browser: bool = True) -> None:
    token = secrets.token_urlsafe(24)
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(token, port))
    url = f"http://127.0.0.1:{port}/"
    print(f"Instellingen: {url}  (Ctrl+C om te stoppen)")
    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
