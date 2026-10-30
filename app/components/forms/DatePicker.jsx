import React, { useState } from "react";
import { IconButton } from "../core/IconButton.jsx";
import { Chip } from "../core/Chip.jsx";

const DOW = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"];
const pad = (n) => String(n).padStart(2, "0");

/** Month grid; Monday-first (VN). Selected = inverted, today = 2px frame, future = disabled. */
export function DatePicker({ value, today = new Date(2026, 9, 14), onChange, allowFuture = false, style }) {
  const sel = value || today;
  const [view, setView] = useState(new Date(sel.getFullYear(), sel.getMonth(), 1));
  const y = view.getFullYear(), m = view.getMonth();
  const lead = (new Date(y, m, 1).getDay() + 6) % 7;
  const days = new Date(y, m + 1, 0).getDate();
  const same = (a, b) => a && b && a.toDateString() === b.toDateString();
  const cells = [...Array(lead).fill(null), ...Array.from({ length: days }, (_, i) => new Date(y, m, i + 1))];
  const yest = new Date(today); yest.setDate(today.getDate() - 1);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8, ...style }}>
      <div style={{ display: "flex", gap: 8 }}>
        <Chip selected={same(sel, today)} onClick={() => onChange && onChange(today)}>Hôm nay</Chip>
        <Chip selected={same(sel, yest)} onClick={() => onChange && onChange(yest)}>Hôm qua</Chip>
      </div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <IconButton icon="chevron-left" label="Tháng trước" onClick={() => setView(new Date(y, m - 1, 1))} />
        <span style={{ font: "var(--type-headline)" }}>Tháng {m + 1}, {y}</span>
        <IconButton icon="chevron-right" label="Tháng sau" onClick={() => setView(new Date(y, m + 1, 1))} />
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)" }}>
        {DOW.map((d) => <span key={d} style={{ height: 32, display: "flex", alignItems: "center", justifyContent: "center", font: "var(--type-caption)", color: "var(--text-secondary)" }}>{d}</span>)}
        {cells.map((d, i) => {
          if (!d) return <span key={i} />;
          const on = same(d, sel), isToday = same(d, today), future = !allowFuture && d > today;
          return (
            <button key={i} type="button" disabled={future} onClick={() => onChange && onChange(d)} aria-label={pad(d.getDate()) + "/" + pad(m + 1) + "/" + y}
              style={{ height: 44, border: isToday && !on ? "var(--border-2) solid var(--border-strong)" : "var(--border-2) solid transparent", borderRadius: 0, boxSizing: "border-box",
                background: on ? "var(--bg-inverse)" : "transparent", color: future ? "var(--text-disabled)" : on ? "var(--text-inverse)" : "var(--text-primary)",
                font: "var(--type-mono-amount)", fontWeight: on ? 600 : 400, cursor: future ? "default" : "pointer" }}>{pad(d.getDate())}</button>
          );
        })}
      </div>
    </div>
  );
}
