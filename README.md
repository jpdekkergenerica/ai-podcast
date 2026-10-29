# Dagelijkse podcast

Elke ochtend (GitHub Actions) wordt automatisch een podcast gemaakt:

1. Nieuws ophalen uit de RSS-feeds per interessegebied (`config.yaml`).
2. Claude geeft elk bericht een relevantiescore (0-10). Berichten onder `min_item_score` vallen af.
3. De tijd wordt gevuld tot `max_minutes` (min haak en synthese) met de meest impactvolle berichten, over alle
   onderwerpen heen. Een bericht krijgt meer tijd naarmate het impactvoller is (`item_minutes_floor` tot
   `item_minutes_top`); de tijd van een onderwerp is de som van zijn berichten. Veel of belangrijk nieuws
   geeft dus meer tijd, een onderwerp zonder nieuws geeft zijn tijd vanzelf af. Elk onderwerp met een bericht
   van `coverage_min_score` of hoger komt altijd aan bod, en extra berichten van hetzelfde onderwerp tellen
   steeds iets minder zwaar (`topic_decay`), zodat één groot onderwerp de rest niet verdringt. Dubbele berichten tussen
   onderwerpen worden eruit gehaald. Is er te weinig nieuws, dan worden de berichten hooguit `max_stretch` keer
   uitgebreider behandeld en blijft de aflevering daarna korter.
   **Geen herhaling:** een onderwerp mag elke dag terugkomen, maar hetzelfde nieuws niet. `covered.json` onthoudt
   wat de laatste dagen is besproken; een Claude-controle schrapt kandidaten die over dezelfde gebeurtenis gaan
   als een ander bericht (ook van een andere bron) of als iets dat al is besproken, tenzij er nieuwe feiten zijn.
   Nederlandse focus: berichten zonder duidelijke link met Nederland krijgen een lage score (`relevance.focus`).
4. Claude schrijft een Nederlands script met een woordbudget per gebied.
   **Uitspraak:** een aparte stap zoekt in elk script de afkortingen, buitenlandse namen en symbolen die een
   Nederlandse stem fout leest, en schrijft ze zoals ze gezegd worden (ASML -> aa-es-em-el). Wat de app leert staat in
   `pronunciation.json`, zodat een term elke dag hetzelfde klinkt. Blijft de stem iets fout doen? Zet het in
   `config.yaml` onder `pronunciation`; dat wint altijd. Titels en beschrijvingen blijven gewoon geschreven.
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
