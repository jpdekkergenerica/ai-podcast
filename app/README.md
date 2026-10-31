# Config-UI (Guardia-stijl)

yourownpod: config-app in de stijl van het **Guardia** UI-kit (`brondata/Guardia - AI Insurance Dashboard Kit`): pagina #fbfbfb, witte kaarten met 1px rand en 12px radius, paars #72188b als merkkleur, Geist Medium, knoppen 6px, velden 8px. De tokens staan in `tokens/guardia.css` en liggen over de oorspronkelijke Monsey-componenten heen (zelfde variabelen, nieuwe waarden). Licht en donker volgen dezelfde structuur.

## Schermen

| Tab | Inhoud |
|-----|--------|
| Home | Status, feed-URL kopiëren, open Podcasts, bouw nu |
| Onderwerpen | CRUD + feed-test |
| Aflevering | Duur, focus, herhaling, CTA, uitspraak |
| Account | Thema, token vernieuwen, uitloggen, account wissen |

Luisteren gebeurt **niet** in deze app — alleen in Apple Podcasts via de privé-feed.

## Lokaal bekijken

```bash
# Terminal 1 — API
pip install -r requirements-api.txt
export AUTH_DEV_MODE=1 WORKER_INLINE=1
python -m api.main

# Open de kit-preview (twee phone frames):
open http://127.0.0.1:8000/app/ui_kits/podcast-app/index.html

# Of full-bleed mobiel (voor iOS WKWebView):
open http://127.0.0.1:8000/app/ui_kits/podcast-app/mobile.html
```

Zonder API start je alleen een static server vanuit `app/`:

```bash
cd app && python3 -m http.server 8766
open http://127.0.0.1:8766/ui_kits/podcast-app/index.html
```

## Designbron

Geïmporteerd uit `brondata/monsey-claude-html_…`: tokens, fonts, line icons, core/forms/navigation/overlays/feedback-componenten. Podcast-specifieke schermen staan in `ui_kits/podcast-app/`.
