import React, { useState } from "react";
import { TopAppBar } from "../../components/navigation/TopAppBar.jsx";
import { TextField } from "../../components/forms/TextField.jsx";
import { Button } from "../../components/core/Button.jsx";
import { ListRow } from "../../components/core/ListRow.jsx";

export function Settings({ show, onBack, onSave, onPronounce }) {
  const [title, setTitle] = useState(show.title);
  const [description, setDescription] = useState(show.description || "");
  const [maxMinutes, setMaxMinutes] = useState(String(show.duration?.max_minutes ?? 15));
  const [focus, setFocus] = useState(show.relevance?.focus ?? "Nederland");
  const [repeatDays, setRepeatDays] = useState(String(show.relevance?.repeat_days ?? 7));
  const [cta, setCta] = useState(show.call_to_action || "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [ok, setOk] = useState(false);

  const save = async () => {
    setBusy(true); setError(""); setOk(false);
    try {
      await onSave({
        title: title.trim(),
        description: description.trim(),
        call_to_action: cta.trim(),
        duration: { ...(show.duration || {}), max_minutes: parseFloat(maxMinutes) || 15 },
        relevance: {
          ...(show.relevance || {}),
          focus: focus.trim() || "Nederland",
          repeat_days: parseInt(repeatDays, 10) || 0,
        },
      });
      setOk(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <TopAppBar title="Aflevering" onBack={onBack} />
      <div style={{ flex: 1, overflowY: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 12 }}>
        <TextField label="Titel" value={title} onChange={setTitle} />
        <TextField label="Beschrijving" value={description} onChange={setDescription} />
        <TextField label="Max. minuten" value={maxMinutes} onChange={setMaxMinutes} inputMode="decimal" />
        <TextField label="Regionale focus" value={focus} onChange={setFocus}
          helper="Nieuws zonder link met deze regio scoort lager" />
        <TextField label="Geen herhaling (dagen)" value={repeatDays} onChange={setRepeatDays} inputMode="numeric"
          helper="0 = herhalingscontrole uit" />
        <TextField label="Actieoproep" value={cta} onChange={setCta}
          helper="Precies één concrete zin aan het eind van de aflevering" />
        {error && <span style={{ font: "var(--type-body-small)", color: "var(--negative-text)" }}>{error}</span>}
        {ok && <span style={{ font: "var(--type-body-small)", color: "var(--positive-text)" }}>Opgeslagen</span>}
        <Button fullWidth loading={busy} onClick={save}>Opslaan</Button>
        {onPronounce && (
          <Button fullWidth variant="secondary" onClick={onPronounce}>Uitspraak beheren</Button>
        )}
      </div>
    </>
  );
}

export function Pronounce({ show, onBack, onSave }) {
  const [term, setTerm] = useState("");
  const [spoken, setSpoken] = useState("");
  const [map, setMap] = useState(() => ({ ...(show.pronunciation || {}) }));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const add = async () => {
    if (!term.trim() || !spoken.trim()) { setError("Vul term en uitspraak in"); return; }
    const next = { ...map, [term.trim()]: spoken.trim() };
    setBusy(true); setError("");
    try {
      await onSave({ pronunciation: next });
      setMap(next);
      setTerm(""); setSpoken("");
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async (key) => {
    const next = { ...map };
    delete next[key];
    setBusy(true);
    try {
      await onSave({ pronunciation: next });
      setMap(next);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <TopAppBar title="Uitspraak" onBack={onBack} />
      <div style={{ flex: 1, overflowY: "auto" }}>
        <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 12 }}>
          <p style={{ margin: 0, font: "var(--type-body-small)", color: "var(--text-secondary)" }}>
            Vaste uitspraken winnen altijd van wat de app zelf leert. Term is hoofdlettergevoelig.
          </p>
          <TextField label="Term" value={term} onChange={setTerm} placeholder="ASML" />
          <TextField label="Zo gezegd" value={spoken} onChange={setSpoken} placeholder="aa-es-em-el" />
          {error && <span style={{ font: "var(--type-body-small)", color: "var(--negative-text)" }}>{error}</span>}
          <Button fullWidth loading={busy} onClick={add}>Toevoegen</Button>
        </div>
        {Object.keys(map).length === 0 ? (
          <div style={{ padding: 16, font: "var(--type-body-small)", color: "var(--text-tertiary)" }}>Nog geen vaste termen</div>
        ) : Object.entries(map).map(([k, v], i) => (
          <ListRow key={k} label={k} value={v} chevron={false} divider={i > 0}
            trailing={<Button size="sm" variant="tertiary" onClick={() => remove(k)}>Verwijder</Button>} />
        ))}
      </div>
    </>
  );
}
