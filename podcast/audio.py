import json
import re
import shutil
import subprocess
from pathlib import Path

from mutagen.id3 import CHAP, CTOC, TIT2, CTOCFlags, ID3, ID3NoHeaderError

BITRATE = 128_000  # CBR, mono spraak
TARGET = "I=-16:TP=-1:LRA=11"  # -16 LUFS / -1 dBTP volgens Apple Podcasts en Spotify
# hoogdoorlaat op 80 Hz en milde compressie (ratio 2:1) voor de loudness-normalisatie
FILTERS = "highpass=f=80,acompressor=threshold=-21dB:ratio=2:attack=20:release=250"


def seconds_for(num_bytes: int) -> float:
    return num_bytes * 8 / BITRATE


def master(src: Path, dest: Path) -> None:
    """Normaliseert naar -16 LUFS / -1 dBTP en codeert naar 128 kbps CBR mono (ffmpeg, twee passes)."""
    if not shutil.which("ffmpeg"):
        print("Waarschuwing: ffmpeg niet gevonden, audio is niet genormaliseerd")
        shutil.copy(src, dest)
        return
    try:
        first = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", str(src),
             "-af", f"{FILTERS},loudnorm={TARGET}:print_format=json", "-f", "null", "-"],
            capture_output=True, text=True, check=True,
        )
        m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", first.stderr, re.S).group())
        measured = (f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
                    f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
             "-af", f"{FILTERS},loudnorm={TARGET}:{measured}",
             "-ar", "44100", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "128k", str(dest)],
            check=True,
        )
        print(f"Audio genormaliseerd (gemeten {m['input_i']} LUFS -> -16 LUFS)")
    except (subprocess.CalledProcessError, AttributeError, KeyError, ValueError) as e:
        print(f"Waarschuwing: mastering mislukt ({e}), ruwe audio gebruikt")
        shutil.copy(src, dest)


def tag_chapters(path: Path, chapters: list[tuple[str, int, int]]) -> None:
    """Schrijft ID3-hoofdstukken (titel, start_ms, einde_ms); Apple Podcasts toont ze in de speler."""
    try:
        tags = ID3(path)
    except ID3NoHeaderError:
        tags = ID3()
    ids = []
    for i, (title, start, end) in enumerate(chapters):
        cid = f"chp{i}"
        ids.append(cid)
        tags.add(CHAP(element_id=cid, start_time=start, end_time=end,
                      start_offset=0xFFFFFFFF, end_offset=0xFFFFFFFF,
                      sub_frames=[TIT2(encoding=3, text=title)]))
    tags.add(CTOC(element_id="toc", flags=CTOCFlags.TOP_LEVEL | CTOCFlags.ORDERED,
                  child_element_ids=ids, sub_frames=[TIT2(encoding=3, text="Hoofdstukken")]))
    tags.save(path, v2_version=3)
