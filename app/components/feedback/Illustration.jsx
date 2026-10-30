import React from "react";

/** Slot for a 1-bit pixel-art illustration (black on white). Shows a striped placeholder until src is supplied. */
export function Illustration({ src, alt = "", size = 128, label = "1-bit illustration", style }) {
  if (src) return <img src={src} alt={alt} width={size} height={size} style={{ imageRendering: "pixelated", display: "block", ...style }} />;
  return (
    <div role="img" aria-label={alt || label} style={{ width: size, height: size, flex: "none", boxSizing: "border-box", border: "var(--border-1) solid var(--border-strong)",
      background: "repeating-linear-gradient(135deg, var(--bg-primary) 0 6px, var(--bg-tertiary) 6px 8px)", display: "flex", alignItems: "flex-end", padding: 6, ...style }}>
      <span style={{ font: "var(--type-mono-small)", color: "var(--text-primary)", background: "var(--bg-primary)", padding: "0 2px" }}>{label}</span>
    </div>
  );
}
