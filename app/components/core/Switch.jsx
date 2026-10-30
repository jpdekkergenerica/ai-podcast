import React, { useEffect, useRef } from "react";
import { animate, haptic } from "./motion.js";

/** Toggle 44×26. Off → light gray track, white knob left (clearly off). On → ink track, white knob right.
    Motion: knob slides on spring/snappy and stretches ~8px toward its travel mid-way. Haptic: selection. */
export function Switch({ checked, onChange, disabled, label, style }) {
  const knob = useRef(null);
  const prev = useRef(checked);
  useEffect(() => {
    if (prev.current === checked) return;
    prev.current = checked;
    const k = knob.current;
    if (!k) return;
    k.style.transformOrigin = checked ? "left center" : "right center";
    animate(k, [{ transform: "scaleX(1)" }, { transform: "scaleX(1.5)", offset: 0.45 }, { transform: "scaleX(1)" }], "snappy");
  }, [checked]);
  const ease = "var(--spring-snappy-dur) var(--spring-snappy)";
  return (
    <button type="button" role="switch" aria-checked={!!checked} aria-label={label} disabled={disabled} data-haptic="selection"
      onClick={() => { haptic("selection", "Switch"); onChange && onChange(!checked); }}
      style={{ position: "relative", width: 44, height: 26, padding: 2, boxSizing: "border-box", flex: "none", border: "none", background: disabled ? "var(--bg-disabled)" : checked ? "var(--switch-on-track)" : "var(--switch-off-track)", display: "flex", cursor: disabled ? "default" : "pointer", borderRadius: "var(--radius-full)", transition: "background " + ease, ...style }}>
      <span style={{ display: "block", width: 22, height: 22, transform: "translateX(" + (checked ? 18 : 0) + "px)", transition: "transform " + ease }}>
        <span ref={knob} style={{ display: "block", width: 22, height: 22, borderRadius: "var(--radius-full)", background: checked ? "var(--switch-on-knob)" : "var(--switch-off-knob)", boxShadow: "var(--switch-knob-shadow, 0 1px 3px rgba(0,0,0,.25), 0 0 0 0.5px rgba(0,0,0,.08))", opacity: disabled ? 0.5 : 1, transition: "background " + ease }} />
      </span>
    </button>
  );
}
