import React from "react";

/** Guardia card: wit vlak, 1px rand, 12px radius. padding=0 voor lijsten met ListRow (rijen krijgen hun eigen scheidingslijn). */
export function Card({ children, padding = 16, style }) {
  return (
    <div style={{ background: "var(--bg-card)", border: "var(--border-1) solid var(--border-default)", borderRadius: "var(--radius-card)", boxShadow: "var(--shadow-card)", overflow: "hidden", padding, boxSizing: "border-box", ...style }}>
      {children}
    </div>
  );
}

/** Kleine kopregel boven een kaart of lijst. */
export function SectionTitle({ children, style }) {
  return <div style={{ padding: "0 4px 8px", font: "var(--type-label)", color: "var(--text-secondary)", ...style }}>{children}</div>;
}
