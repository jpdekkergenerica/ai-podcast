import React from "react";

/** Square avatar: initials on inverted tile, or a 1-bit photo. */
export function Avatar({ name = "", src, size = 32, onClick, label, style }) {
  const ini = name.split(" ").filter(Boolean).slice(-2).map((w) => w[0]).join("").toUpperCase() || "?";
  const box = { width: size, height: size, flex: "none", display: "inline-flex", alignItems: "center", justifyContent: "center", borderRadius: "var(--radius-full)", background: "var(--bg-secondary)", color: "var(--text-primary)", font: size >= 48 ? "var(--type-title)" : "var(--type-label)", fontWeight: 600, overflow: "hidden", ...style };
  const inner = src ? <img src={src} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(1) contrast(1.4)" }} /> : ini;
  if (!onClick) return <span style={box}>{inner}</span>;
  return (
    <button type="button" onClick={onClick} aria-label={label || "Tài khoản"} style={{ width: Math.max(44, size), height: Math.max(44, size), padding: 0, background: "none", border: "none", display: "inline-flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}>
      <span style={box}>{inner}</span>
    </button>
  );
}
