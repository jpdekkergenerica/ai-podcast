import React, { useEffect, useState } from "react";
import { Button } from "../../components/core/Button.jsx";
import { TextField } from "../../components/forms/TextField.jsx";
import { BrandMark } from "../../components/navigation/BrandHeader.jsx";
import { PageDots } from "../../components/core/PageDots.jsx";
import { api, setToken, hasNativeApple, nativeAppleSignIn } from "./api.js";

/** Start: Sign in with Apple (zolang er geen login is) → show-naam. Monsey: Geist Pixel alleen voor display ≥24px. */
export function Start({ onReady, authed = false }) {
  const [step, setStep] = useState(authed ? 1 : 0);
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [devAuth, setDevAuth] = useState(false);

  useEffect(() => {
    api.health().then((h) => setDevAuth(!!h.dev_auth)).catch(() => {});
  }, []);

  const finishLogin = async (res) => {
    setToken(res.access_token);
    if (res.has_show) onReady(await api.getShow());
    else setStep(1);
  };

  const appleLogin = async () => {
    setBusy(true); setError("");
    try {
      if (!hasNativeApple()) throw new Error("Sign in with Apple werkt alleen in de app.");
      const { identityToken, email } = await nativeAppleSignIn();
      await finishLogin(await api.appleLogin(identityToken, email));
    } catch (e) {
      setError(e.message || "Inloggen mislukt");
    } finally {
      setBusy(false);
    }
  };

  const devLogin = async () => {
    setBusy(true); setError("");
    try {
      await finishLogin(await api.devLogin());
    } catch (e) {
      setError(e.message || "Inloggen mislukt. Draait de API?");
    } finally {
      setBusy(false);
    }
  };

  const create = async () => {
    if (!title.trim()) { setError("Geef je podcast een naam"); return; }
    setBusy(true); setError("");
    try {
      const show = await api.createShow({
        title: title.trim(),
        description: "Elke ochtend een persoonlijke nieuwspodcast over jouw onderwerpen.",
        topics: [],
      });
      onReady(show);
    } catch (e) {
      setError(e.message || "Aanmaken mislukt");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: "32px 20px 24px", gap: 24, background: "var(--bg-primary)" }}>
      <span style={{ display: "inline-flex", alignItems: "center", gap: 8, font: "var(--type-headline)", letterSpacing: "-0.01em" }}>
        <BrandMark size={40} />yourownpod
      </span>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", gap: 8 }}>
        {step === 0 && (
          <>
            <h1 style={{ margin: 0, font: "var(--type-display-l)", letterSpacing: "var(--ls-display-l)", textWrap: "balance" }}>Jouw ochtend, jouw podcast</h1>
            <p style={{ margin: 0, font: "var(--type-body)", color: "var(--text-secondary)", textWrap: "pretty" }}>
              Jij kiest de onderwerpen. Wij maken er elke ochtend een podcast van. Luisteren doe je in Apple Podcasts.
            </p>
          </>
        )}
        {step === 1 && (
          <>
            <h1 style={{ margin: 0, font: "var(--type-display-l)", letterSpacing: "var(--ls-display-l)" }}>Geef je podcast een naam</h1>
            <p style={{ margin: "0 0 16px", font: "var(--type-body)", color: "var(--text-secondary)" }}>
              Je kunt dit later altijd aanpassen.
            </p>
            <TextField label="Podcastnaam" value={title} onChange={setTitle} placeholder="Mijn ochtendbriefing"
              error={error && !title.trim() ? error : ""} />
          </>
        )}
        {error && !(step === 1 && !title.trim()) && (
          <p style={{ margin: "8px 0 0", font: "var(--type-body-small)", color: "var(--negative-text)" }}>{error}</p>
        )}
      </div>
      <PageDots count={2} index={step} />
      {step === 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <Button fullWidth variant="secondary" size="lg" loading={busy} onClick={appleLogin}>
            <span style={{ fontFamily: "-apple-system, system-ui", fontSize: 20, marginRight: 2, color: "var(--text-primary)" }} aria-hidden>{"\uF8FF"}</span> Doorgaan met Apple
          </Button>
          {devAuth && <Button fullWidth variant="tertiary" disabled={busy} onClick={devLogin}>Ontwikkel-login</Button>}
        </div>
      )}
      {step === 1 && <Button fullWidth size="lg" loading={busy} onClick={create}>Podcast maken</Button>}
    </div>
  );
}
