import React from "react";
import { InsightCard } from "../../components/ai/InsightCard.jsx";
import { Button } from "../../components/core/Button.jsx";
import { ListRow } from "../../components/core/ListRow.jsx";
import { Chip } from "../../components/core/Chip.jsx";

function jobLabel(job) {
  if (!job) return "Nog geen run";
  const map = { queued: "In de wachtrij", running: "Bezig", succeeded: "Gelukt", failed: "Mislukt", skipped: "Overgeslagen" };
  return map[job.status] || job.status;
}

export function Home({ show, onCopyFeed, onOpenPodcasts, onBuild, onTopics, building }) {
  const ep = show.latest_episode;
  const job = show.latest_job;
  const mins = show.duration?.max_minutes ?? 15;
  return (
    <>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: 52, padding: "0 4px 0 16px", flex: "none" }}>
        <span style={{ font: "400 24px/28px var(--font-pixel)" }}>podcast</span>
        <Chip variant="code">{mins} MIN</Chip>
      </div>
      <div style={{ flex: 1, overflowY: "auto", scrollbarWidth: "none" }}>
        <div style={{ padding: "8px 16px 20px" }}>
          <div style={{ font: "600 28px/34px var(--font-sans)", letterSpacing: "-0.02em" }}>{show.title}</div>
          <div style={{ marginTop: 6, font: "var(--type-body-small)", color: "var(--text-secondary)", textWrap: "pretty" }}>
            {show.description || "Persoonlijke ochtendbriefing op jouw onderwerpen."}
          </div>
        </div>

        <div style={{ padding: "0 16px 16px" }}>
          {job?.status === "failed" ? (
            <InsightCard title="Laatste run mislukt" tone="negative" icon="alert" action="Opnieuw" onAction={onBuild}>
              {job.error || "Onbekende fout"}
            </InsightCard>
          ) : ep ? (
            <InsightCard title={ep.title} tone="info" icon="play" action="Kopieer feed" onAction={onCopyFeed}>
              {ep.date} · {Math.round(ep.duration / 60)} min · {jobLabel(job)}
            </InsightCard>
          ) : (
            <InsightCard title="Nog geen aflevering" tone="warning" icon="sparkles" action="Bouw nu" onAction={onBuild}>
              Voeg onderwerpen toe en start een build. Daarna volg je de feed in Apple Podcasts.
            </InsightCard>
          )}
        </div>

        <div style={{ padding: "8px 16px", font: "var(--type-headline)" }}>Feed</div>
        <ListRow icon="copy" label="Kopieer privé-feed" description="Plak in Apple Podcasts → Volg via URL" onClick={onCopyFeed} divider={false} />
        <ListRow icon="play" label="Open Podcasts" description="Luisteren gebeurt buiten deze app" onClick={onOpenPodcasts} />

        <div style={{ padding: "16px 16px 8px", font: "var(--type-headline)" }}>Status</div>
        <ListRow icon="repeat" label="Laatste run" value={jobLabel(job)} chevron={false} divider={false} />
        <ListRow icon="hash" label="Onderwerpen" value={String(show.topics?.length || 0)} onClick={onTopics} />

        <div style={{ padding: 16 }}>
          <Button fullWidth loading={building} onClick={onBuild} icon="sparkles">Bouw nu</Button>
        </div>
      </div>
    </>
  );
}
