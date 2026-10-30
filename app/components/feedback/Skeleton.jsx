import React, { useEffect, useState } from "react";

/** Skeleton → content without pop-in: both layers share one grid cell and cross-fade (250ms). ready=false shows the stepped shimmer. */
export function SkeletonSwap({ ready, skeleton, children, style }) {
  const [gone, setGone] = useState(ready);
  useEffect(() => { if (!ready) { setGone(false); return; } const id = setTimeout(() => setGone(true), 300); return () => clearTimeout(id); }, [ready]);
  return (
    <div style={{ display: "grid", ...style }}>
      <div aria-hidden={!ready} style={{ gridArea: "1 / 1", opacity: ready ? 1 : 0, animation: ready ? "mn-fade-in 250ms var(--ease-fade) both" : "none", minWidth: 0 }}>{ready && children}</div>
      {!gone && <div aria-hidden="true" style={{ gridArea: "1 / 1", opacity: ready ? 0 : 1, transition: "opacity 250ms var(--ease-fade)", pointerEvents: "none", minWidth: 0 }}>{skeleton}</div>}
    </div>
  );
}

/** Placeholder block with stepped pixel shimmer (dither band marching in 4 steps). */
export function Skeleton({ width = "100%", height = 16, variant = "block", style }) {
  if (variant === "row") {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 12, height: 64, padding: "0 16px", ...style }}>
        <Skeleton width={40} height={40} />
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 8 }}><Skeleton width="60%" height={12} /><Skeleton width="36%" height={8} /></div>
        <Skeleton width={72} height={12} />
      </div>
    );
  }
  return (
    <span aria-hidden="true" style={{ display: "block", width, height, background: "var(--bg-tertiary)", position: "relative", overflow: "hidden", ...style }}>
      <span style={{ position: "absolute", inset: 0, background: "var(--pattern-dither-25)", opacity: 0.35, animation: "mn-shimmer 1000ms steps(8, end) infinite" }} />
    </span>
  );
}
