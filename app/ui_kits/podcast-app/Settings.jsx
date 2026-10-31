import React, { useState } from "react";
import { TopAppBar } from "../../components/navigation/TopAppBar.jsx";
import { TextField } from "../../components/forms/TextField.jsx";
import { Button } from "../../components/core/Button.jsx";
import { ListRow } from "../../components/core/ListRow.jsx";
import { Card, SectionTitle } from "../../components/core/Card.jsx";
import { Chip } from "../../components/core/Chip.jsx";
import { Switch } from "../../components/core/Switch.jsx";
import { DAYS, DEFAULT_SCHEDULE, deviceTimezone } from "./schedule.js";

export function Settings({ show, onBack, onSave, onPronounce }) {
  const [title, setTitle] = useState(show.title);
  const [description, setDescription] = useState(show.description || "");
  const [maxMinutes, setMaxMinutes] = useState(String(show.duration?.max_minutes ?? 15));
  const [focus, setFocus] = useState(show.relevance?.focus ?? "Nederland");
  const [repeatDays, setRepeatDays] = useState(String(show.relevance?.repeat_days ?? 7));
  const [cta, setCta] = useState(show.call_to_action || "");
  const [schedule, setSchedule] = useState({ ...DEFAULT_SCHEDULE, ...(show.schedule || {}) });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [ok, setOk] = useState(false);

  const toggleDay = (d) => setSchedule((s) => ({
    ...s, days: s.days.includes(d) ? s.days.filter((x) => x !== d) : [...s.days, d].sort(),
  }));

  const save = async () => {
    setBusy(true); setError(""); setOk(false);
    try {
      await onSave({
        title: title.trim(),
        description: description.trim(),
        call_to_action: cta.trim(),
        schedule: { ...schedule, timezone: deviceTimezone(schedule.timezone) },
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
      <div style={{ flex: 1, overflowY: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <SectionTitle>Planning</SectionTitle>
          <Card padding={16} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ font: "var(--type-body)" }}>Automatisch nieuwe aflevering</span>
                <span style={{ font: "var(--type-body-small)", color: "var(--text-secondary)" }}>
                  {schedule.enabled ? "Jij bepaalt de dagen en het tijdstip" : "Uit: je bouwt zelf met de knop Bouw"}
                </span>
              </div>
              <Switch checked={schedule.enabled} onChange={(v) => setSchedule({ ...schedule, enabled: v })} label="Automatisch nieuwe aflevering" />
            </div>
            {schedule.enabled && (
              <>
                <div>
                  <div style={{ font: "var(--type-label)", marginBottom: 8 }}>Dagen</div>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    {DAYS.map((name, d) => (
                      <Chip key={d} selected={schedule.days.includes(d)} onClick={() => toggleDay(d)} style={{ padding: "0 10px", margin: 0 }}>{name}</Chip>
                    ))}
                  </div>
                </div>
                <TextField label="Tijdstip" type="time" value={schedule.time} onChange={(v) => setSchedule({ ...schedule, time: v })}
                  helper={`Tijdzone: ${deviceTimezone(schedule.timezone)}. Start hooguit 2 uur te laat als er iets haperde.`} />
              </>
            )}
          </Card>
        </div>
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
        <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 16 }}>
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
        ) : (
          <div style={{ padding: "0 16px 16px" }}>
            <Card padding={0}>
              {Object.entries(map).map(([k, v], i) => (
                <ListRow key={k} label={k} value={v} chevron={false} divider={i > 0}
                  trailing={<Button size="sm" variant="tertiary" onClick={() => remove(k)}>Verwijder</Button>} />
              ))}
            </Card>
          </div>
        )}
      </div>
    </>
  );
}
