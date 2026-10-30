import React from "react";
import { Icon } from "./Icon.jsx";
import { haptic } from "./motion.js";

/** Filter / choice chip (radius-full) and the currency-code chip (variant="code").
    Motion: selecting grows the ink fill from the centre (spring/snappy, ~200ms) and draws a checkmark in. Haptic: selection. */
export function Chip({ children, selected, disabled, icon, onRemove, variant = "filter", onClick, forceState, style }) {
  if (variant === "code") {
    return <span style={{ display: "inline-flex", alignItems: "center", height: 20, padding: "0 4px", border: "var(--border-1) solid var(--border-strong)", borderRadius: "var(--radius-xs)", font: "var(--type-mono-small)", fontWeight: 500, letterSpacing: "0.04em", color: "var(--text-primary)", ...style }}>{children}</span>;
  }
  const inv = selected && !disabled;
  const check = !icon && !onRemove;
  const ease = "var(--spring-snappy-dur) var(--spring-snappy)";
  return (
    <button type="button" disabled={disabled} aria-pressed={!!selected} data-haptic="selection"
      onClick={(e) => { haptic("selection", "Chip"); onClick && onClick(e); }}
      style={{
        position: "relative", overflow: "hidden", isolation: "isolate", flexShrink: 0,
        display: "inline-flex", alignItems: "center", gap: 0, height: 32, padding: icon ? "0 12px 0 8px" : "0 12px", boxSizing: "border-box",
        background: forceState === "pressed" && !inv ? "var(--bg-pressed)" : "var(--bg-primary)",
        color: disabled ? "var(--text-disabled)" : inv ? "var(--text-inverse)" : "var(--text-primary)",
        border: "var(--border-1) solid " + (disabled ? "var(--border-default)" : inv ? "var(--bg-inverse)" : "var(--border-control)"),
        borderRadius: "var(--radius-full)", font: "var(--type-label)", whiteSpace: "nowrap", cursor: disabled ? "default" : "pointer",
        outline: forceState === "focused" ? "var(--border-2) solid var(--focus-ring)" : undefined, outlineOffset: 2,
        transition: "color " + ease + ", border-color " + ease,
        /* 32px visual, 44px hit area */ margin: "6px 0", ...style,
      }}>
      <span aria-hidden="true" style={{ position: "absolute", inset: 0, zIndex: -1, borderRadius: "inherit", background: "var(--bg-inverse)", transform: inv ? "scale(1)" : "scale(0.3, 0)", opacity: inv ? 1 : 0, transition: "transform 200ms var(--spring-snappy), opacity 120ms var(--ease-fade)" }} />
      {icon && <span style={{ marginRight: 4, display: "inline-flex" }}><Icon name={icon} size={24} /></span>}
      {check && (
        <span aria-hidden="true" style={{ display: "inline-flex", width: inv ? 20 : 0, marginLeft: inv ? -2 : 0, overflow: "hidden", transition: "width " + ease + ", margin " + ease, flex: "none" }}>
          {inv && <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ display: "block", flex: "none" }}>
            <path d="m5 12.5 4.5 4.5L19 7.5" pathLength="24" strokeDasharray="24" style={{ animation: "mn-draw 200ms var(--ease-fade) 80ms both" }} />
          </svg>}
        </span>
      )}
      {children}
      {onRemove && <span onClick={(e) => { e.stopPropagation(); haptic("light", "Chip remove"); onRemove(); }} aria-label="Bỏ lọc" style={{ display: "inline-flex", marginRight: -6, marginLeft: 4 }}><Icon name="close" /></span>}
    </button>
  );
}
