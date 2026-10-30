"""Lokale object-storage voor mp3's en site-bestanden (S3 later via STORAGE_ROOT / adapter)."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

STORAGE_ROOT = Path(os.environ.get("STORAGE_ROOT", "data/storage"))


def show_dir(show_id: str) -> Path:
    path = STORAGE_ROOT / show_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def audio_path(show_id: str, filename: str) -> Path:
    path = show_dir(show_id) / "audio"
    path.mkdir(parents=True, exist_ok=True)
    return path / filename


def site_dir(show_id: str) -> Path:
    path = show_dir(show_id) / "site"
    path.mkdir(parents=True, exist_ok=True)
    return path


def store_audio(show_id: str, src: Path) -> Path:
    dest = audio_path(show_id, src.name)
    shutil.copy2(src, dest)
    return dest
