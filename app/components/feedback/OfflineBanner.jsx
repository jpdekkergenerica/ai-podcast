import React from "react";
import { Icon } from "../core/Icon.jsx";

/** Full-width inverted strip under the app bar while offline. */
export function OfflineBanner({ pending = 0, style }) {
  return (
    <div role="status" style={{ display: "flex", alignItems: "center", gap: 8, minHeight: 40, padding: "8px 16px", boxSizing: "border-box", background: "var(--warning-fill)", color: "var(--warning-on)", ...style }}>
      <Icon name="cellular-signal-off" />
      <span style={{ flex: 1, font: "var(--type-body-small)" }}>Đang ngoại tuyến. Giao dịch sẽ đồng bộ khi có mạng.</span>
      {pending > 0 && <span style={{ font: "var(--type-mono-small)", border: "var(--border-1) solid var(--warning-on)", padding: "0 4px" }}>{pending} chờ</span>}
    </div>
  );
}
