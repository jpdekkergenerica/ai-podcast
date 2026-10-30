import React from "react";
import { haptic } from "./motion.js";

/** L3b · Compact segmented control for 2–3 options on the same content. 32px, gray track, white selected segment.
    Motion: the white segment slides on spring/snappy. Haptic: selection. Not for top-level navigation, data scope or form structure. */
export function SegmentedControl({ options = [], value, onChange, size = "md", disabled, style }) {
  const n = options.length || 1;
  const idx = Math.max(0, options.findIndex((o) => (typeof o === "string" ? o : o.value) === value));
  const ease = "var(--spring-snappy-dur) var(--spring-snappy)";
  const h = size === "sm" ? 28 : 32;
  return (
    <div role="radiogroup" style={{ position: "relative", isolation: "isolate", display: "grid", gridTemplateColumns: "repeat(" + n + ", minmax(0,1fr))", height: h, padding: 2, boxSizing: "border-box", borderRadius: "var(--radius-full)", background: "var(--bg-tertiary)", ...style }}>
      <span aria-hidden="true" style={{ position: "absolute", top: 2, bottom: 2, left: 2, width: "calc((100% - 4px) / " + n + ")", zIndex: -1, borderRadius: "var(--radius-full)", background: disabled ? "var(--bg-disabled)" : "var(--bg-primary)", boxShadow: "0 1px 3px rgba(0,0,0,.12), 0 0 0 0.5px rgba(0,0,0,.06)", transform: "translateX(" + idx * 100 + "%)", transition: "transform " + ease }} />
      {options.map((o) => {
        const opt = typeof o === "string" ? { value: o, label: o } : o;
        const on = opt.value === value;
        return (
          <button key={opt.value} type="button" role="radio" aria-checked={on} disabled={disabled} data-haptic="selection"
            onClick={() => { if (!on) haptic("selection", "Segmented"); onChange && onChange(opt.value); }}
            style={{ height: "100%", padding: "0 10px", border: "none", background: "transparent", borderRadius: "var(--radius-full)",
              color: disabled ? "var(--text-disabled)" : on ? "var(--text-primary)" : "var(--text-secondary)",
              font: (on ? "600" : "500") + " 13px/16px var(--font-sans)", cursor: disabled ? "default" : "pointer", whiteSpace: "nowrap", transition: "color " + ease }}>{opt.label}</button>
        );
      })}
    </div>
  );
}
