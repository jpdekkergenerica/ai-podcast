# yourownpod: multi-tenant config-app

## Stack

- **UI:** Monsey design system in [`app/`](app/) (Paper/LED, Geist Pixel display)
- **iOS:** WKWebView-host in [`ios/`](ios/)
- **API:** FastAPI in [`api/`](api/) + worker in [`worker/`](worker/)
- **CLI:** bestaande `python -m podcast build` blijft YAML gebruiken via `FileShowStore`

## Snel starten

```bash
pip install -r requirements-api.txt
export AUTH_DEV_MODE=1 WORKER_INLINE=1
python -m api.main
# UI: http://127.0.0.1:8000/app/ui_kits/podcast-app/mobile.html
# Kit-preview: http://127.0.0.1:8000/app/ui_kits/podcast-app/index.html
```

Migratie huidige show:

```bash
python scripts/migrate_yaml_to_db.py --apple-sub dev-user --email j.p.dekker@generica.nl
```

## Tests en productie

```bash
python -m tests.test_api        # auth, tenant-isolatie, limieten, feed-toegang
```

Productie: zet `API_JWT_SECRET` (minstens 32 tekens), `APPLE_CLIENT_ID`, `PUBLIC_BASE_URL` (https) en laat `AUTH_DEV_MODE` weg; zonder geheim start de API niet.
`WORKER_INLINE` staat standaard uit; draai `python -m worker.run loop` als aparte worker.

## Planning

Elke gebruiker kiest zelf of er automatisch een aflevering komt, op welke dagen en hoe laat (Aflevering → Planning).
Standaard staat de planning **uit**, zodat er nooit ongevraagd kosten ontstaan; handmatig bouwen met de knop Bouw blijft mogelijk (1 per dag).
De planning staat in `shows.schedule` (`enabled`, `days` 0 = maandag … 6 = zondag, `time` HH:MM, `timezone`). De worker (`python -m worker.run loop`)
zet elke ronde de shows klaar die aan de beurt zijn (`enqueue_due`); een late start wordt tot 2 uur na het gekozen tijdstip ingehaald en er is hooguit één geplande run per dag.
Zonder eigen worker kan `python -m worker.run enqueue-due` elke 15 minuten draaien (zie `.github/workflows/enqueue.yml`).
