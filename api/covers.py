"""Omslagafbeeldingen: upload controleren en bijsnijden tot een vierkante JPEG (Apple wil 1400-3000 px)."""
from __future__ import annotations

import base64
import binascii
import io
import os

from PIL import Image, UnidentifiedImageError

MAX_BYTES = 10_000_000
MIN_SIDE = 600
OUT_SIDE = 1400


class BadCover(ValueError):
    """De upload is geen bruikbare afbeelding."""


def decode(data: str) -> bytes:
    """Base64 of data-URL naar bytes."""
    if "," in data[:100] and data.lstrip().startswith("data:"):
        data = data.split(",", 1)[1]
    try:
        raw = base64.b64decode(data, validate=False)
    except (binascii.Error, ValueError) as e:
        raise BadCover("De afbeelding kon niet worden gelezen") from e
    if len(raw) > MAX_BYTES:
        raise BadCover("De afbeelding is te groot (maximaal 10 MB)")
    return raw


def normalize(raw: bytes) -> bytes:
    """Midden uitsnijden tot een vierkant en opslaan als JPEG van OUT_SIDE x OUT_SIDE."""
    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as e:
        raise BadCover("Dit bestand is geen afbeelding die we kunnen gebruiken (kies een JPEG of PNG)") from e
    if img.format not in ("JPEG", "PNG", "WEBP", "HEIF", "MPO"):
        raise BadCover("Kies een JPEG- of PNG-afbeelding")
    if min(img.size) < MIN_SIDE:
        raise BadCover(f"De afbeelding is te klein (minimaal {MIN_SIDE} bij {MIN_SIDE} pixels)")
    img = img.convert("RGB")
    side = min(img.size)
    left, top = (img.width - side) // 2, (img.height - side) // 2
    img = img.crop((left, top, left + side, top + side)).resize((OUT_SIDE, OUT_SIDE), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, "JPEG", quality=88)
    return out.getvalue()


def save_atomic(dest, content: bytes) -> None:
    """Schrijf eerst naar een tijdelijk bestand, zodat een mislukte upload de vorige afbeelding intact laat."""
    tmp = f"{dest}.tmp"
    with open(tmp, "wb") as f:
        f.write(content)
    os.replace(tmp, dest)
