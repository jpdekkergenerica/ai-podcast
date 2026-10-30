import React, { useState } from "react";
import { Button } from "../../components/core/Button.jsx";
import { TextField } from "../../components/forms/TextField.jsx";
import { PageDots } from "../../components/core/PageDots.jsx";
import { api, setToken } from "./api.js";

/** Onboarding: belofte → login → show-naam. Monsey: Geist Pixel alleen voor display ≥24px. */
export function Start({ onReady }) {
  const [step, setStep] = useState(0);
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const login = async () => {
    setBusy(true); setError("");
    try {
      const res = await api.devLogin();
      setToken(res.access_token);
      if (res.has_show) {
        const show = await api.getShow();
        onReady(show);
      } else setStep(2);
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
    <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: "24px 16px 16px", gap: 24 }}>
      <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", gap: 16 }}>
        {step === 0 && (
          <>
            <span style={{ font: "400 28px/32px var(--font-pixel)", letterSpacing: "-0.02em" }}>jouw ochtend</span>
            <p style={{ margin: 0, font: "var(--type-body)", color: "var(--text-secondary)", textWrap: "pretty" }}>
              Jij kiest de onderwerpen. Wij maken er elke ochtend een podcast van. Luisteren doe je in Apple Podcasts.
            </p>
          </>
        )}
        {step === 1 && (
          <>
            <span style={{ font: "400 28px/32px var(--font-pixel)" }}>inloggen</span>
            <p style={{ margin: 0, font: "var(--type-body)", color: "var(--text-secondary)", textWrap: "pretty" }}>
              In productie via Sign in with Apple. Nu: ontwikkel-login om de kit te testen.
            </p>
          </>
        )}
        {step === 2 && (
          <>
            <span style={{ font: "400 28px/32px var(--font-pixel)" }}>naam</span>
            <p style={{ margin: 0, font: "var(--type-body)", color: "var(--text-secondary)" }}>
              Hoe heet jouw podcast?
            </p>
            <TextField label="Podcastnaam" value={title} onChange={setTitle} error={error && !title.trim() ? error : ""} />
          </>
        )}
        {error && step !== 2 && (
          <p style={{ margin: 0, font: "var(--type-body-small)", color: "var(--negative-text)" }}>{error}</p>
        )}
        {error && step === 2 && title.trim() && (
          <p style={{ margin: 0, font: "var(--type-body-small)", color: "var(--negative-text)" }}>{error}</p>
        )}
      </div>
      <PageDots count={3} index={step} />
      {step === 0 && <Button fullWidth onClick={() => setStep(1)}>Verder</Button>}
      {step === 1 && <Button fullWidth loading={busy} onClick={login}>Doorgaan</Button>}
      {step === 2 && <Button fullWidth loading={busy} onClick={create}>Podcast maken</Button>}
    </div>
  );
}
