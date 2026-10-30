import React, { useState } from "react";
import { TopAppBar } from "../../components/navigation/TopAppBar.jsx";
import { ListRow } from "../../components/core/ListRow.jsx";
import { Switch } from "../../components/core/Switch.jsx";
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
      <div style={{ flex: 1, overflowY: "auto", position: "relative" }}>
        <ListRow icon="moon" label="Donker (LED)" description="True inversion van Paper"
          chevron={false} divider={false}
          trailing={<Switch checked={theme === "dark"} onChange={(v) => setTheme(v)} label="Donker" />} />
        <ListRow icon="copy" label="Feed-URL" description={show.feed_url} chevron={false}
          onClick={() => navigator.clipboard?.writeText(show.feed_url)} />
        <ListRow icon="repeat" label="Feed-token vernieuwen"
          description="Oude URL stopt met werken" onClick={() => setConfirm("rotate")} />
        <ListRow icon="close" label="Uitloggen" onClick={onLogout} />
        <ListRow icon="warning" label="Account verwijderen" danger onClick={() => setConfirm("delete")} />
        <div style={{ padding: 16 }}>
          <a href="#privacy" onClick={(e) => { e.preventDefault(); window.open((window.PODCAST_API_BASE || "http://127.0.0.1:8000") + "/privacy", "_blank"); }}
            style={{ font: "var(--type-label)", color: "var(--info-text)" }}>Privacy</a>
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
