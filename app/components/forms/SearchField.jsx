import React from "react";
import { Icon } from "../core/Icon.jsx";

/** 44px search input with clear button. */
export function SearchField({ value = "", onChange, placeholder = "Tìm giao dịch, ghi chú, số tiền", onCancel, style }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, ...style }}>
      <label style={{ flex: 1, display: "flex", alignItems: "center", gap: 8, height: 44, padding: "0 4px 0 12px", background: "var(--bg-secondary)", border: "var(--border-1) solid var(--border-control)", borderRadius: "var(--radius-full)", boxSizing: "border-box" }}>
        <span style={{ display: "inline-flex", color: "var(--text-secondary)" }}><Icon name="search" /></span>
        <input value={value} onChange={(e) => onChange && onChange(e.target.value)} placeholder={placeholder} aria-label="Tìm kiếm"
          style={{ flex: 1, minWidth: 0, border: "none", outline: "none", background: "transparent", font: "var(--type-body)", color: "var(--text-primary)", padding: 0 }} />
        {value && <button type="button" aria-label="Xoá" onClick={() => onChange && onChange("")} style={{ width: 36, height: 36, display: "inline-flex", alignItems: "center", justifyContent: "center", background: "none", border: "none", borderRadius: "var(--radius-full)", color: "var(--text-primary)", cursor: "pointer" }}><Icon name="close" /></button>}
      </label>
      {onCancel && <button type="button" onClick={onCancel} style={{ background: "none", border: "none", font: "var(--type-label)", color: "var(--text-primary)", minHeight: 44, cursor: "pointer" }}>Huỷ</button>}
    </div>
  );
}
