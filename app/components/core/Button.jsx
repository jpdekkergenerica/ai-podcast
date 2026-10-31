import React, { useState } from "react";
import { Icon } from "./Icon.jsx";
import { PixelLoader } from "./PixelLoader.jsx";
import { haptic } from "./motion.js";

const H = { sm: 36, md: 48, lg: 52 };

/** primary · secondary · tertiary · destructive. forceState lets docs show pressed/focused.
    Motion: press → scale(--press-scale) + 4% darken on spring/snappy; release springs back. Haptic: light (destructive: medium). */
export function Button({ variant = "primary", size = "md", children, icon, iconRight, disabled, loading, fullWidth, forceState, onClick, type = "button", style }) {
  const [down, setDown] = useState(false);
  const pressed = forceState === "pressed" || down;
  const focused = forceState === "focused";
  const inert = disabled || loading;
  const v = variant === "destructive" ? "primary" : variant;
  let bg = "transparent", fg = "var(--text-primary)", bd = "transparent";
  if (v === "primary") { bg = pressed ? "var(--bg-inverse-pressed)" : "var(--bg-inverse)"; fg = "var(--text-inverse)"; bd = bg; }
  if (v === "secondary") { bg = pressed ? "var(--bg-pressed)" : "var(--bg-card)"; bd = "var(--border-default)"; }
  if (v === "tertiary") { fg = "var(--text-brand)"; if (pressed) bg = "var(--bg-pressed)"; }
  if (disabled) { bg = v === "tertiary" ? "transparent" : "var(--bg-disabled)"; fg = "var(--text-disabled)"; bd = v === "secondary" ? "var(--border-default)" : bg; }
  if (variant === "destructive" && !disabled) { bg = pressed ? "var(--negative-fill-pressed)" : "var(--negative-fill)"; fg = "var(--negative-on)"; bd = bg; }
  const lead = variant === "destructive" ? (icon || "warning-box") : icon;
  const h = H[size] || 48;
  return (
    <button type={type} disabled={inert} aria-busy={loading || undefined} onClick={onClick}
      data-haptic={variant === "destructive" ? "medium" : "light"}
      onPointerDown={() => { if (inert) return; setDown(true); haptic(variant === "destructive" ? "medium" : "light", "Button"); }} onPointerUp={() => setDown(false)} onPointerLeave={() => setDown(false)}
      style={{
        position: "relative", flexShrink: 0, display: fullWidth ? "flex" : "inline-flex", width: fullWidth ? "100%" : undefined,
        alignItems: "center", justifyContent: "center", gap: 8, height: h, minWidth: 44,
        padding: v === "tertiary" ? "0 12px" : size === "sm" ? "0 12px" : "0 20px", boxSizing: "border-box",
        background: bg, color: fg, border: "var(--border-1) solid " + bd, borderRadius: "var(--radius-btn)",
        font: "var(--type-label)", letterSpacing: "var(--ls-label)",
        boxShadow: disabled || v === "tertiary" ? "none" : v === "secondary" ? "var(--shadow-btn-secondary)" : "var(--shadow-btn)", textDecoration: "none",
        cursor: inert ? "default" : "pointer", WebkitTapHighlightColor: "transparent",
        outline: focused ? "var(--border-2) solid var(--focus-ring)" : undefined, outlineOffset: "var(--focus-offset)",
        transform: pressed && !inert ? "scale(var(--press-scale))" : "none", filter: pressed && !inert ? "var(--press-darken)" : "none",
        transition: "transform var(--spring-snappy-dur) var(--spring-snappy), filter var(--spring-snappy-dur) var(--spring-snappy), background var(--dur-100) var(--ease-step-4)", ...style,
      }}>
      {loading ? <PixelLoader /> : <>
        {lead && <Icon name={lead} />}
        <span style={{ whiteSpace: "nowrap" }}>{children}</span>
        {iconRight && <Icon name={iconRight} />}
      </>}
    </button>
  );
}
