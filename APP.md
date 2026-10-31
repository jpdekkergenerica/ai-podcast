# yourownpod: multi-tenant config-app

## Stack

- **UI:** Guardia-stijl in [`app/`](app/) (paars, Geist, kaarten)
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

## Functionele specificatie (v1)

De app volgt `Functionele_specificatie_persoonlijke_podcasts.docx`:

- **Meerdere podcasts** per gebruiker, elk met eigen onderwerpen (vrije tekst, variabel aantal), eigen bronnen (optioneel), duur (5/10/15/20 min),
  stem (via ElevenLabs), vertelstijl (zakelijk/informeel/verhalend), omslag (optioneel) en planning. Elke podcast heeft een eigen persoonlijke feed.
- **Direct de eerste aflevering** na aanmaken; daarna volgens de planning. Er is geen knop om handmatig een extra aflevering te maken en geen goedkeuringsstap.
- **Planning:** dagelijks, werkdagen, wekelijks of elke X dagen (2-30), op een zelfgekozen tijdstip waarop de aflevering klaarstaat (de generatie start 45 minuten eerder;
  een gemiste start wordt tot 2 uur erna ingehaald). `api/schedule.py` rekent de volgende publicatie uit. Hooguit één aflevering per dag.
- **Nieuws:** per onderwerp zoekt het model zelf nieuws (webzoektool van Anthropic) sinds de vorige aflevering (de eerste: één interval terug) en leest het de eigen RSS-bronnen.
  Alleen berichten met een adres dat echt in de zoekresultaten stond doen mee (geen verzonnen nieuws); betrouwbaarheid telt mee bij het scoren. Bij weinig nieuws vult het script aan met herkenbare achtergrond.
  Is er helemaal geen nieuws, dan wordt de aflevering overgeslagen met uitleg.
- **Fouten:** tijdelijke fouten worden hooguit 3 keer opnieuw geprobeerd (15, 30 minuten uitstel); daarna status "Mislukt" en een melding. Eerdere afleveringen blijven beschikbaar.
- **Meldingen:** pushmelding bij een nieuwe aflevering en bij een mislukte generatie, afzonderlijk uit te zetten (Account). Versturen via APNs: zet `APNS_KEY_ID`, `APNS_TEAM_ID`,
  `APNS_AUTH_KEY` (inhoud van het .p8-bestand), `APNS_BUNDLE_ID` en eventueel `APNS_USE_SANDBOX=1` op de worker. De iOS-app heeft de Push Notifications-capability nodig (Apple Developer).
- **Beheer:** podcasts bewerken, pauzeren, hervatten en verwijderen (met bevestiging). Wijzigingen gelden voor toekomstige afleveringen.
- **API-sleutels** (Anthropic, ElevenLabs) staan centraal op de server; gebruikers voeren er geen in. Er zijn geen kostenschermen in de app.

Schermen: Aanmelden · Mijn podcasts · Podcast aanmaken/bewerken · Omslag kiezen · Stem kiezen · Podcastdetail · Afleveringsdetail · Account en meldingen.

## Tests en productie

```bash
python -m tests.test_api        # API: podcasts, tenant-isolatie, planning, bronnen, omslag, stemmen, meldingen, worker
python -m tests.test_discover   # nieuws zoeken, stijlen, nieuwsperiode
python -m tests.test_round1     # pijplijn (selectie, scores, tijdverdeling)
```

Productie: zet `API_JWT_SECRET` (minstens 32 tekens), `APPLE_CLIENT_ID`, `PUBLIC_BASE_URL` (https), `ELEVENLABS_API_KEY` (API: stemmenlijst) en laat `AUTH_DEV_MODE` weg; zonder geheim start de API niet.
`WORKER_INLINE` staat standaard uit; draai `python -m worker.run loop` als aparte worker (die zet ook de geplande afleveringen klaar).
Zonder eigen worker kan `python -m worker.run enqueue-due` elke 15 minuten draaien (zie `.github/workflows/enqueue.yml`) naast `python -m worker.run once`.
