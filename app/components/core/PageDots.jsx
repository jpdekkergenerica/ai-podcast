import React from "react";

/** Pager indicator: 8px squares, active = 24px bar. */
export function PageDots({ count = 3, index = 0, onChange, style }) {
  return (
    <div role="tablist" style={{ display: "flex", gap: 8, alignItems: "center", ...style }}>
      {Array.from({ length: count }).map((_, i) => (
        <button key={i} type="button" aria-label={"Pagina " + (i + 1)} aria-selected={i === index} onClick={() => onChange && onChange(i)}
          style={{ width: i === index ? 24 : 8, height: 8, padding: 0, border: "none", borderRadius: 4, background: i === index ? "var(--bg-inverse)" : "var(--purple-300)", cursor: "pointer", transition: "width var(--dur-150) var(--ease-step-4)" }} />
      ))}
    </div>
  );
}
