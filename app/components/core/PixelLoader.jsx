import React from "react";

/** Three dots lighting in sequence — the system's only spinner. */
export function PixelLoader({ size = 6, color = "currentColor", label = "Bezig" }) {
  return (
    <span role="status" aria-label={label} style={{ display: "inline-flex", gap: size, alignItems: "center" }}>
      {[0, 1, 2].map((i) => (
        <span key={i} style={{ width: size, height: size, borderRadius: "50%", background: color, animation: "mn-loader 750ms steps(1, end) infinite", animationDelay: i * 250 + "ms" }} />
      ))}
    </span>
  );
}
