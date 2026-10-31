import React, { useEffect, useState } from "react";
import { Button } from "../../components/core/Button.jsx";
import { Chip } from "../../components/core/Chip.jsx";
import { IconButton } from "../../components/core/IconButton.jsx";
import { ListRow } from "../../components/core/ListRow.jsx";
import { Card } from "../../components/core/Card.jsx";
import { Dialog } from "../../components/overlays/Dialog.jsx";
import { TextField } from "../../components/forms/TextField.jsx";
import { TopAppBar } from "../../components/navigation/TopAppBar.jsx";
import { api } from "./api.js";
import { CoverPicker } from "./CoverPicker.jsx";
import { VoicePicker } from "./VoicePicker.jsx";
import { DAYS, DAY_NAMES, DEFAULT_SCHEDULE, PRESETS, applyPreset, deviceTimezone, presetOf } from "./schedule.js";
import { Cover, FieldError, Group, Muted, Page } from "./ui.jsx";

const DURATIONS = [5, 10, 15, 20];
const STYLES = [
  { id: "zakelijk", label: "Zakelijk", hint: "Helder, feitelijk en beknopt" },
  { id: "informeel", label: "Informeel", hint: "Warm en rechtstreeks, alsof je een vriend bijpraat" },
  { id: "verhalend", label: "Verhalend", hint: "Het nieuws als verhaal met een lijn" },
];
const DEFAULT_VOICE = { voice_id: "dLPO5AsXc3FZDbTh1IKa", name: "Standaardstem" };
const MAX_TOPICS = 12;

/** Eerstvolgende publicatie volgens deze planning, in de tijd van dit toestel (de server rekent de echte datum uit). */
function nextText(s) {
  if (s.every_days) return `Daarna elke ${s.every_days} dagen om ${s.time}`;
  const [hh, mm] = s.time.split(":").map(Number);
  const now = new Date();
  for (let i = 0; i < 8; i += 1) {
    const d = new Date(now.getFullYear(), now.getMonth(), now.getDate() + i, hh, mm);
    if (d > now && s.days.includes((d.getDay() + 6) % 7)) {
      return `Daarna: ${DAYS[(d.getDay() + 6) % 7].toLowerCase()} ${d.getDate()}-${d.getMonth() + 1} om ${s.time}`;
    }
  }
  return "";
}

/** Scherm 3 · Podcast aanmaken en bewerken: vier groepen (basis, inhoud, presentatie, planning). */
export function PodcastForm({ id, nav }) {
  const editing = !!id;
  const [loaded, setLoaded] = useState(!editing);
  const [view, setView] = useState("form"); // form | voice | cover
  const [title, setTitle] = useState("");
  const [topics, setTopics] = useState([""]);
  const [sources, setSources] = useState([]); // {url, name, kind, error}
  const [sourceDraft, setSourceDraft] = useState("");
  const [sourceBusy, setSourceBusy] = useState(false);
  const [duration, setDuration] = useState(10);
  const [voice, setVoice] = useState(DEFAULT_VOICE);
  const [style, setStyle] = useState("informeel");
  const [schedule, setSchedule] = useState({ ...DEFAULT_SCHEDULE, timezone: deviceTimezone() });
  const [cover, setCover] = useState({ mode: "keep", dataUrl: null, url: null, custom: false });
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  useEffect(() => {
    if (!editing) return;
    api.podcast(id).then((p) => {
      setTitle(p.title);
      setTopics(p.topics.map((t) => t.text).concat(p.topics.length ? [] : [""]));
      setSources(p.sources);
      setDuration(p.duration_minutes);
      setVoice(p.voice.voice_id ? p.voice : DEFAULT_VOICE);
      setStyle(p.style);
      setSchedule({ ...DEFAULT_SCHEDULE, ...p.schedule });
      setCover({ mode: "keep", dataUrl: null, url: p.cover_url, custom: p.has_custom_cover });
      setLoaded(true);
    }).catch((e) => { setErrors({ form: e.message }); setLoaded(true); });
  }, [id]);

  if (view === "voice") return <VoicePicker value={voice} onConfirm={(v) => { setVoice(v); setView("form"); }} onCancel={() => setView("form")} />;
  if (view === "cover") {
    const shown = cover.mode === "new" ? cover.dataUrl : cover.mode === "remove" ? null : cover.url;
    return (
      <CoverPicker current={shown || cover.url || "../../assets/logo.png"} hasCustom={cover.mode === "new" || (cover.mode === "keep" && cover.custom)}
        onBack={() => setView("form")}
        onUse={async (dataUrl) => { setCover({ ...cover, mode: "new", dataUrl }); setView("form"); }}
        onRemove={async () => { setCover({ ...cover, mode: "remove", dataUrl: null, custom: false }); setView("form"); }} />
    );
  }

  const setTopic = (i, v) => setTopics(topics.map((t, j) => (j === i ? v : t)));
  const sched = (patch) => setSchedule({ ...schedule, ...patch });
  const preset = presetOf(schedule);

  const addSource = async () => {
    const url = sourceDraft.trim();
    if (!url) return;
    if (sources.some((s) => s.url === url)) { setSourceDraft(""); return; }
    setSourceBusy(true);
    try {
      const info = await api.checkSource(url);
      setSources([...sources, { url: info.error ? url : info.url, name: info.name, kind: info.kind, error: info.error }]);
      setSourceDraft("");
    } catch (e) {
      setSources([...sources, { url, name: "", kind: "website", error: e.message }]);
      setSourceDraft("");
    } finally { setSourceBusy(false); }
  };

  const submit = async () => {
    const clean = topics.map((t) => t.trim()).filter(Boolean);
    const local = {};
    if (!title.trim()) local.title = "Geef je podcast een naam";
    if (!clean.length) local.topics = "Voeg minstens één onderwerp toe";
    if (Object.keys(local).length) { setErrors(local); return; }
    setBusy(true); setErrors({});
    const body = {
      title: title.trim(), topics: clean, sources: sources.map((s) => s.url), duration_minutes: duration,
      voice_id: voice.voice_id, voice_name: voice.name, style,
      schedule: { ...schedule, timezone: deviceTimezone(schedule.timezone), enabled: true },
    };
    try {
      const saved = editing ? await api.updatePodcast(id, body) : await api.createPodcast(body);
      let coverError = "";
      try {
        if (cover.mode === "new") await api.setCover(saved.id, cover.dataUrl);
        else if (cover.mode === "remove" && editing) await api.deleteCover(saved.id);
      } catch (e) { coverError = e.message; } // een mislukte omslag blokkeert de podcast niet
      nav.done(saved, coverError ? `Podcast opgeslagen, maar de omslag lukte niet: ${coverError}` : "");
    } catch (e) {
      // ingevulde gegevens blijven staan; fouten komen bij het betreffende veld
      setErrors(e.fields || { form: e.message });
      setBusy(false);
    }
  };

  const remove = async () => {
    setBusy(true);
    try { await api.deletePodcast(id); nav.done(null, "Podcast verwijderd", "ok"); }
    catch (e) { setErrors({ form: e.message }); setBusy(false); setConfirmDelete(false); }
  };

  if (!loaded) return (<><TopAppBar title="Podcast" onBack={nav.pop} /><Page><Muted>Laden…</Muted></Page></>);

  const e = errors;
  return (
    <>
      <TopAppBar title={editing ? "Podcast bewerken" : "Nieuwe podcast"} onBack={nav.pop} />
      <Page>
        <Group title="Basisgegevens">
          <TextField label="Naam" value={title} onChange={setTitle} placeholder="Bijvoorbeeld: Mijn technieuws" error={e.title} />
          <ListRow label="Omslag" description="Optioneel. Zonder eigen afbeelding gebruiken we een standaardomslag."
            style={{ padding: 0, border: "none" }} onClick={() => setView("cover")}
            icon={undefined}
            trailing={<Cover url={cover.mode === "new" ? cover.dataUrl : cover.mode === "remove" ? "../../assets/logo.png" : cover.url || "../../assets/logo.png"} size={48} radius={8} />} chevron={false} />
        </Group>

        <Group title="Onderwerpen en bronnen">
          {topics.map((t, i) => (
            <TextField key={i} label={`Onderwerp ${i + 1}`} value={t} onChange={(v) => setTopic(i, v)}
              placeholder="Bijvoorbeeld: nieuwe ontwikkelingen in AI-regelgeving"
              error={i === 0 ? e.topics : ""}
              trailing={topics.length > 1 ? <IconButton icon="trash" label={`Onderwerp ${i + 1} verwijderen`} size={32} onClick={() => setTopics(topics.filter((_, j) => j !== i))} /> : null} />
          ))}
          {topics.length < MAX_TOPICS && <Button variant="secondary" icon="plus" onClick={() => setTopics([...topics, ""])}>Onderwerp toevoegen</Button>}
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <span style={{ font: "var(--type-label)" }}>Eigen bronnen <Muted>(optioneel)</Muted></span>
            {sources.map((s) => (
              <div key={s.url} style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 12px", border: "var(--border-1) solid var(--border-default)", borderRadius: "var(--radius-input)" }}>
                <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
                  <span style={{ font: "var(--type-body-small)", fontWeight: 500 }}>{s.name || s.url}</span>
                  <Muted style={{ overflowWrap: "anywhere" }}>{s.url}</Muted>
                  {s.error && <FieldError>{s.error}</FieldError>}
                </div>
                <IconButton icon="close" label="Bron verwijderen" size={32} onClick={() => setSources(sources.filter((x) => x.url !== s.url))} />
              </div>
            ))}
            <TextField placeholder="https://… (website of RSS)" value={sourceDraft} onChange={setSourceDraft} type="url" inputMode="url" error={e.sources} />
            <Button variant="secondary" loading={sourceBusy} onClick={addSource}>Bron toevoegen</Button>
            <Muted>De app zoekt zelf ook betrouwbare bronnen en combineert die met jouw bronnen.</Muted>
          </div>
        </Group>

        <Group title="Duur, stem en vertelstijl">
          <div>
            <div style={{ font: "var(--type-label)", marginBottom: 8 }}>Duur</div>
            <div style={{ display: "flex", gap: 8 }}>
              {DURATIONS.map((m) => <Chip key={m} selected={duration === m} onClick={() => setDuration(m)} style={{ flex: 1, justifyContent: "center", margin: 0 }}>{m} min</Chip>)}
            </div>
            <FieldError>{e.duration_minutes}</FieldError>
          </div>
          <ListRow label="Stem" value={voice.name || "Kies een stem"} style={{ padding: 0, border: "none", minHeight: 40 }} onClick={() => setView("voice")} />
          <FieldError>{e.voice}</FieldError>
          <div>
            <div style={{ font: "var(--type-label)", marginBottom: 8 }}>Vertelstijl</div>
            <div style={{ display: "flex", gap: 8 }}>
              {STYLES.map((s) => <Chip key={s.id} selected={style === s.id} onClick={() => setStyle(s.id)} style={{ flex: 1, justifyContent: "center", margin: 0, padding: "0 8px" }}>{s.label}</Chip>)}
            </div>
            <Muted style={{ display: "block", marginTop: 8 }}>{STYLES.find((s) => s.id === style)?.hint}</Muted>
            <FieldError>{e.style}</FieldError>
          </div>
        </Group>

        <Group title="Planning">
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {PRESETS.map((p) => (
              <Chip key={p.id} selected={preset === p.id} style={{ margin: 0 }}
                onClick={() => setSchedule(applyPreset(schedule, p.id))}>{p.label}</Chip>
            ))}
          </div>
          {preset === "weekly" && (
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {DAYS.map((d, i) => <Chip key={d} selected={schedule.days[0] === i} style={{ margin: 0, padding: "0 10px" }} onClick={() => setSchedule(applyPreset(schedule, "weekly", { day: i }))}>{d}</Chip>)}
            </div>
          )}
          {preset === "every" && (
            <TextField label="Aantal dagen tussen afleveringen" value={String(schedule.every_days ?? 2)} inputMode="numeric"
              onChange={(v) => sched({ every_days: Math.max(2, Math.min(30, parseInt(v, 10) || 2)) })} helper="Tussen 2 en 30 dagen" />
          )}
          <TextField label="Tijdstip waarop de aflevering klaarstaat" type="time" value={schedule.time} onChange={(v) => sched({ time: v })}
            helper={`Tijdzone: ${deviceTimezone(schedule.timezone)}. De voorbereiding begint iets eerder.`} />
          <Muted>{nextText(schedule)}</Muted>
          <FieldError>{e.schedule}</FieldError>
        </Group>

        <FieldError>{e.form}</FieldError>
        {!editing && <Muted>Na het aanmaken maken we direct de eerste aflevering. Je hoeft niets te starten.</Muted>}
        {editing && <Muted>Wijzigingen gelden voor nieuwe afleveringen en starten zelf geen extra aflevering.</Muted>}
        <Button fullWidth size="lg" loading={busy} onClick={submit}>{editing ? "Wijzigingen opslaan" : "Podcast aanmaken"}</Button>
        {editing && <Button fullWidth variant="destructive" disabled={busy} onClick={() => setConfirmDelete(true)}>Podcast verwijderen</Button>}
      </Page>
      <Dialog open={confirmDelete} loading={busy} destructive title={`“${title}” verwijderen?`} confirmLabel="Verwijderen" cancelLabel="Annuleren"
        onCancel={() => setConfirmDelete(false)} onConfirm={remove}>
        De podcast, alle afleveringen en de feed verdwijnen. Dit kun je niet terugdraaien.
      </Dialog>
    </>
  );
}
