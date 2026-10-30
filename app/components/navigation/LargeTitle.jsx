import React, { useState } from "react";
import { Icon } from "../core/Icon.jsx";
import { BottomSheet } from "../overlays/BottomSheet.jsx";
import { haptic } from "../core/motion.js";

/** Option list in a bottom sheet — for > 5 options or rarely changed choices (rule 3). Rows separated by hairlines, check on the selected one. */
export function OptionSheet({ title, options = [], value, onSelect, onClose }) {
  return (
    <BottomSheet title={title} onClose={onClose}>
      <div style={{ margin: "0 -16px", paddingBottom: 16 }}>
        {options.map((o, i) => {
          const on = o.value === value;
          return (
            <button key={o.value} type="button" data-haptic="selection" onClick={() => { haptic("selection", "Option"); onSelect && onSelect(o.value); }}
              style={{ display: "flex", alignItems: "center", gap: 12, width: "100%", minHeight: 52, padding: "0 16px", background: "none", border: "none", borderTop: i ? "var(--border-1) solid var(--border-subtle)" : "none", color: "var(--text-primary)", textAlign: "left", cursor: "pointer" }}>
              {o.icon && <Icon name={o.icon} />}
              <span style={{ flex: 1, display: "flex", flexDirection: "column" }}><span style={{ font: on ? "600 16px/22px var(--font-sans)" : "var(--type-body)" }}>{o.label}</span>{o.meta && <span style={{ font: "var(--type-mono-small)", color: "var(--text-secondary)" }}>{o.meta}</span>}</span>
              {on && <Icon name="check" />}
            </button>
          );
        })}
      </div>
    </BottomSheet>
  );
}

/** L1 · Scope menu: text + chevron under the large title (e.g. "Tất cả ví ▾"). Opens a sheet/menu. Data scope lives here, never in tabs. */
export function ScopeMenu({ label, onClick, style }) {
  return (
    <button type="button" onClick={onClick} data-haptic="light" aria-haspopup="dialog"
      style={{ display: "inline-flex", alignItems: "center", gap: 2, height: 32, padding: 0, background: "none", border: "none", color: "var(--text-primary)", font: "500 15px/20px var(--font-sans)", cursor: "pointer", alignSelf: "flex-start", ...style }}>
      {label}<span style={{ display: "inline-flex", color: "var(--text-secondary)" }}><Icon name="chevron-down" size={18} /></span>
    </button>
  );
}

/** L1 · Large title (Geist 28px) at the top of a screen's scroll content. The nav bar shows the small title as this scrolls away (useCollapse in the UI kit).
    scope → a ScopeMenu or PeriodStepper node under the title. */
export function LargeTitle({ title, subtitle, scope, style }) {
  return (
    <div style={{ padding: "2px 16px 12px", display: "flex", flexDirection: "column", gap: 4, flex: "none", ...style }}>
      <h1 style={{ margin: 0, font: "600 28px/34px var(--font-sans)", letterSpacing: "-0.02em", color: "var(--text-primary)", textWrap: "balance" }}>{title}</h1>
      {subtitle && <span style={{ font: "var(--type-body-small)", color: "var(--text-secondary)" }}>{subtitle}</span>}
      {scope}
    </div>
  );
}

export const PERIOD_TYPES = ["Tuần", "Tháng", "Quý", "Năm", "Tuỳ chọn"];

/** L3a · Period stepper pill "‹ Tháng 10 ›". Arrows step the period; tapping the centre opens a sheet (Tuần · Tháng · Quý · Năm · Tuỳ chọn).
    Haptic: selection on step, light on open. */
export function PeriodStepper({ label, type = "Tháng", types = PERIOD_TYPES, onPrev, onNext, onType, style }) {
  const [open, setOpen] = useState(false);
  const arrow = (icon, fn, aria) => (
    <button type="button" aria-label={aria} disabled={!fn} data-haptic="selection" onClick={() => { haptic("selection", "Period step"); fn && fn(); }}
      style={{ width: 36, height: 36, display: "inline-flex", alignItems: "center", justifyContent: "center", border: "none", background: "none", borderRadius: "var(--radius-full)", color: fn ? "var(--text-primary)" : "var(--text-disabled)", cursor: fn ? "pointer" : "default", padding: 0 }}><Icon name={icon} size={20} /></button>
  );
  return (
    <>
      <div style={{ display: "inline-flex", alignItems: "center", height: 36, border: "var(--border-1) solid var(--border-control)", borderRadius: "var(--radius-full)", alignSelf: "flex-start", flex: "none", ...style }}>
        {arrow("chevron-left", onPrev, "Kỳ trước")}
        <button type="button" onClick={() => { haptic("light", "Period sheet"); setOpen(true); }} aria-haspopup="dialog"
          style={{ height: 36, padding: "0 4px", minWidth: 88, border: "none", background: "none", color: "var(--text-primary)", font: "600 14px/20px var(--font-sans)", cursor: "pointer", whiteSpace: "nowrap" }}>{label}</button>
        {arrow("chevron-right", onNext, "Kỳ sau")}
      </div>
      {open && <OptionSheet title="Khoảng thời gian" value={type} options={types.map((t) => ({ value: t, label: t, icon: t === "Tuỳ chọn" ? "calendar" : undefined }))} onSelect={(t) => { setOpen(false); onType && onType(t); }} onClose={() => setOpen(false)} />}
    </>
  );
}
