import os
import time
from pathlib import Path

import requests

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}"
CHUNK_CHARS = 2500


def _chunks(text: str) -> list[str]:
    out, cur = [], ""
    for para in text.split("\n"):
        para = para.strip()
        if not para:
            continue
        if cur and len(cur) + len(para) + 1 > CHUNK_CHARS:
            out.append(cur)
            cur = ""
        cur = f"{cur}\n{para}".strip()
    if cur:
        out.append(cur)
    return out


def synthesize(text: str, cfg: dict, dest: Path) -> None:
    voice = cfg["voice"]
    headers = {"xi-api-key": os.environ["ELEVENLABS_API_KEY"]}
    parts = _chunks(text)
    with dest.open("wb") as f:
        for i, part in enumerate(parts):
            body = {"text": part, "model_id": voice["model_id"]}
            if i > 0:
                body["previous_text"] = parts[i - 1][-300:]
            if i < len(parts) - 1:
                body["next_text"] = parts[i + 1][:300]
            for attempt in range(4):
                r = requests.post(
                    API.format(voice=voice["voice_id"]),
                    params={"output_format": "mp3_44100_64"},
                    headers=headers,
                    json=body,
                    timeout=180,
                )
                if r.status_code in (429, 500, 502, 503) and attempt < 3:
                    time.sleep(5 * (attempt + 1))
                    continue
                r.raise_for_status()
                break
            f.write(r.content)
            print(f"Audio deel {i + 1}/{len(parts)} klaar")
