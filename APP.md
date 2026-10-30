# Multi-tenant config-app

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
