# Dagelijkse podcast

Elke ochtend (GitHub Actions) wordt automatisch een podcast gemaakt:

1. Nieuws ophalen uit de RSS-feeds per interessegebied (`config.yaml`).
2. Claude geeft elk bericht een relevantiescore (0-10). Berichten onder `min_item_score` vallen af.
3. Spreektijd per gebied = som van de scores x `minutes_per_point`. Komt het totaal boven `max_minutes`,
   dan wordt alles evenredig ingekort. Een rustige dag geeft dus een kortere aflevering.
4. Claude schrijft een Nederlands script met een woordbudget per gebied.
5. ElevenLabs maakt er audio van; de mp3 komt als GitHub Release, de feed op GitHub Pages.

## Eenmalige setup

1. Maak een **publieke** GitHub-repo en push deze map (Pages is gratis voor publieke repo's).
2. Repo > Settings > Secrets and variables > Actions: voeg `ANTHROPIC_API_KEY` en `ELEVENLABS_API_KEY` toe.
3. Repo > Settings > Pages > Source: **GitHub Actions**.
4. Pas `config.yaml` aan (titel, e-mailadres, `voice_id`, interessegebieden, duur).
5. Actions > "Dagelijkse podcast" > **Run workflow** voor de eerste aflevering.

## In Apple Podcasts

- Direct voor jezelf: Apple Podcasts > Archief > Archief-menu / Bestand > **Volg een programma via URL** en plak
  `https://<gebruiker>.github.io/<repo>/feed.xml`. Dit werkt ook op iPhone (Zoeken > plak de URL).
- Publiek in de Apple-catalogus: aanmelden via [Apple Podcasts Connect](https://podcastsconnect.apple.com) met dezelfde feed-URL.

## Lokaal testen

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
.venv/bin/python -m podcast build --no-tts   # alleen script, geen ElevenLabs-kosten
```

## Kosten (indicatie voor 15 min per dag)

Een aflevering is ca. 14.000 tekens. Dat is ca. 420.000 tekens per maand bij `eleven_multilingual_v2`;
kies een ElevenLabs-abonnement dat dat dekt, of zet `model_id` op `eleven_flash_v2_5` (ongeveer de helft).
De Claude-kosten zijn enkele cent per dag.
