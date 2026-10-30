# Config-UI (Monsey kit)

Persoonlijke podcast-config-app gebouwd met het Monsey design system uit `brondata/` (Paper/LED, Geist Pixel display, soft shell / pixel core).

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
