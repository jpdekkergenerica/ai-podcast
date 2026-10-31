import React, { useEffect, useState } from "react";
import { PhoneFrame } from "./PhoneFrame.jsx";
import { TabBar } from "../../components/navigation/TabBar.jsx";
import { Toast } from "../../components/overlays/Toast.jsx";
import { Start } from "./Start.jsx";
import { PodcastList } from "./PodcastList.jsx";
import { PodcastForm } from "./PodcastForm.jsx";
import { PodcastDetail } from "./PodcastDetail.jsx";
import { EpisodeDetail } from "./EpisodeDetail.jsx";
import { Account } from "./Account.jsx";
import { api, getToken, setToken } from "./api.js";

const TABS = [
  { value: "podcasts", label: "Podcasts", icon: "dashboard" },
  { value: "account", label: "Account", icon: "user" },
];

/** yourownpod — Guardia-stijl, Nederlands. Mijn podcasts is het startpunt; detail- en formulierschermen liggen als stapel erboven. */
export function App({ theme: theme0 = "light", framed = true }) {
  const [theme, setTheme] = useState(theme0);
  const [authed, setAuthed] = useState(false);
  const [booting, setBooting] = useState(true);
  const [tab, setTab] = useState("podcasts");
  const [stack, setStack] = useState([]);
  const [toast, setToast] = useState(null);
  const [listKey, setListKey] = useState(0); // ververst Mijn podcasts na een wijziging

  useEffect(() => {
    if (!toast) return undefined;
    const id = setTimeout(() => setToast(null), 3500);
    return () => clearTimeout(id);
  }, [toast]);

  useEffect(() => {
    (async () => {
      if (getToken()) {
        try { await api.me(); setAuthed(true); } catch (e) { if (e.status === 401) setToken(""); else setAuthed(true); }
      }
      setBooting(false);
    })();
  }, []);

  const showToast = (message, icon, variant) => setToast({ message, icon, variant });
  const nav = {
    push: (screen) => setStack((s) => [...s, screen]),
    pop: () => setStack((s) => s.slice(0, -1)),
    toast: showToast,
    // klaar met een scherm: terug naar het overzicht met een melding
    done: (saved, message) => {
      setStack(saved && saved.id ? [{ name: "detail", id: saved.id }] : []);
      setTab("podcasts");
      setListKey((k) => k + 1);
      if (message) showToast(message, "alert", "error");
    },
  };

  const logout = () => { setToken(""); setAuthed(false); setStack([]); setTab("podcasts"); };

  const top = stack[stack.length - 1];
  let screen;
  if (booting) {
    screen = <div style={{ flex: 1, display: "grid", placeItems: "center", font: "var(--type-body-small)", color: "var(--text-secondary)" }}>Laden…</div>;
  } else if (!authed) {
    screen = <Start onReady={() => setAuthed(true)} />;
  } else if (top?.name === "form") {
    screen = <PodcastForm key={top.id || "new"} id={top.id} nav={nav} />;
  } else if (top?.name === "detail") {
    screen = <PodcastDetail key={top.id} id={top.id} nav={nav} />;
  } else if (top?.name === "episode") {
    screen = <EpisodeDetail key={top.guid} id={top.id} guid={top.guid} nav={nav} />;
  } else if (tab === "account") {
    screen = <Account theme={theme} setTheme={setTheme} onLogout={logout} onDeleted={logout} toast={showToast} />;
  } else {
    screen = <PodcastList key={listKey} nav={nav} />;
  }

  const showTabs = authed && !booting && stack.length === 0;
  const body = (
    <>
      {screen}
      {toast && (
        <div style={{ position: "absolute", left: 16, right: 16, bottom: showTabs ? 80 : 24, zIndex: 40 }}>
          <Toast message={toast.message} icon={toast.icon} variant={toast.variant || "default"} />
        </div>
      )}
      {showTabs && <TabBar tabs={TABS} value={tab} onChange={setTab} />}
    </>
  );

  if (!framed) {
    return (
      <div data-theme={theme} style={{ height: "100%", display: "flex", flexDirection: "column", background: "var(--bg-primary)", color: "var(--text-primary)", position: "relative" }}>
        {body}
      </div>
    );
  }
  return <PhoneFrame theme={theme}>{body}</PhoneFrame>;
}
