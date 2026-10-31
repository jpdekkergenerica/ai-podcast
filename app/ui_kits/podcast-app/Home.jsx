import React from "react";
import { InsightCard } from "../../components/ai/InsightCard.jsx";
import { Button } from "../../components/core/Button.jsx";
import { ListRow } from "../../components/core/ListRow.jsx";
import { Chip } from "../../components/core/Chip.jsx";
import { Card, SectionTitle } from "../../components/core/Card.jsx";
import { scheduleLabel } from "./schedule.js";
import { BrandHeader } from "../../components/navigation/BrandHeader.jsx";

function jobLabel(job) {
  if (!job) return "Nog geen run";
  const map = { queued: "In de wachtrij", running: "Bezig", succeeded: "Gelukt", failed: "Mislukt", skipped: "Overgeslagen" };
  return map[job.status] || job.status;
}

export function Home({ show, onCopyFeed, onOpenPodcasts, onBuild, onTopics, onSettings, building }) {
  const ep = show.latest_episode;
  const job = show.latest_job;
  const mins = show.duration?.max_minutes ?? 15;
  return (
    <>
      <BrandHeader actions={<Chip variant="code">{mins} MIN</Chip>} />
      <div style={{ flex: 1, overflowY: "auto", scrollbarWidth: "none" }}>
        <div style={{ padding: "16px 16px 16px" }}>
          {job?.status === "failed" ? (
            <InsightCard title="Laatste run mislukt" tone="negative" icon="alert" action="Opnieuw" onAction={onBuild}>
              {job.error || "Onbekende fout"}
            </InsightCard>
          ) : ep ? (
            <InsightCard title={ep.title} tone="info" icon="play" action="Kopieer feed" onAction={onCopyFeed}>
              {ep.date} · {Math.round(ep.duration / 60)} min · {jobLabel(job)}
            </InsightCard>
          ) : (
            <InsightCard title="Nog geen aflevering" tone="info" icon="sparkles" action="Bouw nu" onAction={onBuild}>
              Voeg onderwerpen toe en start een build. Daarna volg je de feed in Apple Podcasts.
            </InsightCard>
          )}
        </div>

        <div style={{ padding: "0 16px 16px" }}>
          <SectionTitle>Feed</SectionTitle>
          <Card padding={0}>
            <ListRow icon="copy" label="Kopieer privé-feed" description="Plak in Apple Podcasts → Volg via URL" onClick={onCopyFeed} divider={false} />
            <ListRow icon="play" label="Open Podcasts" description="Luisteren gebeurt buiten deze app" onClick={onOpenPodcasts} />
          </Card>
        </div>

        <div style={{ padding: "0 16px 16px" }}>
          <SectionTitle>Status</SectionTitle>
          <Card padding={0}>
            <ListRow icon="repeat" label="Laatste run" value={jobLabel(job)} chevron={false} divider={false} />
            <ListRow icon="calendar-month" label="Planning" value={scheduleLabel(show.schedule)} onClick={onSettings} />
            <ListRow icon="hash" label="Onderwerpen" value={String(show.topics?.length || 0)} onClick={onTopics} />
          </Card>
        </div>

        <div style={{ padding: "0 16px 24px" }}>
          <Button fullWidth loading={building} onClick={onBuild} icon="sparkles">Bouw nu</Button>
        </div>
      </div>
    </>
  );
}
