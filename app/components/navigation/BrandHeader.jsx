import React from "react";

/** yourownpod-beeldmerk (zelfde ontwerp als het app-icoon). */
export function BrandMark({ size = 24 }) {
  return <img src="../../assets/logo.png" srcSet="../../assets/logo.png 1x, ../../assets/logo@2x.png 2x" width={size} height={size} alt="" aria-hidden="true" style={{ display: "block", flex: "none", borderRadius: size * 0.22 }} />;
}

/** Guardia-header op tab-roots: wit, 1px onderlijn, merk links en een vrij slot rechts. */
export function BrandHeader({ actions, style }) {
  return (
    <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", height: 56, padding: "0 16px", background: "var(--bg-card)", borderBottom: "var(--border-1) solid var(--border-default)", flex: "none", ...style }}>
      <span style={{ display: "inline-flex", alignItems: "center", gap: 8, font: "var(--type-headline)", letterSpacing: "-0.01em" }}>
        <BrandMark size={28} />yourownpod
      </span>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>{actions}</div>
    </header>
  );
}
