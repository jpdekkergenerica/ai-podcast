import React, { useState } from "react";
import { Icon } from "./Icon.jsx";
import { haptic } from "./motion.js";

/** 56×56 square floating action — black block with a 2px bg-colored inner keyline so it reads on any surface. */
export function FAB({ icon = "plus", label = "Thêm giao dịch", extended, disabled, forceState, onClick, style }) {
  const [down, setDown] = useState(false);
  const pressed = forceState === "pressed" || down;
  const bg = disabled ? "var(--bg-disabled)" : pressed ? "var(--bg-inverse-pressed)" : "var(--bg-inverse)";
  return (
    <button type="button" aria-label={label} disabled={disabled} onClick={onClick}
      data-haptic="light" onPointerDown={() => { if (disabled) return; setDown(true); haptic("light", "FAB"); }} onPointerUp={() => setDown(false)} onPointerLeave={() => setDown(false)}
      style={{
        height: 56, minWidth: 56, padding: extended ? "0 20px 0 16px" : 0, display: "inline-flex", alignItems: "center", justifyContent: "center", gap: 8,
        background: bg, color: disabled ? "var(--text-disabled)" : "var(--text-inverse)", border: "none", borderRadius: "var(--radius-full)",
        boxShadow: "0 0 0 4px var(--bg-primary), var(--shadow-float)", font: "var(--type-headline)", cursor: disabled ? "default" : "pointer",
        outline: forceState === "focused" ? "var(--border-2) solid var(--focus-ring)" : undefined, outlineOffset: 4,
        transform: pressed && !disabled ? "scale(var(--press-scale))" : "none", transition: "transform var(--spring-snappy-dur) var(--spring-snappy), background var(--dur-100) var(--ease-step-4)", ...style,
      }}>
      <Icon name={icon} />
      {extended && <span>{label}</span>}
    </button>
  );
}
