import React, { useState } from "react";
import { TopAppBar } from "../../components/navigation/TopAppBar.jsx";
import { ListRow } from "../../components/core/ListRow.jsx";
import { Switch } from "../../components/core/Switch.jsx";
import { Card } from "../../components/core/Card.jsx";
import { Dialog } from "../../components/overlays/Dialog.jsx";

export function Account({ show, theme, setTheme, onBack, onRotate, onLogout, onDelete }) {
  const [confirm, setConfirm] = useState(null); // rotate | delete
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setBusy(true);
    try {
      if (confirm === "rotate") await onRotate();
      if (confirm === "delete") await onDelete();
      setConfirm(null);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <TopAppBar title="Account" onBack={onBack} />
      <div style={{ flex: 1, overflowY: "auto", position: "relative", padding: 16, display: "flex", flexDirection: "column", gap: 16 }}>
        <Card padding={0}>
          <ListRow icon="moon" label="Donkere modus" chevron={false} divider={false}
            trailing={<Switch checked={theme === "dark"} onChange={(v) => setTheme(v ? "dark" : "light")} label="Donkere modus" />} />
          <ListRow icon="copy" label="Feed-URL" description={show.feed_url} chevron={false}
            onClick={() => navigator.clipboard?.writeText(show.feed_url)} />
          <ListRow icon="repeat" label="Feed-token vernieuwen"
            description="Oude URL stopt met werken" onClick={() => setConfirm("rotate")} />
        </Card>
        <Card padding={0}>
          <ListRow icon="close" label="Uitloggen" onClick={onLogout} divider={false} />
          <ListRow icon="warning" label="Account verwijderen" danger onClick={() => setConfirm("delete")} />
        </Card>
        <div style={{ padding: "0 4px" }}>
          <a href="#privacy" onClick={(e) => { e.preventDefault(); window.open((window.PODCAST_API_BASE || "http://127.0.0.1:8000") + "/privacy", "_blank"); }}
            style={{ font: "var(--type-label)", color: "var(--text-brand)", textDecoration: "none" }}>Privacy</a>
        </div>
        <Dialog
          open={!!confirm}
          title={confirm === "delete" ? "Account verwijderen?" : "Feed-token vernieuwen?"}
          destructive={confirm === "delete"}
          confirmLabel={confirm === "delete" ? "Verwijderen" : "Vernieuwen"}
          cancelLabel="Annuleren"
          onConfirm={run}
          onCancel={() => setConfirm(null)}
          loading={busy}
        >
          {confirm === "delete"
            ? "Je show, afleveringen en feed verdwijnen. Dit kun je niet terugdraaien."
            : "Apple Podcasts moet de nieuwe URL opnieuw volgen."}
        </Dialog>
      </div>
    </>
  );
}
