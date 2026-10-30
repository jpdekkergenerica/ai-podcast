import React, { useRef } from "react";
import { BlockCursor } from "../ai/BlockCursor.jsx";

/** 6-cell OTP entry. Active cell 2px + block cursor; error = all cells 2px + message. */
export function OTPField({ value = "", length = 6, onChange, error, autoFocus, style }) {
  const ref = useRef(null);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8, ...style }}>
      <div onClick={() => ref.current && ref.current.focus()} style={{ position: "relative", display: "grid", gridTemplateColumns: "repeat(" + length + ", 1fr)", gap: 8 }}>
        <input ref={ref} autoFocus={autoFocus} inputMode="numeric" autoComplete="one-time-code" value={value} maxLength={length} onChange={(e) => onChange && onChange(e.target.value.replace(/\D/g, "").slice(0, length))}
          aria-label="Mã OTP" style={{ position: "absolute", inset: 0, opacity: 0, width: "100%" }} />
        {Array.from({ length }).map((_, i) => {
          const active = i === value.length;
          return (
            <span key={i} style={{ height: 56, display: "flex", alignItems: "center", justifyContent: "center", boxSizing: "border-box", border: (active || error ? "var(--border-2)" : "var(--border-1)") + " solid " + (active || error ? "var(--border-strong)" : "var(--border-control)"), font: "var(--type-display-s)" }}>
              {value[i] || (active ? <BlockCursor width={10} height={24} /> : "")}
            </span>
          );
        })}
      </div>
      {error && <span role="alert" style={{ font: "var(--type-body-small)", fontWeight: 500 }}>{error}</span>}
    </div>
  );
}
