import React from "react";
import { Icon } from "./Icon.jsx";
import { Chip } from "./Chip.jsx";

/** Settings / navigation row: icon · label (+desc) · value · trailing (chevron, switch, custom). */
export function ListRow({ icon, label, description, value, trailing, chevron = true, onClick, pro, danger, divider = true, style }) {
  const Tag = onClick ? "button" : "div";
  return (
    <Tag type={onClick ? "button" : undefined} onClick={onClick}
      style={{ display: "flex", alignItems: "center", gap: 12, width: "100%", minHeight: description ? 64 : 52, padding: "8px 16px", boxSizing: "border-box", background: "none", border: "none", borderTop: divider ? "var(--border-1) solid var(--border-default)" : "none", color: "var(--text-primary)", textAlign: "left", cursor: onClick ? "pointer" : "default", ...style }}>
      {icon && <span style={{ display: "inline-flex" }}><Icon name={icon} color={danger ? "var(--negative-text)" : undefined} /></span>}
      <span style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
        <span style={{ font: "var(--type-body)", fontWeight: danger ? 500 : 400, color: danger ? "var(--negative-text)" : undefined, display: "inline-flex", alignItems: "center", gap: 6 }}>{label}{pro && <Chip variant="code">PRO</Chip>}</span>
        {description && <span style={{ font: "var(--type-body-small)", color: "var(--text-secondary)", textWrap: "pretty", overflowWrap: "anywhere" }}>{description}</span>}
      </span>
      {value != null && <span style={{ font: "var(--type-body-small)", color: "var(--text-secondary)", whiteSpace: "nowrap" }}>{value}</span>}
      {trailing}
      {!trailing && chevron && onClick && <span style={{ display: "inline-flex", color: "var(--text-tertiary)" }}><Icon name="chevron-right" /></span>}
    </Tag>
  );
}
