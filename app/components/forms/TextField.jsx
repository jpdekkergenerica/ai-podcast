import React, { useEffect, useRef, useState } from "react";
import { Icon } from "../core/Icon.jsx";
import { animate, haptic } from "../core/motion.js";

/** Guardia text input: label boven het veld (Geist Medium 14), wit veld 48px met 1px rand en 8px radius.
    Focus: paarse ring van 2px (geen layout shift). Fout: rode rand en een korte schud (300ms). Haptic: error bij nieuwe fout. */
export function TextField({ label, value, defaultValue, onChange, placeholder, helper, error, disabled, icon, trailing, forceState, type = "text", inputMode, style }) {
  const [f, setF] = useState(false);
  const box = useRef(null);
  const prevErr = useRef(error);
  const focused = forceState === "focused" || f;
  useEffect(() => {
    if (error && error !== prevErr.current) {
      haptic("error", "Field error");
      animate(box.current, [{ transform: "none" }, { transform: "translateX(-6px)" }, { transform: "translateX(6px)" }, { transform: "translateX(-4px)" }, { transform: "translateX(4px)" }, { transform: "translateX(-2px)" }, { transform: "none" }], "linear", { duration: 300 });
    }
    prevErr.current = error;
  }, [error]);
  const ring = error ? "var(--negative-text)" : focused ? "var(--focus-ring)" : null;
  const ease = "var(--spring-snappy-dur) var(--spring-snappy)";
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 8, ...style }}>
      {label && <span style={{ font: "var(--type-label)", color: disabled ? "var(--text-disabled)" : "var(--text-primary)" }}>{label}</span>}
      <span ref={box} style={{ display: "flex", alignItems: "center", gap: 8, height: 48, padding: "0 14px", boxSizing: "border-box", borderRadius: "var(--radius-input)",
        border: "var(--border-1) solid " + (ring || "var(--border-control)"), boxShadow: ring ? "0 0 0 1px " + ring : "var(--shadow-btn-secondary)",
        background: disabled ? "var(--bg-disabled)" : "var(--bg-card)", color: disabled ? "var(--text-disabled)" : "var(--text-primary)", transition: "box-shadow " + ease + ", border-color " + ease }}>
        {icon && <span style={{ display: "inline-flex", color: "var(--text-tertiary)" }}><Icon name={icon} /></span>}
        <input type={type} inputMode={inputMode} value={value} defaultValue={defaultValue} onChange={(e) => onChange && onChange(e.target.value)} placeholder={placeholder} disabled={disabled}
          onFocus={() => setF(true)} onBlur={() => setF(false)} aria-invalid={!!error || undefined}
          style={{ flex: 1, width: "100%", minWidth: 0, border: "none", outline: "none", background: "transparent", font: "var(--type-body)", color: "inherit", padding: 0 }} />
        {trailing}
      </span>
      {error ? (
        <span role="alert" style={{ display: "flex", alignItems: "center", gap: 6, font: "var(--type-body-small)", fontWeight: 500, color: "var(--negative-text)", animation: "mn-fade-in 150ms var(--ease-fade)" }}><Icon name="alert" />{error}</span>
      ) : helper ? <span style={{ font: "var(--type-caption)", color: "var(--text-tertiary)" }}>{helper}</span> : null}
    </label>
  );
}
