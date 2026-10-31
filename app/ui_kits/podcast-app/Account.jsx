import React, { useEffect, useState } from "react";
import { BrandHeader } from "../../components/navigation/BrandHeader.jsx";
import { Button } from "../../components/core/Button.jsx";
import { Card } from "../../components/core/Card.jsx";
import { ListRow } from "../../components/core/ListRow.jsx";
import { Switch } from "../../components/core/Switch.jsx";
import { Dialog } from "../../components/overlays/Dialog.jsx";
import { api, pushRegister, pushStatus } from "./api.js";
import { Muted, Page } from "./ui.jsx";

/** Scherm 8 · Account en meldingen: Apple-account, pushstatus en twee afzonderlijke meldingsvoorkeuren. */
export function Account({ theme, setTheme, onLogout, onDeleted, toast }) {
  const [me, setMe] = useState(null);
  const [push, setPush] = useState({ status: "unknown" });
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);

  const refreshPush = async () => setPush(await pushStatus());
  useEffect(() => { api.me().then(setMe).catch(() => {}); refreshPush(); }, []);

  const setPref = async (key, value) => {
    setMe({ ...me, [key]: value });
    try { setMe(await api.setNotifications({ [key]: value })); } catch (e) { toast(e.message, "alert", "error"); api.me().then(setMe); }
  };

  const enablePush = async () => {
    const res = await pushRegister();
    setPush(res);
    if (res.token) { try { setMe(await api.registerDevice(res.token)); } catch (e) { toast(e.message, "alert", "error"); } }
    else if (res.status === "denied") toast("Meldingen staan uit voor deze app. Zet ze aan in Instellingen van je iPhone.", "alert");
  };

  const pushText = {
    authorized: me?.push_registered ? "Aan" : "Toegestaan, nog niet gekoppeld",
    denied: "Geweigerd in Instellingen",
    notDetermined: "Nog niet ingesteld",
    unsupported: "Alleen beschikbaar in de app",
  }[push.status] || "Onbekend";

  const del = async () => {
    setBusy(true);
    try { await api.deleteAccount(); onDeleted(); } catch (e) { toast(e.message, "alert", "error"); setBusy(false); setConfirm(false); }
  };

  return (
    <>
      <BrandHeader />
      <Page>
        <Card padding={0}>
          <ListRow icon="user" label="Apple-account" description={me?.email || "Ingelogd met Apple"} chevron={false} divider={false} />
        </Card>

        <div>
          <Muted style={{ display: "block", padding: "0 4px 8px", fontWeight: 500 }}>Meldingen</Muted>
          <Card padding={0}>
            <ListRow icon="notification" label="Pushmeldingen" value={pushText} chevron={false} divider={false} />
            <ListRow label="Nieuwe aflevering" description="Als een aflevering klaarstaat" chevron={false} divider
              trailing={<Switch checked={!!me?.notify_new} onChange={(v) => setPref("notify_new", v)} label="Melding bij een nieuwe aflevering" />} />
            <ListRow label="Mislukte aflevering" description="Als het maken niet lukt" chevron={false}
              trailing={<Switch checked={!!me?.notify_failed} onChange={(v) => setPref("notify_failed", v)} label="Melding bij een mislukte aflevering" />} />
          </Card>
          {(push.status === "notDetermined" || (push.status === "authorized" && me && !me.push_registered)) && (
            <Button fullWidth style={{ marginTop: 12 }} onClick={enablePush}>Meldingen inschakelen</Button>
          )}
          <Muted style={{ display: "block", marginTop: 8 }}>
            De status van elke podcast blijft altijd zichtbaar in de app, ook als je geen meldingen ontvangt.
          </Muted>
        </div>

        <Card padding={0}>
          <ListRow icon="moon" label="Donkere modus" chevron={false} divider={false}
            trailing={<Switch checked={theme === "dark"} onChange={(v) => setTheme(v ? "dark" : "light")} label="Donkere modus" />} />
          <ListRow icon="close" label="Uitloggen" onClick={onLogout} />
          <ListRow icon="warning" label="Account verwijderen" danger onClick={() => setConfirm(true)} />
        </Card>
        <div style={{ padding: "0 4px" }}>
          <a href="#privacy" onClick={(e) => { e.preventDefault(); window.open((window.PODCAST_API_BASE || "http://127.0.0.1:8000") + "/privacy", "_blank"); }}
            style={{ font: "var(--type-label)", color: "var(--text-brand)", textDecoration: "none" }}>Privacy</a>
        </div>
      </Page>
      <Dialog open={confirm} title="Account verwijderen?" destructive confirmLabel="Verwijderen" cancelLabel="Annuleren" loading={busy}
        onConfirm={del} onCancel={() => setConfirm(false)}>
        Al je podcasts, afleveringen en feeds verdwijnen. Dit kun je niet terugdraaien.
      </Dialog>
    </>
  );
}
