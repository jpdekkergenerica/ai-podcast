import React from "react";
import { BottomSheet } from "../overlays/BottomSheet.jsx";
import { CategoryIcon, CATEGORIES } from "../core/CategoryIcon.jsx";
import { Icon } from "../core/Icon.jsx";
import { Chip } from "../core/Chip.jsx";
import { formatMoney } from "../money/Amount.jsx";

/** Bottom-sheet picker. type="category" → 4-col tile grid; type="wallet" → rows with balance. */
export function PickerSheet({ type = "category", open = true, value, wallets = [], onSelect, onClose, inline, title }) {
  const t = title || (type === "category" ? "Chọn danh mục" : "Chọn ví");
  return (
    <BottomSheet open={open} title={t} onClose={onClose} inline={inline}>
      {type === "category" ? (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px 8px", padding: "8px 0 16px" }}>
          {Object.entries(CATEGORIES).map(([k, c]) => (
            <button key={k} type="button" onClick={() => onSelect && onSelect(k)} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, background: "none", border: "none", padding: 0, cursor: "pointer", color: "var(--text-primary)" }}>
              <CategoryIcon category={k} selected={value === k} size={48} />
              <span style={{ font: value === k ? "var(--type-label)" : "var(--type-caption)", textAlign: "center" }}>{c.label}</span>
            </button>
          ))}
        </div>
      ) : (
        <div style={{ margin: "0 -16px" }}>
          {wallets.map((w, i) => (
            <button key={w.id || i} type="button" onClick={() => onSelect && onSelect(w.id || w.name)} style={{ display: "flex", alignItems: "center", gap: 12, width: "100%", minHeight: 56, padding: "0 16px", background: "none", border: "none", borderTop: i ? "var(--border-1) solid var(--border-default)" : "none", cursor: "pointer", color: "var(--text-primary)", textAlign: "left" }}>
              <span style={{ width: 40, height: 40, display: "inline-flex", alignItems: "center", justifyContent: "center", border: "var(--border-1) solid var(--border-default)" }}><Icon name={w.icon || "wallet"} /></span>
              <span style={{ flex: 1, display: "flex", flexDirection: "column" }}>
                <span style={{ font: "var(--type-body)", fontWeight: 500, display: "inline-flex", gap: 6, alignItems: "center" }}>{w.name}{w.currency && w.currency !== "VND" && <Chip variant="code">{w.currency}</Chip>}</span>
                <span style={{ font: "var(--type-mono-small)", color: "var(--text-secondary)" }}>{formatMoney(w.balance || 0, w.currency || "VND")}</span>
              </span>
              {(value === (w.id || w.name)) && <Icon name="check" />}
            </button>
          ))}
        </div>
      )}
    </BottomSheet>
  );
}
