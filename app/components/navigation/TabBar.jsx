import React from "react";
import { LINE_ICONS } from "../core/icons-line.js";
import { haptic } from "../core/motion.js";

export const DEFAULT_TABS = [
  { value: "home", label: "Home", icon: "dashboard" },
  { value: "topics", label: "Onderwerpen", icon: "flag" },
  { value: "settings", label: "Aflevering", icon: "sliders" },
  { value: "account", label: "Account", icon: "user" },
];

/** Lijn-icoon dat vult wanneer de tab actief is. */
function TabIcon({ name, on }) {
  return React.createElement("svg", {
    viewBox: "0 0 24 24", width: 24, height: 24, fill: on ? "currentColor" : "none", stroke: "currentColor", strokeWidth: on ? 1.75 : 1.5, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true,
    style: { display: "block" },
    dangerouslySetInnerHTML: { __html: LINE_ICONS[name] || "" },
  });
}

/** Guardia-tabbalk: wit, 1px bovenlijn, icoon + label per tab (actief = paars, icoon gevuld).
    Met onCenter komt er een primaire actieknop (paars, 12px radius) in het midden. Haptic: selection. */
export function TabBar({ tabs = DEFAULT_TABS, value = "home", onChange, onCenter, centerLabel = "Bouw", centerPressed, style }) {
  const half = Math.ceil(tabs.length / 2);
  const cell = (t) => {
    const on = t.value === value;
    return (
      <button key={t.value} type="button" aria-label={t.label} aria-current={on ? "page" : undefined} data-haptic="selection"
        onClick={() => { if (!on) haptic("selection", "Tab"); onChange && onChange(t.value); }}
        style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 2, minWidth: 0, background: "none", border: "none", cursor: "pointer", padding: 0, WebkitTapHighlightColor: "transparent", color: on ? "var(--text-brand)" : "var(--text-tertiary)" }}>
        <TabIcon name={t.icon} on={on} />
        <span style={{ font: "500 11px/14px var(--font-sans)", whiteSpace: "nowrap" }}>{t.label}</span>
      </button>
    );
  };
  return (
    <nav aria-label="Hoofdnavigatie" style={{ display: "grid", gridTemplateColumns: onCenter ? "repeat(" + half + ",1fr) 72px repeat(" + (tabs.length - half) + ",1fr)" : "repeat(" + tabs.length + ",1fr)", alignItems: "center", height: "calc(64px + env(safe-area-inset-bottom, 0px))", padding: "0 8px env(safe-area-inset-bottom, 0px)", background: "var(--bg-card)", borderTop: "var(--border-1) solid var(--border-default)", flex: "none", ...style }}>
      {tabs.slice(0, onCenter ? half : tabs.length).map(cell)}
      {onCenter && (
        <button type="button" aria-label={centerLabel} data-haptic="light" onClick={() => { haptic("light", "Center"); onCenter(); }}
          style={{ justifySelf: "center", width: 48, height: 48, display: "inline-flex", alignItems: "center", justifyContent: "center", border: "none", borderRadius: "var(--radius-card)", cursor: "pointer", color: "var(--text-inverse)", background: centerPressed ? "var(--bg-inverse-pressed)" : "var(--bg-inverse)", boxShadow: "var(--shadow-btn)", WebkitTapHighlightColor: "transparent" }}>
          {React.createElement("svg", { viewBox: "0 0 24 24", width: 24, height: 24, fill: "none", stroke: "currentColor", strokeWidth: 1.75, strokeLinecap: "round", "aria-hidden": true, style: { display: "block" }, dangerouslySetInnerHTML: { __html: LINE_ICONS.plus } })}
        </button>
      )}
      {onCenter && tabs.slice(half).map(cell)}
    </nav>
  );
}
