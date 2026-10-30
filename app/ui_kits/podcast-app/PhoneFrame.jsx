import React from "react";

/** Minimal monochrome device frame, 390×844. [data-mn-frame] hosts overlays ([data-mn-overlay]); [data-mn-content] is what sheets scale back. hud → small haptic readout in the status bar. */
export function PhoneFrame({ children, theme, hud, led }) {
  return (
    <div data-theme={theme} data-led={led ? "" : undefined} data-mn-frame="" style={{ width: 390, height: 844, flex: "none", position: "relative", overflow: "hidden", background: theme === "dark" ? "var(--black)" : "var(--gray-900)", color: "var(--text-primary)", border: "2px solid var(--black)", outline: theme === "dark" ? "1px solid var(--gray-700)" : "none", display: "flex", flexDirection: "column" }}>
      <div data-mn-content="" style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", background: "var(--bg-primary)", position: "relative", overflow: "hidden" }}>
        <div style={{ height: 44, flex: "none", display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 24px", font: "var(--type-mono-small)", fontWeight: 600, position: "relative" }}>
          <span>9:41</span>
          {hud}
          <span style={{ display: "flex", gap: 3, alignItems: "flex-end" }}>{[4, 6, 8, 10].map((h) => <span key={h} style={{ width: 3, height: h, background: "currentColor" }} />)}<span style={{ width: 22, height: 10, border: "1px solid currentColor", marginLeft: 6, padding: 1, boxSizing: "border-box" }}><span style={{ display: "block", width: "70%", height: "100%", background: "currentColor" }} /></span></span>
        </div>
        <div style={{ flex: 1, minHeight: 0, position: "relative", display: "flex", flexDirection: "column" }}>{children}</div>
        <div style={{ height: 20, flex: "none", display: "flex", justifyContent: "center", alignItems: "center", background: "var(--bg-primary)" }}><span style={{ width: 120, height: 4, background: "currentColor" }} /></div>
      </div>
      <div data-mn-overlay="" style={{ position: "absolute", inset: 0, pointerEvents: "none", zIndex: 50 }} />
    </div>
  );
}
