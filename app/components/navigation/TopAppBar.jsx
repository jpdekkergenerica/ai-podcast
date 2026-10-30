import React from "react";
import { IconButton } from "../core/IconButton.jsx";

/** L1 nav bar for pushed screens. small: centered Geist headline with back/close.
    collapse (0–1): pair with a LargeTitle in the scroll content — the small title and divider fade in as the large title scrolls away.
    large (legacy): Geist title below the bar. */
export function TopAppBar({ title, variant = "small", leading, onBack, onClose, actions, subtitle, divider = true, collapse, style }) {
  const lead = leading || (onBack ? <IconButton icon="arrow-left" label="Quay lại" onClick={onBack} /> : onClose ? <IconButton icon="close" label="Đóng" onClick={onClose} /> : null);
  const c = collapse == null ? 1 : Math.max(0, Math.min(1, collapse));
  return (
    <header style={{ background: "var(--bg-primary)", flex: "none", transition: "border-color 150ms var(--ease-fade)", ...style }}>
      <div style={{ display: "grid", gridTemplateColumns: "minmax(44px,1fr) auto minmax(44px,1fr)", alignItems: "center", height: 52, padding: "0 4px" }}>
        <div style={{ display: "flex" }}>{lead}</div>
        {variant === "small" ? <span style={{ font: "600 16px/22px var(--font-sans)", color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: 220, opacity: c, transform: "translateY(" + 6 * (1 - c) + "px)" }}>{title}</span> : <span />}
        <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center" }}>{actions}</div>
      </div>
      {variant === "large" && (
        <div style={{ padding: "0 16px 16px", display: "flex", flexDirection: "column", gap: 4 }}>
          <h1 style={{ margin: 0, font: "600 28px/34px var(--font-sans)", letterSpacing: "-0.02em", color: "var(--text-primary)" }}>{title}</h1>
          {subtitle && <span style={{ font: "var(--type-body-small)", color: "var(--text-secondary)" }}>{subtitle}</span>}
        </div>
      )}
    </header>
  );
}
