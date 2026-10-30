import React, { useLayoutEffect, useRef, useState } from "react";
import { haptic } from "./motion.js";

/** L2 · Primary views within a screen. Text tabs, 2px sliding underline, no container (hairline only).
    Geist 15px; selected = 600 primary, others secondary. Scrolls horizontally when > 4. Haptic: selection. */
export function Tabs({ tabs = [], value, onChange, style }) {
  const refs = useRef({});
  const wrap = useRef(null);
  const [bar, setBar] = useState(null);
  const [anim, setAnim] = useState(false);
  useLayoutEffect(() => {
    const el = refs.current[value], w = wrap.current;
    if (!el || !w) return;
    setBar((b) => { if (b) setAnim(true); return { x: el.offsetLeft, w: el.offsetWidth }; });
    if (w.scrollWidth > w.clientWidth) w.scrollTo({ left: Math.max(0, el.offsetLeft - 16), behavior: "smooth" });
  }, [value, tabs.length]);
  return (
    <div ref={wrap} role="tablist" style={{ position: "relative", display: "flex", gap: 20, padding: "0 16px", borderBottom: "var(--border-1) solid var(--border-default)", overflowX: "auto", scrollbarWidth: "none", flex: "none", ...style }}>
      {tabs.map((t) => {
        const tab = typeof t === "string" ? { value: t, label: t } : t;
        const on = tab.value === value;
        return (
          <button key={tab.value} ref={(n) => { refs.current[tab.value] = n; }} role="tab" aria-selected={on} type="button" data-haptic="selection"
            onClick={() => { if (!on) haptic("selection", "Tab L2"); onChange && onChange(tab.value); }}
            style={{ height: 44, padding: 0, background: "none", border: "none", color: on ? "var(--text-primary)" : "var(--text-secondary)", font: (on ? "600" : "500") + " 15px/20px var(--font-sans)", letterSpacing: "-0.005em", cursor: "pointer", whiteSpace: "nowrap", display: "inline-flex", alignItems: "center", gap: 6, flex: "none", transition: "color var(--spring-snappy-dur) var(--spring-snappy)" }}>
            {tab.label}
            {tab.count != null && <span style={{ font: "var(--type-mono-small)", color: "var(--text-tertiary)" }}>{tab.count}</span>}
          </button>
        );
      })}
      {bar && <span aria-hidden="true" style={{ position: "absolute", left: 0, bottom: -1, height: 2, width: bar.w, background: "var(--text-primary)", transform: "translateX(" + bar.x + "px)", transition: anim ? "transform var(--spring-smooth-dur) var(--spring-snappy), width var(--spring-smooth-dur) var(--spring-snappy)" : "none" }} />}
    </div>
  );
}
