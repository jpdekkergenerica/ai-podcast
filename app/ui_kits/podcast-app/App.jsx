import React, { useEffect, useState } from "react";
import { PhoneFrame } from "./PhoneFrame.jsx";
import { TabBar } from "../../components/navigation/TabBar.jsx";
import { Toast } from "../../components/overlays/Toast.jsx";
import { Start } from "./Start.jsx";
import { Home } from "./Home.jsx";
import { Topics } from "./Topics.jsx";
import { Settings, Pronounce } from "./Settings.jsx";
import { Account } from "./Account.jsx";
import { api, getToken, setToken } from "./api.js";

const TABS = [
  { value: "home", label: "Home", icon: "dashboard" },
  { value: "topics", label: "Onderwerpen", icon: "flag" },
  { value: "settings", label: "Aflevering", icon: "sliders" },
  { value: "account", label: "Account", icon: "user" },
];

/** Config-app voor persoonlijke podcasts — Monsey UI kit, Nederlands, geen speler. */
export function App({ theme: theme0 = "light", framed = true }) {
  const [theme, setTheme] = useState(theme0);
  const [show, setShow] = useState(null);
  const [booting, setBooting] = useState(true);
  const [authed, setAuthed] = useState(false); // ingelogd, maar nog geen show
  const [tab, setTab] = useState("home");
  const [stack, setStack] = useState(null); // "pronounce" | null
  const [toast, setToast] = useState(null);
  const [building, setBuilding] = useState(false);

  useEffect(() => {
    if (!toast) return;
    const id = setTimeout(() => setToast(null), 3500);
    return () => clearTimeout(id);
  }, [toast]);

  useEffect(() => {
    (async () => {
      if (!getToken()) { setBooting(false); return; }
      try {
        const s = await api.getShow();
        setShow(s);
      } catch (e) {
        if (e.status === 404) setAuthed(true);
        else setToken("");
      } finally {
        setBooting(false);
      }
    })();
  }, []);

  const refresh = async () => {
    const s = await api.getShow();
    setShow(s);
    return s;
  };

  const copyFeed = async () => {
    try {
      await navigator.clipboard.writeText(show.feed_url);
      setToast({ message: "Feed-URL gekopieerd", icon: "check" });
    } catch {
      setToast({ message: show.feed_url, variant: "default" });
    }
  };

  const openPodcasts = () => {
    // iOS: podcasts://; anders instructie
    window.location.href = "podcasts://";
    setToast({ message: "Plak de feed-URL in Podcasts → Volg via URL" });
  };

  const build = async () => {
    setBuilding(true);
    try {
      const res = await api.build();
      setToast({ message: res.message || "Build gestart", icon: "check" });
      await refresh();
    } catch (e) {
      setToast({ message: e.message, variant: "error", icon: "alert" });
    } finally {
      setBuilding(false);
    }
  };

  const saveShow = async (patch) => {
    const s = await api.updateShow(patch);
    setShow(s);
    return s;
  };

  const saveTopics = async (topics) => {
    const s = await api.updateShow({ topics });
    setShow(s);
    return s;
  };

  let screen;
  if (booting) {
    screen = <div style={{ flex: 1, display: "grid", placeItems: "center", font: "var(--type-body-small)", color: "var(--text-secondary)" }}>Laden…</div>;
  } else if (!show) {
    screen = <Start authed={authed} onReady={(s) => { setShow(s); setTab("home"); }} />;
  } else if (stack === "pronounce") {
    screen = <Pronounce show={show} onBack={() => setStack(null)} onSave={saveShow} />;
  } else if (tab === "home") {
    screen = (
      <Home show={show} building={building}
        onCopyFeed={copyFeed} onOpenPodcasts={openPodcasts} onBuild={build}
        onTopics={() => setTab("topics")} onSettings={() => setTab("settings")} />
    );
  } else if (tab === "topics") {
    screen = (
      <Topics show={show} onBack={() => setTab("home")}
        onSave={saveTopics} onTest={(t) => api.feedTest(t)} />
    );
  } else if (tab === "settings") {
    screen = (
      <Settings show={show} onBack={() => setTab("home")} onSave={saveShow}
        onPronounce={() => setStack("pronounce")} />
    );
  } else {
    screen = (
      <Account show={show} theme={theme} setTheme={setTheme} onBack={() => setTab("home")}
        onRotate={async () => { await api.rotateToken(); await refresh(); setToast({ message: "Nieuw feed-token", icon: "check" }); }}
        onLogout={() => { setToken(""); setShow(null); setAuthed(false); }}
        onDelete={async () => { await api.deleteAccount(); setToken(""); setShow(null); setAuthed(false); }} />
    );
  }

  const body = (
    <>
      {screen}
      {toast && (
        <div style={{ position: "absolute", left: 16, right: 16, bottom: show && !stack && tab ? 80 : 24, zIndex: 40 }}>
          <Toast message={toast.message} icon={toast.icon} variant={toast.variant || "default"} />
        </div>
      )}
      {show && !stack && !booting && (
        <TabBar tabs={TABS} value={tab} onChange={setTab}
          onCenter={build} centerLabel="Bouw" centerPressed={building} />
      )}
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
