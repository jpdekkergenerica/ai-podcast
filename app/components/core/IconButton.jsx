import React, { useState } from "react";
import { Icon } from "./Icon.jsx";
import { PixelLoader } from "./PixelLoader.jsx";
import { haptic } from "./motion.js";

/** 44×44 square icon-only button. ghost (default) · outline · filled. */
export function IconButton({ icon, label, variant = "ghost", size = 44, disabled, loading, selected, forceState, onClick, style }) {
  const [down, setDown] = useState(false);
  const pressed = forceState === "pressed" || down;
  const inv = variant === "filled";
  let bg = inv ? "var(--bg-inverse)" : pressed || selected ? "var(--bg-pressed)" : "transparent";
  if (variant === "filled" && pressed) bg = "var(--bg-inverse-pressed)";
  let fg = inv ? "var(--text-inverse)" : selected ? "var(--text-brand)" : "var(--text-primary)";
  let bd = variant === "outline" ? "var(--border-default)" : selected ? "var(--bg-inverse)" : "transparent";
  if (variant === "filled") bd = bg;
  if (disabled) { bg = variant === "ghost" ? "transparent" : "var(--bg-disabled)"; fg = "var(--text-disabled)"; bd = variant === "outline" ? "var(--border-default)" : "transparent"; }
  return (
    <button type="button" aria-label={label} title={label} disabled={disabled || loading} aria-pressed={selected || undefined} onClick={onClick}
      data-haptic="light" onPointerDown={() => { if (disabled) return; setDown(true); haptic("light", "IconButton"); }} onPointerUp={() => setDown(false)} onPointerLeave={() => setDown(false)}
      style={{
        width: size, height: size, flex: "none", display: "inline-flex", alignItems: "center", justifyContent: "center", padding: 0,
        background: bg, color: fg, border: "var(--border-1) solid " + bd, borderRadius: "var(--radius-input)", boxSizing: "border-box",
        cursor: disabled ? "default" : "pointer", WebkitTapHighlightColor: "transparent",
        outline: forceState === "focused" ? "var(--border-2) solid var(--focus-ring)" : undefined, outlineOffset: "var(--focus-offset)",
        transform: pressed && !disabled ? "scale(var(--press-scale))" : "none", transition: "transform var(--spring-snappy-dur) var(--spring-snappy), background var(--dur-100) var(--ease-step-4)", ...style,
      }}>
      {loading ? <PixelLoader /> : <Icon name={icon} />}
    </button>
  );
}
