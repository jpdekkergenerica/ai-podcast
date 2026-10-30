import React from "react";

/** 6px pixel indicator. LED mode adds a 4px glow (via --led-glow); pending → stepped blink. */
export function SignalDot({ tone = "info", pending, size = 6, label, style }) {
  const c = "var(--" + tone + "-signal)";
  return <span role={label ? "img" : undefined} aria-label={label} aria-hidden={label ? undefined : true} style={{ display: "inline-block", width: size, height: size, flex: "none", background: tone === "warning" ? "var(--warning-fill)" : c, outline: tone === "warning" ? "1px solid var(--warning-on)" : "none", outlineOffset: 0, boxShadow: "0 0 var(--led-glow) " + c, animation: pending ? "mn-blink 1000ms steps(1, end) infinite" : "none", ...style }} />;
}
