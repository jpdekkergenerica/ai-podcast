import React, { useEffect, useState } from "react";
import { Button } from "../../components/core/Button.jsx";
import { Card } from "../../components/core/Card.jsx";
import { TopAppBar } from "../../components/navigation/TopAppBar.jsx";
import { api } from "./api.js";
import { dateText, minutesText } from "./schedule.js";
import { FieldError, Muted, Page } from "./ui.jsx";

/** Scherm 7 · Afleveringsdetail: samenvatting, behandelde periode en de gebruikte bronnen per onderwerp. */
export function EpisodeDetail({ id, guid, nav }) {
  const [ep, setEp] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api.episode(id, guid).then(setEp).catch((e) => setError(e.message)); }, [id, guid]);

  if (!ep) return (<><TopAppBar title="Aflevering" onBack={nav.pop} /><Page>{error ? <FieldError>{error}</FieldError> : <Muted>Laden…</Muted>}</Page></>);

  return (
    <>
      <TopAppBar title="Aflevering" onBack={nav.pop} />
      <Page>
        <div>
          <h1 style={{ margin: 0, font: "var(--type-display-s)", letterSpacing: "var(--ls-display-s)", textWrap: "balance" }}>{ep.title}</h1>
          <Muted style={{ display: "block", marginTop: 6 }}>{dateText(ep.published || ep.date)} · {minutesText(ep.duration)}</Muted>
        </div>
        {ep.summary && <Card padding={16}><span style={{ font: "var(--type-body)", textWrap: "pretty" }}>{ep.summary}</span></Card>}
        {ep.period_start && (
          <Muted>Behandelde nieuwsperiode: {dateText(ep.period_start)} t/m {dateText(ep.period_end || ep.published)}</Muted>
        )}
        {ep.sources.map((g) => (
          <div key={g.topic}>
            <Muted style={{ display: "block", padding: "0 4px 8px", fontWeight: 500 }}>{g.topic || "Bronnen"}</Muted>
            <Card padding={0}>
              {g.items.map((s, i) => (
                <a key={s.link} href={s.link} target="_blank" rel="noopener noreferrer"
                  style={{ display: "flex", flexDirection: "column", gap: 2, padding: "12px 16px", textDecoration: "none", color: "var(--text-primary)", borderTop: i ? "var(--border-1) solid var(--border-default)" : "none" }}>
                  <span style={{ font: "var(--type-body)", fontWeight: 500, textWrap: "pretty" }}>{s.title}</span>
                  <Muted>{s.source}</Muted>
                </a>
              ))}
            </Card>
          </div>
        ))}
        <Muted>Luisteren gebeurt via de persoonlijke feed in Apple Podcasts.</Muted>
        <Button fullWidth variant="secondary" onClick={() => { window.location.href = "podcasts://"; }}>Open Podcasts</Button>
      </Page>
    </>
  );
}
