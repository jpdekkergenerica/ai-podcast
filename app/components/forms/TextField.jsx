import React, { useEffect, useRef, useState } from "react";
import { Icon } from "../core/Icon.jsx";
import { animate, haptic } from "../core/motion.js";

/** Text field with floating label (56px when labelled, 48px otherwise).
    Motion: focus thickens the border 1→2px (inset ring, no layout shift) and floats the label up on spring/snappy.
    An error shakes the field 3 beats (300ms) with a red border. Haptic: error on new error. */
export function TextField({ label, value, defaultValue, onChange, placeholder, helper, error, disabled, icon, trailing, forceState, type = "text", inputMode, style }) {
  const [f, setF] = useState(false);
  const [inner, setInner] = useState(defaultValue || "");
  const box = useRef(null);
  const prevErr = useRef(error);
  const focused = forceState === "focused" || f;
  const thick = focused || !!error;
  const has = String(value != null ? value : inner).length > 0;
  const floated = !label || focused || has || forceState === "filled";
  useEffect(() => {
    if (error && error !== prevErr.current) {
      haptic("error", "Field error");
      animate(box.current, [{ transform: "none" }, { transform: "translateX(-6px)" }, { transform: "translateX(6px)" }, { transform: "translateX(-4px)" }, { transform: "translateX(4px)" }, { transform: "translateX(-2px)" }, { transform: "none" }], "linear", { duration: 300 });
    }
    prevErr.current = error;
  }, [error]);
  const color = disabled ? "var(--border-default)" : error ? "var(--negative-text)" : focused ? "var(--focus-ring)" : "var(--border-control)";
  const ease = "var(--spring-snappy-dur) var(--spring-snappy)";
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 6, ...style }}>
      <span ref={box} style={{ position: "relative", display: "flex", alignItems: "center", gap: 8, height: label ? 56 : 48, padding: "0 12px", boxSizing: "border-box", borderRadius: "var(--radius-sm)",
        border: "none", boxShadow: thick ? "inset 0 0 0 1.5px " + color : "inset 0 0 0 0 " + color, borderRadius: 12,
        background: disabled ? "var(--bg-disabled)" : "var(--bg-secondary)", color: disabled ? "var(--text-disabled)" : "var(--text-primary)", transition: "box-shadow " + ease + ", border-color " + ease }}>
        {icon && <span style={{ display: "inline-flex", color: "var(--text-secondary)" }}><Icon name={icon} /></span>}
        <span style={{ position: "relative", flex: 1, minWidth: 0, alignSelf: "stretch", display: "flex", alignItems: label ? "flex-end" : "center", paddingBottom: label ? 8 : 0 }}>
          {label && <span style={{ position: "absolute", left: 0, top: "50%", font: "var(--type-body)", color: disabled ? "var(--text-disabled)" : error ? "var(--negative-text)" : floated ? "var(--text-secondary)" : "var(--text-tertiary)", transformOrigin: "left center", pointerEvents: "none", whiteSpace: "nowrap",
            transform: floated ? "translateY(-21px) scale(0.75)" : "translateY(-50%)", fontWeight: floated ? 500 : 400, transition: "transform " + ease + ", color " + ease }}>{label}</span>}
          <input type={type} inputMode={inputMode} value={value} defaultValue={defaultValue} onChange={(e) => { setInner(e.target.value); onChange && onChange(e.target.value); }} placeholder={floated ? placeholder : ""} disabled={disabled}
            onFocus={() => setF(true)} onBlur={() => setF(false)} aria-invalid={!!error || undefined}
            style={{ width: "100%", minWidth: 0, border: "none", outline: "none", background: "transparent", font: "var(--type-body)", color: "inherit", padding: 0 }} />
        </span>
        {trailing}
      </span>
      {error ? (
        <span role="alert" style={{ display: "flex", alignItems: "center", gap: 6, font: "var(--type-body-small)", fontWeight: 500, color: "var(--negative-text)", animation: "mn-fade-in 150ms var(--ease-fade)" }}><Icon name="alert" />{error}</span>
      ) : helper ? <span style={{ font: "var(--type-caption)", color: "var(--text-secondary)" }}>{helper}</span> : null}
    </label>
  );
}
