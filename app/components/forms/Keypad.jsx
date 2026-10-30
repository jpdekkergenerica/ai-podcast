import React, { useState } from "react";
import { Icon } from "../core/Icon.jsx";
import { evalExpr } from "./AmountField.jsx";

const KEYS = [["C", "÷", "×", "back"], ["7", "8", "9", "−"], ["4", "5", "6", "+"], ["1", "2", "3", "="], ["000", "0", "done"]];

/** Reducer for keypad input. */
export function applyKey(expr, k) {
  if (k === "C") return "";
  if (k === "back") return expr.slice(0, -1);
  if (k === "=") return String(evalExpr(expr));
  if ("+−×÷".includes(k)) return !expr ? "" : /[+−×÷]$/.test(expr) ? expr.slice(0, -1) + k : expr + k;
  if ((k === "0" || k === "000") && (!expr || /[+−×÷]$/.test(expr))) return expr;
  if ((expr.match(/\d+$/) || [""])[0].length >= 12) return expr;
  return expr + k;
}

function Key({ k, onKey, span }) {
  const [down, setDown] = useState(false);
  const done = k === "done", op = "÷×−+=C".includes(k) && k.length === 1;
  const label = k === "back" ? <Icon name="arrow-left" title="Xoá" /> : done ? "Xong" : k;
  return (
    <button type="button" onClick={() => onKey && onKey(k)} onPointerDown={() => setDown(true)} onPointerUp={() => setDown(false)} onPointerLeave={() => setDown(false)}
      style={{ gridColumn: span ? "span " + span : undefined, height: 56, border: "none", borderRadius: "var(--radius-md)", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer",
        background: done ? (down ? "var(--bg-inverse-pressed)" : "var(--bg-inverse)") : down ? "var(--bg-inverse)" : op ? "var(--bg-tertiary)" : "var(--bg-secondary)",
        color: done || down ? "var(--text-inverse)" : "var(--text-primary)", font: done ? "var(--type-headline)" : "var(--type-mono-l)", fontWeight: 400 }}>
      {label}
    </button>
  );
}

/** Calculator keypad — 4 columns, 1px hairline grid. Press = inversion. */
export function Keypad({ onKey, style }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, padding: 8, ...style }}>
      {KEYS.flat().map((k) => <Key key={k} k={k} onKey={onKey} span={k === "done" ? 2 : undefined} />)}
    </div>
  );
}
