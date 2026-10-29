"""Rooktest van de lokale instellingenpagina in een wegwerpkopie met een eigen git-remote.

Gebruik (vanuit de projectmap):  python -m tests.smoke_ui      (vereist: pip install -r requirements-ui.txt)
Raakt het echte config.yaml en GitHub niet aan.
"""
import difflib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PORT = 8769
B = f"http://127.0.0.1:{PORT}"


def git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def main() -> None:
    tmp = Path(tempfile.mkdtemp())
    work, remote = tmp / "work", tmp / "remote.git"
    work.mkdir()
    for name in ("config.yaml", "episodes.json", "covered.json", "pronunciation.json"):
        shutil.copy(ROOT / name, work / name)
    shutil.copytree(ROOT / "podcast", work / "podcast", ignore=shutil.ignore_patterns("__pycache__"))
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    git("init", "-q", "-b", "main", cwd=work)
    git("config", "user.email", "t@t", cwd=work)
    git("config", "user.name", "t", cwd=work)
    git("add", "-A", cwd=work)
    git("commit", "-qm", "init", cwd=work)
    git("remote", "add", "origin", str(remote), cwd=work)
    git("push", "-q", "-u", "origin", "main", cwd=work)
    original = (work / "config.yaml").read_text()

    server = subprocess.Popen([sys.executable, "-m", "podcast", "ui", "--port", str(PORT), "--no-browser"],
                              cwd=work, env={"PYTHONPATH": str(work), "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"},
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try:
                page = urllib.request.urlopen(B + "/").read().decode()
                break
            except OSError:
                time.sleep(0.25)
        token = re.search(r'const TOKEN = "([^"]+)"', page).group(1)

        def call(path, body=None, tok=token, host=None):
            req = urllib.request.Request(f"{B}/api/{path}", data=None if body is None else json.dumps(body).encode(),
                                         method="GET" if body is None else "POST")
            req.add_header("X-Token", tok)
            if host:
                req.add_header("Host", host)
            try:
                r = urllib.request.urlopen(req)
                return r.status, json.loads(r.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())

        assert call("state", tok="fout")[0] == 403 and call("state", host="evil.com")[0] == 403
        _, state = call("state")
        topics = state["config"]["topics"]
        topics[0]["keywords"] = topics[0]["keywords"] + ["extra"]
        _, r = call("save", {"values": {"duration.max_minutes": "12", "voice.settings.stability": "0.5"},
                             "topics": topics, "pronunciation": {**state["config"]["pronunciation"], "KPN": "kaa-pee-en"},
                             "learned": {"Test": "test"}})
        assert set(r["changed"]) == {"duration.max_minutes", "voice.settings.stability", "topics", "pronunciation", "learned"}
        text = (work / "config.yaml").read_text()
        cfg = yaml.safe_load(text)
        assert cfg["duration"]["max_minutes"] == 12 and cfg["topics"][0]["keywords"][-1] == "extra"
        assert cfg["pronunciation"]["KPN"] == "kaa-pee-en"
        assert "# bovengrens van de aflevering" in text and "# de naam van de podcast" in text, "commentaar verloren"
        diff = [x for x in difflib.unified_diff(original.splitlines(), text.splitlines(), lineterm="", n=0)
                if x[:1] in "+-" and x[:3] not in ("+++", "---")]
        assert len(diff) <= 10, f"te grote diff: {len(diff)} regels"
        assert call("save", {"values": {"duration.max_minutes": "12"}})[1]["changed"] == []
        assert "regex" in call("save", {"topics": [{"name": "x", "feeds": ["f"], "keywords": ["(["]}]})[1]["error"]
        assert call("save", {"values": {"duration.max_minutes": "abc"}})[0] == 400
        (work / "fx.xml").write_text('<rss version="2.0"><channel><title>t</title><item><title>Dakloze krijgt huis</title>'
                                     '<link>http://x/1</link><description>d</description></item></channel></rss>')
        _, res = call("test-feeds", {"topic": {"feeds": ["fx.xml"], "keywords": ["\\bdaklo"]}, "lookback_hours": 1e6})
        assert res[0]["matches"] == 1, res
        _, r = call("publish", {"message": "test"})
        assert "Gepubliceerd" in r["message"] and r["git"] == {"dirty": [], "unpushed": 0}, r
        log = subprocess.run(["git", "--git-dir", str(remote), "log", "--oneline", "-1"], capture_output=True, text=True).stdout
        assert "test" in log, log
        print("OK: pagina, opslaan (minimale diff, commentaar), validatie, feed-test, publiceren en beveiliging kloppen")
    finally:
        server.terminate()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
