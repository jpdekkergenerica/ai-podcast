import React from "react";

/** yourownpod-merkteken: paars vlak met drie geluidsstaafjes. */
export function BrandMark({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" style={{ display: "block", flex: "none" }}>
      <rect width="24" height="24" rx="6" fill="var(--purple-600)" />
      <g fill="#fff"><rect x="6" y="9" width="2.6" height="6" rx="1.3" /><rect x="10.7" y="6" width="2.6" height="12" rx="1.3" /><rect x="15.4" y="10" width="2.6" height="4" rx="1.3" /></g>
    </svg>
  );
}

/** Guardia-header op tab-roots: wit, 1px onderlijn, merk links en een vrij slot rechts. */
export function BrandHeader({ actions, style }) {
  return (
    <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: 56, padding: "0 16px", background: "var(--bg-card)", borderBottom: "var(--border-1) solid var(--border-default)", flex: "none", ...style }}>
      <span style={{ display: "inline-flex", alignItems: "center", gap: 8, font: "var(--type-headline)", letterSpacing: "-0.01em" }}>
        <BrandMark />yourownpod
      </span>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>{actions}</div>
    </header>
  );
}
