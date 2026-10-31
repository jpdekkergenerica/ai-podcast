import React, { useEffect, useState } from "react";
import { Button } from "../../components/core/Button.jsx";
import { BrandMark } from "../../components/navigation/BrandHeader.jsx";
import { api, setToken, hasNativeApple, nativeAppleSignIn } from "./api.js";

/** Scherm 1 · Aanmelden: korte uitleg en Log in met Apple. Annuleren laat je hier; een fout krijgt een begrijpelijke melding. */
export function Start({ onReady }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [devAuth, setDevAuth] = useState(false);

  useEffect(() => {
    api.health().then((h) => setDevAuth(!!h.dev_auth)).catch(() => {});
  }, []);

  const finish = (res) => { setToken(res.access_token); onReady(); };

  const appleLogin = async () => {
    setBusy(true); setError("");
    try {
      if (!hasNativeApple()) throw new Error("Inloggen met Apple werkt alleen in de app.");
      const { identityToken, email } = await nativeAppleSignIn();
      finish(await api.appleLogin(identityToken, email));
    } catch (e) {
      // annuleren is geen fout: je blijft gewoon op dit scherm
      if (!/geannuleerd/i.test(e.message || "")) setError(e.message || "Inloggen mislukt. Probeer het opnieuw.");
    } finally {
      setBusy(false);
    }
  };

  const devLogin = async () => {
    setBusy(true); setError("");
    try { finish(await api.devLogin()); } catch (e) { setError(e.message || "Inloggen mislukt. Draait de API?"); } finally { setBusy(false); }
  };

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: "32px 20px 24px", gap: 24, background: "var(--bg-primary)" }}>
      <span style={{ display: "inline-flex", alignItems: "center", gap: 8, font: "var(--type-headline)", letterSpacing: "-0.01em" }}>
        <BrandMark size={40} />yourownpod
      </span>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", gap: 8 }}>
        <h1 style={{ margin: 0, font: "var(--type-display-l)", letterSpacing: "var(--ls-display-l)", textWrap: "balance" }}>Jouw onderwerpen, jouw podcast</h1>
        <p style={{ margin: 0, font: "var(--type-body)", color: "var(--text-secondary)", textWrap: "pretty" }}>
          Kies waar je nieuws over wilt horen. Wij maken en publiceren de afleveringen in je eigen feed. Luisteren doe je in Apple Podcasts.
        </p>
        {error && <p role="alert" style={{ margin: "8px 0 0", font: "var(--type-body-small)", color: "var(--negative-text)" }}>{error}</p>}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <Button fullWidth variant="secondary" size="lg" loading={busy} onClick={appleLogin}>
          <span style={{ fontFamily: "-apple-system, system-ui", fontSize: 20, marginRight: 2, color: "var(--text-primary)" }} aria-hidden>{"\uF8FF"}</span> Doorgaan met Apple
        </Button>
        {devAuth && <Button fullWidth variant="tertiary" disabled={busy} onClick={devLogin}>Ontwikkel-login</Button>}
      </div>
    </div>
  );
}
