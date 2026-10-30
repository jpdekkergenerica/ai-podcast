import React from "react";

/** Three square blocks lighting in sequence — the system's only spinner. */
export function PixelLoader({ size = 4, color = "currentColor", label = "Đang xử lý" }) {
  return (
    <span role="status" aria-label={label} style={{ display: "inline-flex", gap: size, alignItems: "center" }}>
      {[0, 1, 2].map((i) => (
        <span key={i} style={{ width: size, height: size, background: color, animation: "mn-loader 750ms steps(1, end) infinite", animationDelay: i * 250 + "ms" }} />
      ))}
    </span>
  );
}
