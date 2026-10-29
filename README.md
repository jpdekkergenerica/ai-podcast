# Dagelijkse podcast

Elke ochtend (GitHub Actions) wordt automatisch een podcast gemaakt:

1. Nieuws ophalen uit de RSS-feeds per interessegebied (`config.yaml`).
2. Claude geeft elk bericht een relevantiescore (0-10). Berichten onder `min_item_score` vallen af.
3. De beschikbare tijd (`max_minutes` min haak en synthese) wordt verdeeld over de onderwerpen, evenredig met
   hun relevantie. Heeft een onderwerp geen nieuws, dan vullen de andere onderwerpen die tijd. Alleen als er
   voor alle onderwerpen te weinig materiaal is (`max_minutes_per_item`) wordt de aflevering korter.
4. Claude schrijft een Nederlands script met een woordbudget per gebied.
5. ElevenLabs maakt er audio van per hoofdstuk; ffmpeg normaliseert naar -16 LUFS / -1 dBTP (128 kbps CBR mono)
   en ID3-hoofdstukken worden toegevoegd. De mp3 komt als GitHub Release, de feed op GitHub Pages.

## Succescriteria uit `brondata/`

Op basis van het rapport over solo-podcasts past de pijplijn dit toe:

- **Haak binnen ~45 s**, daarna een korte showintro; 2-4 inhoudelijke blokken (`max_topics`); synthese met precies
  één actieoproep (`call_to_action`) aan het eind.
- **Stijl:** consequent "je/jij", afwisselende zinslengte, pauzes van 1-2 s vóór kernpunten (`<break>`),
  levendiger stem via `voice.settings`.
- **Audio:** -16 LUFS, -1 dBTP, hoogdoorlaat 80 Hz, milde compressie, 128 kbps CBR mono, 44,1 kHz.
- **Metadata:** titel als concrete vraag zonder showtitel/datum/nummer; eerste 250 tekens van de beschrijving
  bevatten de kernantwoorden; hoofdstukken < 45 tekens; AI-vermelding en bronnen onderaan.
- **Cover:** 3000x3000 JPEG (<500 KB), hoog contrast, veilige marge. Eigen ontwerp? Zet het als `assets/cover.jpg`.
- **Ritme:** vaste publicatietijd (02:30 UTC, dus 03:30/04:30 Nederlandse tijd).

Bewust niet gedaan: luisterersvragen via SpeakPipe (vraagt een menselijke tussenstap), audiograms/nieuwsbrief en
getimede transcripties. Dit is het eerste wat je kunt toevoegen als de podcast publiek gaat.

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
