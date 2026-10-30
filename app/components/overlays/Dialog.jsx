import React from "react";
import { Icon } from "../core/Icon.jsx";
import { Button } from "../core/Button.jsx";

/** Centered modal with 2px frame. destructive → warning icon, explicit verb button + "Huỷ". */
export function Dialog({ open = true, title, children, confirmLabel = "Đồng ý", cancelLabel = "Huỷ", onConfirm, onCancel, destructive, inline, loading }) {
  if (!open) return null;
  const box = (
    <div role="alertdialog" aria-label={title} style={{ width: "100%", maxWidth: 320, boxSizing: "border-box", background: "var(--bg-primary)", color: "var(--text-primary)", borderRadius: "var(--radius-xl)", boxShadow: "var(--shadow-float)", border: "var(--float-border)", padding: 24, display: "flex", flexDirection: "column", gap: 12 }}>
      {destructive && <Icon name="warning-box" filled color="var(--negative-fill)" onColor="var(--negative-on)" />}
      <span style={{ font: "var(--type-title)", letterSpacing: "var(--ls-title)", textWrap: "pretty" }}>{title}</span>
      {children && <div style={{ font: "var(--type-body)", color: "var(--text-secondary)", textWrap: "pretty" }}>{children}</div>}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginTop: 8 }}>
        <Button variant="secondary" onClick={onCancel}>{cancelLabel}</Button>
        <Button variant={destructive ? "destructive" : "primary"} onClick={onConfirm} loading={loading}>{confirmLabel}</Button>
      </div>
    </div>
  );
  if (inline) return box;
  return (
    <div style={{ position: "absolute", inset: 0, zIndex: 30, display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div onClick={onCancel} style={{ position: "absolute", inset: 0, background: "var(--overlay)" }} />
      <div style={{ position: "relative", width: "100%", display: "flex", justifyContent: "center" }}>{box}</div>
    </div>
  );
}
