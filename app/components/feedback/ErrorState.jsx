import React from "react";
import { Icon } from "../core/Icon.jsx";
import { Button } from "../core/Button.jsx";

/** Block-level error: 2px frame + alert icon + explicit message + retry. */
export function ErrorState({ title = "Không tải được dữ liệu", children, action = "Thử lại", onAction, style }) {
  return (
    <div role="alert" style={{ border: "var(--border-2) solid var(--negative-text)", padding: 16, display: "flex", gap: 12, alignItems: "flex-start", background: "var(--bg-primary)", color: "var(--text-primary)", ...style }}>
      <Icon name="alert" filled color="var(--negative-fill)" onColor="var(--negative-on)" />
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ font: "var(--type-headline)" }}>{title}</span>
        {children && <span style={{ font: "var(--type-body-small)", color: "var(--text-secondary)", textWrap: "pretty" }}>{children}</span>}
        {action && <Button size="sm" variant="secondary" icon="reload" onClick={onAction} style={{ alignSelf: "flex-start", marginTop: 8 }}>{action}</Button>}
      </div>
    </div>
  );
}
