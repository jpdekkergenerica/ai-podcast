import React, { useEffect, useState } from "react";
import { Button } from "../../components/core/Button.jsx";
import { Card } from "../../components/core/Card.jsx";
import { EmptyState } from "../../components/feedback/EmptyState.jsx";
import { BrandHeader } from "../../components/navigation/BrandHeader.jsx";
import { api } from "./api.js";
import { scheduleLabel } from "./schedule.js";
import { Cover, Muted, Page, StatusPill } from "./ui.jsx";

/** Scherm 2 · Mijn podcasts: omslag, naam, duur, schema, volgende publicatie en status per podcast. */
export function PodcastList({ nav }) {
  const [podcasts, setPodcasts] = useState(null);
  const [error, setError] = useState("");

  const load = async () => {
    try { setPodcasts(await api.podcasts()); setError(""); } catch (e) { setError(e.message); }
  };
  useEffect(() => { load(); }, []);
  // zolang er een aflevering wordt gemaakt, ververst de lijst zichzelf
  useEffect(() => {
    if (!podcasts?.some((p) => p.status.code === "running")) return undefined;
    const id = setInterval(load, 8000);
    return () => clearInterval(id);
  }, [podcasts]);

  const add = () => nav.push({ name: "form" });

  return (
    <>
      <BrandHeader />
      <Page>
        {error && <Card padding={16}><Muted style={{ color: "var(--negative-text)" }}>{error}</Muted></Card>}
        {podcasts && podcasts.length === 0 && !error && (
          <EmptyState compact title="Nog geen podcasts" action="Podcast toevoegen" onAction={add}>
            Kies je onderwerpen en wij maken en publiceren de afleveringen. Luisteren doe je in Apple Podcasts.
          </EmptyState>
        )}
        {podcasts?.map((p) => (
          <button key={p.id} type="button" onClick={() => nav.push({ name: "detail", id: p.id })}
            style={{ all: "unset", cursor: "pointer", display: "block", WebkitTapHighlightColor: "transparent" }}>
            <Card padding={12} style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <Cover url={p.cover_url} size={64} />
              <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: 4 }}>
                <span style={{ font: "var(--type-headline)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.title}</span>
                <Muted>{p.duration_minutes} min · {scheduleLabel(p.schedule)}</Muted>
                <Muted>{p.next_run ? `Volgende: ${p.next_run.local}` : p.paused ? "Gepauzeerd" : ""}</Muted>
                <div><StatusPill status={p.status} /></div>
              </div>
            </Card>
          </button>
        ))}
        {podcasts && podcasts.length > 0 && <Button fullWidth icon="plus" onClick={add}>Podcast toevoegen</Button>}
      </Page>
    </>
  );
}
