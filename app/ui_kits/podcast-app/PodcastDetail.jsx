import React, { useEffect, useState } from "react";
import { Button } from "../../components/core/Button.jsx";
import { Card } from "../../components/core/Card.jsx";
import { ListRow } from "../../components/core/ListRow.jsx";
import { Dialog } from "../../components/overlays/Dialog.jsx";
import { TopAppBar } from "../../components/navigation/TopAppBar.jsx";
import { api } from "./api.js";
import { dateText, minutesText, scheduleLabel } from "./schedule.js";
import { Cover, FieldError, Group, Muted, Page, StatusPill } from "./ui.jsx";

const STYLE_LABEL = { zakelijk: "Zakelijk", informeel: "Informeel", verhalend: "Verhalend" };

/** Scherm 6 · Podcastdetail: status, volgende publicatie, persoonlijke feedlink, instellingen en afleveringen. */
export function PodcastDetail({ id, nav }) {
  const [p, setP] = useState(null);
  const [episodes, setEpisodes] = useState([]);
  const [error, setError] = useState("");
  const [confirm, setConfirm] = useState(null); // delete | rotate
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      const [pod, eps] = await Promise.all([api.podcast(id), api.episodes(id)]);
      setP(pod); setEpisodes(eps); setError("");
    } catch (e) { setError(e.message); }
  };
  useEffect(() => { load(); }, [id]);
  useEffect(() => {
    if (p?.status.code !== "running") return undefined;
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, [p?.status.code]);

  const copy = async () => {
    try { await navigator.clipboard.writeText(p.feed_url); nav.toast("Feedlink gekopieerd", "check"); } catch { nav.toast(p.feed_url); }
  };
  const act = async (fn, after) => {
    setBusy(true);
    try { const res = await fn(); if (after) after(res); else setP(res); } catch (e) { nav.toast(e.message, "alert", "error"); }
    finally { setBusy(false); setConfirm(null); }
  };

  if (!p) return (<><TopAppBar title="Podcast" onBack={nav.pop} /><Page>{error ? <FieldError>{error}</FieldError> : <Muted>Laden…</Muted>}</Page></>);

  return (
    <>
      <TopAppBar title={p.title} onBack={nav.pop} actions={<Button size="sm" variant="tertiary" onClick={() => nav.push({ name: "form", id })}>Bewerken</Button>} />
      <Page style={{ paddingBottom: 32 }}>
        <Card padding={16} style={{ display: "flex", gap: 16 }}>
          <Cover url={p.cover_url} size={88} radius={12} />
          <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: 6 }}>
            <div><StatusPill status={p.status} /></div>
            <Muted>{p.status.detail}</Muted>
            {p.next_run && <span style={{ font: "var(--type-body-small)" }}>Volgende aflevering: <b style={{ fontWeight: 500 }}>{p.next_run.local}</b> <Muted>({p.next_run.timezone})</Muted></span>}
          </div>
        </Card>

        <Group title="Persoonlijke feed">
          <Button fullWidth icon="copy" onClick={copy}>Kopieer feedlink</Button>
          <Muted>
            Zo luister je: open Apple Podcasts → Bibliotheek → menu (…) → “Volg een programma via URL” en plak de link.
            Nieuwe afleveringen verschijnen daarna vanzelf.
          </Muted>
          <Muted style={{ color: "var(--warning-text)" }}>Deel deze link met niemand: wie hem heeft, kan je afleveringen beluisteren.</Muted>
          <Button variant="tertiary" onClick={() => setConfirm("rotate")}>Nieuwe feedlink maken</Button>
        </Group>

        <div>
          <Muted style={{ display: "block", padding: "0 4px 8px", fontWeight: 500 }}>Instellingen</Muted>
          <Card padding={0}>
            <ListRow label="Onderwerpen" description={p.topics.map((t) => t.text).join(" · ")} chevron={false} divider={false} />
            <ListRow label="Duur" value={`${p.duration_minutes} min`} chevron={false} />
            <ListRow label="Stem" value={p.voice.name || "Standaardstem"} chevron={false} />
            <ListRow label="Vertelstijl" value={STYLE_LABEL[p.style] || p.style} chevron={false} />
            <ListRow label="Planning" value={scheduleLabel(p.schedule)} chevron={false} />
            <ListRow label="Eigen bronnen" value={p.sources.length ? String(p.sources.length) : "Geen"} chevron={false} />
          </Card>
        </div>

        <div>
          <Muted style={{ display: "block", padding: "0 4px 8px", fontWeight: 500 }}>Afleveringen</Muted>
          {episodes.length === 0 ? (
            <Card padding={16}><Muted>{p.status.code === "running" ? "De eerste aflevering wordt gemaakt. Dit duurt even." : "Er is nog geen aflevering gepubliceerd."}</Muted></Card>
          ) : (
            <Card padding={0}>
              {episodes.map((e, i) => (
                <ListRow key={e.guid} label={e.title} description={`${dateText(e.published || e.date)} · ${minutesText(e.duration)}`}
                  divider={i > 0} onClick={() => nav.push({ name: "episode", id, guid: e.guid })} />
              ))}
            </Card>
          )}
        </div>

        <Card padding={0}>
          {p.paused
            ? <ListRow icon="play" label="Hervatten" description="Er worden weer afleveringen gepland" divider={false} chevron={false} onClick={() => act(() => api.resumePodcast(id))} />
            : <ListRow icon="minus" label="Pauzeren" description="Tijdelijk geen nieuwe afleveringen" divider={false} chevron={false} onClick={() => act(() => api.pausePodcast(id))} />}
          <ListRow icon="trash" label="Podcast verwijderen" danger chevron={false} onClick={() => setConfirm("delete")} />
        </Card>
        <Muted>Bestaande afleveringen blijven bewaard totdat je de podcast verwijdert.</Muted>
      </Page>

      <Dialog open={!!confirm} loading={busy}
        title={confirm === "delete" ? `“${p.title}” verwijderen?` : "Nieuwe feedlink maken?"}
        destructive={confirm === "delete"} confirmLabel={confirm === "delete" ? "Verwijderen" : "Nieuwe link"} cancelLabel="Annuleren"
        onCancel={() => setConfirm(null)}
        onConfirm={() => confirm === "delete" ? act(() => api.deletePodcast(id), () => nav.done(null, "Podcast verwijderd")) : act(() => api.rotateFeedToken(id))}>
        {confirm === "delete"
          ? "De podcast, alle afleveringen en de feed verdwijnen. Dit kun je niet terugdraaien."
          : "De oude link stopt direct met werken. Voeg de nieuwe link opnieuw toe in Apple Podcasts."}
      </Dialog>
    </>
  );
}
