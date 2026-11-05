#!/usr/bin/env python3
"""Verwijdert alle gebruikers behalve één, met hun podcasts, afleveringen, meldingstoestellen en bestanden in de opslag
(en losse bestanden van podcasts die niet meer bestaan).

Gebruik, in de DigitalOcean-console van de component `api` (daar staan DATABASE_URL en de Spaces-sleutels al in):
  python scripts/purge_other_users.py --keep jp@seastarters.nl            # proef: laat alleen zien wat er weg zou gaan
  python scripts/purge_other_users.py --keep jp@seastarters.nl --apply    # verwijdert echt, niet terug te draaien
Staat het e-mailadres niet in de database (bijv. een verborgen Apple-adres), kies dan met --keep-id <id uit de lijst>.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from api import storage  # noqa: E402
from api.db import SessionLocal, init_db  # noqa: E402
from api.models import User  # noqa: E402


def storage_prefixes() -> list[str]:
    """Mappen op het hoogste niveau van de opslag: elke map is één podcast (id)."""
    if storage.remote_enabled():
        found: list[str] = []
        pages = storage._client().get_paginator("list_objects_v2").paginate(Bucket=storage.SPACES_BUCKET, Delimiter="/")
        for page in pages:
            found += [p["Prefix"].rstrip("/") for p in page.get("CommonPrefixes", [])]
        return found
    root = storage.STORAGE_ROOT
    return [p.name for p in root.iterdir() if p.is_dir()] if root.is_dir() else []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", help="e-mailadres van de gebruiker die blijft")
    ap.add_argument("--keep-id", help="id van de gebruiker die blijft (als het e-mailadres niet in de database staat)")
    ap.add_argument("--apply", action="store_true", help="echt verwijderen (zonder deze vlag is het een proef)")
    args = ap.parse_args()
    if not args.keep and not args.keep_id:
        ap.error("geef --keep <e-mail> of --keep-id <id>")

    init_db()
    db = SessionLocal()
    users = db.query(User).order_by(User.created_at).all()
    print(f"{len(users)} gebruiker(s) in de database:")
    for u in users:
        episodes = sum(len(s.episodes) for s in u.shows)
        print(f"  {u.id}  {u.email or '(geen e-mail)':35}  podcasts: {len(u.shows)}  afleveringen: {episodes}  aangemaakt: {u.created_at:%Y-%m-%d %H:%M}")

    keep = [u for u in users if (args.keep_id and u.id == args.keep_id) or (args.keep and (u.email or "").lower() == args.keep.lower())]
    if len(keep) != 1:
        print(f"\nGestopt: {len(keep)} gebruikers komen overeen met jouw keuze, het moet er precies één zijn. Er is niets verwijderd.")
        print("Tip: neem het id van jouw gebruiker uit de lijst hierboven en gebruik --keep-id <id>.")
        return 2
    keeper = keep[0]
    others = [u for u in users if u.id != keeper.id]
    keep_show_ids = {s.id for s in keeper.shows}
    other_show_ids = {s.id for u in others for s in u.shows}
    orphans = [p for p in storage_prefixes() if p not in keep_show_ids and p not in other_show_ids and not p.startswith("_")]

    print(f"\nBlijft: {keeper.email or keeper.id} ({len(keeper.shows)} podcast(s))")
    for u in others:
        print(f"Weg: {u.email or '(geen e-mail)'} ({u.id}): {len(u.shows)} podcast(s), {sum(len(s.episodes) for s in u.shows)} aflevering(en)")
    print(f"Losse bestandsmappen in de opslag zonder podcast: {len(orphans)}")

    if not args.apply:
        print("\nDit was een proef; er is niets verwijderd. Voeg --apply toe om echt te verwijderen.")
        return 0

    for u in others:
        for show in u.shows:
            storage.remove_show(show.id)
        db.delete(u)
        db.commit()
    for prefix in orphans:
        storage.remove_show(prefix)
    left = db.query(User).count()
    print(f"\nKlaar: {len(others)} gebruiker(s) en {len(orphans)} losse mappen verwijderd. Nu {left} gebruiker in de database.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
