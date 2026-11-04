"""Object-storage voor mp3's, omslagen en site-bestanden.

Zonder `SPACES_BUCKET` is dit alleen de lokale map `STORAGE_ROOT` (ontwikkeling, docker-compose met gedeeld volume).
Met `SPACES_BUCKET` (DigitalOcean Spaces, S3-compatibel) is Spaces de bron van waarheid en is `STORAGE_ROOT` een cache:
de worker en de API hebben elk hun eigen lokale schijf. Schrijven gaat via `push`/`push_show`, lezen via `ensure`.
"""
from __future__ import annotations

import os
import shutil
from functools import lru_cache
from pathlib import Path

STORAGE_ROOT = Path(os.environ.get("STORAGE_ROOT", "data/storage"))
SPACES_BUCKET = os.environ.get("SPACES_BUCKET", "")


def remote_enabled() -> bool:
    return bool(SPACES_BUCKET)


@lru_cache(maxsize=1)
def _client():
    import boto3
    region = os.environ.get("SPACES_REGION", "ams3")
    return boto3.client(
        "s3",
        region_name=region,
        endpoint_url=os.environ.get("SPACES_ENDPOINT", f"https://{region}.digitaloceanspaces.com"),
        aws_access_key_id=os.environ["SPACES_KEY"],
        aws_secret_access_key=os.environ["SPACES_SECRET"],
    )


def _key(path: Path) -> str:
    return path.resolve().relative_to(STORAGE_ROOT.resolve()).as_posix()


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


def ensure(path: Path, fresh: bool = False) -> bool:
    """Zorgt dat `path` lokaal bestaat; haalt het zo nodig uit Spaces. Geeft terug of het bestand er is.
    `fresh=True` haalt het altijd opnieuw op (feed en site veranderen onder dezelfde naam, audio en omslagen niet)."""
    if path.is_file() and not (fresh and remote_enabled()):
        return True
    if not remote_enabled():
        return False
    from botocore.exceptions import ClientError
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".part")
    try:
        _client().download_file(SPACES_BUCKET, _key(path), str(tmp))
    except ClientError:
        tmp.unlink(missing_ok=True)
        return path.is_file()
    tmp.replace(path)
    return True


def push(path: Path) -> None:
    """Zet één lokaal bestand in Spaces (no-op zonder Spaces)."""
    if remote_enabled() and path.is_file():
        _client().upload_file(str(path), SPACES_BUCKET, _key(path))


def push_tree(root: Path) -> None:
    if not remote_enabled():
        return
    for f in root.rglob("*"):
        if f.is_file() and not f.name.endswith(".part"):
            push(f)


def remove(path: Path) -> None:
    """Verwijdert één bestand lokaal en in Spaces."""
    path.unlink(missing_ok=True)
    if remote_enabled():
        _client().delete_object(Bucket=SPACES_BUCKET, Key=_key(path))


def remove_show(show_id: str) -> None:
    """Verwijdert alle bestanden van een podcast, lokaal en in Spaces."""
    shutil.rmtree(STORAGE_ROOT / show_id, ignore_errors=True)
    if not remote_enabled():
        return
    client = _client()
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=SPACES_BUCKET, Prefix=f"{show_id}/"):
        objs = [{"Key": o["Key"]} for o in page.get("Contents", [])]
        if objs:
            client.delete_objects(Bucket=SPACES_BUCKET, Delete={"Objects": objs})


def store_audio(show_id: str, src: Path) -> Path:
    dest = audio_path(show_id, src.name)
    shutil.copy2(src, dest)
    push(dest)
    return dest
