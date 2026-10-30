import React from "react";
import { Illustration } from "./Illustration.jsx";
import { Button } from "../core/Button.jsx";

/** Illustration + Geist Pixel headline + one sentence + one action. */
export function EmptyState({ title, children, action, onAction, illustration, illustrationLabel, compact, style }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center", gap: 12, padding: compact ? "24px 16px" : "48px 24px", ...style }}>
      {!compact && <Illustration src={illustration} label={illustrationLabel} size={128} />}
      <span style={{ font: "var(--type-display-s)", color: "var(--text-primary)", textWrap: "balance" }}>{title}</span>
      {children && <span style={{ font: "var(--type-body)", color: "var(--text-secondary)", maxWidth: 300, textWrap: "pretty" }}>{children}</span>}
      {action && <Button variant="secondary" onClick={onAction} style={{ marginTop: 4 }}>{action}</Button>}
    </div>
  );
}
