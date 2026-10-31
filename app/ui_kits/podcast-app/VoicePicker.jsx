import React, { useEffect, useRef, useState } from "react";
import { Button } from "../../components/core/Button.jsx";
import { Card } from "../../components/core/Card.jsx";
import { IconButton } from "../../components/core/IconButton.jsx";
import { ListRow } from "../../components/core/ListRow.jsx";
import { TextField } from "../../components/forms/TextField.jsx";
import { TopAppBar } from "../../components/navigation/TopAppBar.jsx";
import { Icon } from "../../components/core/Icon.jsx";
import { api } from "./api.js";
import { FieldError, Muted, Page } from "./ui.jsx";

/** Scherm 5 · Stem kiezen: de stemmen van ElevenLabs met zoeken en een kort luistervoorbeeld. Annuleren behoudt de vorige keuze. */
export function VoicePicker({ value, onConfirm, onCancel }) {
  const [voices, setVoices] = useState(null);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");
  const [picked, setPicked] = useState(value);
  const [playing, setPlaying] = useState("");
  const audio = useRef(null);

  useEffect(() => {
    api.voices().then(setVoices).catch((e) => { setVoices([]); setError(e.message); });
    return () => { if (audio.current) audio.current.pause(); };
  }, []);

  const play = (v) => {
    if (audio.current) audio.current.pause();
    if (playing === v.voice_id) { setPlaying(""); return; }
    const a = new Audio(v.preview_url);
    a.onended = () => setPlaying("");
    a.play().catch(() => setPlaying(""));
    audio.current = a;
    setPlaying(v.voice_id);
  };

  const shown = (voices || []).filter((v) => !q.trim() || `${v.name} ${v.description}`.toLowerCase().includes(q.trim().toLowerCase()));

  return (
    <>
      <TopAppBar title="Stem kiezen" onBack={onCancel} />
      <Page>
        <TextField placeholder="Zoek op naam" icon="search" value={q} onChange={setQ} />
        {voices === null && <Muted>Stemmen laden…</Muted>}
        {error && <FieldError>{error} Je huidige keuze ({value.name || "standaardstem"}) blijft behouden.</FieldError>}
        {shown.length > 0 && (
          <Card padding={0}>
            {shown.map((v, i) => (
              <ListRow key={v.voice_id} label={v.name} description={v.description || undefined} divider={i > 0}
                chevron={false} onClick={() => setPicked({ voice_id: v.voice_id, name: v.name })}
                icon={picked.voice_id === v.voice_id ? "check" : undefined}
                trailing={v.preview_url ? <IconButton icon={playing === v.voice_id ? "close" : "play"} label={`Luister naar ${v.name}`} onClick={(e) => { e.stopPropagation(); play(v); }} /> : null} />
            ))}
          </Card>
        )}
        {voices && voices.length > 0 && shown.length === 0 && <Muted>Geen stem gevonden voor “{q}”.</Muted>}
        <Button fullWidth onClick={() => onConfirm(picked)}>Bevestigen</Button>
        <Button fullWidth variant="tertiary" onClick={onCancel}>Annuleren</Button>
      </Page>
    </>
  );
}
