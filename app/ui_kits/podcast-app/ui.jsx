import React from "react";
import { Card, SectionTitle } from "../../components/core/Card.jsx";

/** Groep met kopregel en kaart. */
export function Group({ title, children, padding = 16, style }) {
  return (
    <div style={{ ...style }}>
      {title && <SectionTitle>{title}</SectionTitle>}
      <Card padding={padding} style={{ display: "flex", flexDirection: "column", gap: 16 }}>{children}</Card>
    </div>
  );
}

const TONES = {
  running: ["var(--info-bg)", "var(--info-text)"],
  scheduled: ["var(--info-bg)", "var(--info-text)"],
  published: ["var(--positive-bg)", "var(--positive-text)"],
  failed: ["var(--negative-bg)", "var(--negative-text)"],
  skipped: ["var(--warning-bg)", "var(--warning-text)"],
  paused: ["var(--bg-tertiary)", "var(--text-secondary)"],
};

/** Statuslabel: Gepland · Bezig · Gepubliceerd · Mislukt · Gepauzeerd · Overgeslagen. */
export function StatusPill({ status }) {
  const [bg, fg] = TONES[status.code] || TONES.paused;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6, height: 24, padding: "0 8px", borderRadius: "var(--radius-btn)", background: bg, color: fg, font: "var(--type-caption)", fontWeight: 500, whiteSpace: "nowrap" }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: "currentColor", animation: status.code === "running" ? "mn-loader 900ms steps(1, end) infinite" : "none" }} />
      {status.label}
    </span>
  );
}

/** Omslag: eigen afbeelding of de standaardomslag van de server. */
export function Cover({ url, size = 56, radius = 10, style }) {
  return <img src={url} alt="" width={size} height={size} style={{ width: size, height: size, flex: "none", borderRadius: radius, objectFit: "cover", background: "var(--bg-tertiary)", display: "block", ...style }} />;
}

export const Muted = ({ children, style }) => <span style={{ font: "var(--type-body-small)", color: "var(--text-secondary)", ...style }}>{children}</span>;

/** Foutmelding bij een veld of onderaan het formulier. */
export const FieldError = ({ children }) => children ? <span role="alert" style={{ font: "var(--type-body-small)", color: "var(--negative-text)" }}>{children}</span> : null;

/** Pagina met scrollbare inhoud. */
export function Page({ children, style }) {
  return <div style={{ flex: 1, overflowY: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 16, ...style }}>{children}</div>;
}
