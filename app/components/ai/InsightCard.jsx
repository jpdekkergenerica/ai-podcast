import React from "react";
import { Icon } from "../core/Icon.jsx";

/** One AI observation: headline, explanation, optional visual, one action. */
const TONE = { info: ["var(--info-fill)", "var(--info-on)"], warning: ["var(--warning-fill)", "var(--warning-on)"], negative: ["var(--negative-fill)", "var(--negative-on)"], positive: ["var(--positive-fill)", "var(--positive-on)"] };
export function InsightCard({ title, children, icon = "zap", tone = "info", action, onAction, visual, onDismiss, style }) {
  return (
    <div style={{ border: "var(--border-1) solid var(--border-default)", background: "var(--bg-primary)", padding: 16, display: "flex", flexDirection: "column", gap: 12, color: "var(--text-primary)", ...style }}>
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
        <span style={{ display: "inline-flex", flex: "none" }}><Icon name={icon} filled color={TONE[tone][0]} onColor={TONE[tone][1]} /></span>
        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: 4 }}>
          <span style={{ font: "var(--type-headline)", textWrap: "pretty" }}>{title}</span>
          {children && <span style={{ font: "var(--type-body-small)", color: "var(--text-secondary)", textWrap: "pretty" }}>{children}</span>}
        </div>
        {onDismiss && <button type="button" aria-label="Ẩn" onClick={onDismiss} style={{ background: "none", border: "none", padding: 10, margin: -10, color: "var(--text-tertiary)", cursor: "pointer" }}><Icon name="close" /></button>}
      </div>
      {visual}
      {action && <button type="button" onClick={onAction} style={{ alignSelf: "flex-start", background: "none", border: "none", padding: 0, minHeight: 32, font: "var(--type-label)", color: "var(--text-primary)", textDecoration: "underline", textUnderlineOffset: 4, cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 4 }}>{action}<Icon name="arrow-right" /></button>}
    </div>
  );
}
