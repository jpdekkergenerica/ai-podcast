import React from "react";
import { Avatar } from "../core/Avatar.jsx";
import { IconButton } from "../core/IconButton.jsx";

/** Tab-root nav bar (L1): avatar (→ profile) · collapsed title · actions + notification bell.
    The large title lives in the scroll content (LargeTitle); dockProgress (0–1) fades the small title — or a docked node such as the compact balance — into the bar. */
export function AppHeader({ title, name = "Minh Anh", onAvatar, onNotifications, unread = 0, actions, docked, dockProgress = 0, style }) {
  const p = Math.max(0, Math.min(1, dockProgress));
  return (
    <header style={{ display: "grid", gridTemplateColumns: "minmax(88px,1fr) auto minmax(88px,1fr)", alignItems: "center", height: 52, padding: "0 4px", background: "var(--bg-primary)", flex: "none", ...style }}>
      <div style={{ display: "flex" }}><Avatar name={name} onClick={onAvatar} /></div>
      <div aria-hidden={p < 0.5} style={{ display: "flex", flexDirection: "column", alignItems: "center", minWidth: 0, opacity: p, transform: "translateY(" + 8 * (1 - p) + "px)", pointerEvents: p < 0.5 ? "none" : undefined }}>
        {docked || <span style={{ font: "600 16px/22px var(--font-sans)", color: "var(--text-primary)", whiteSpace: "nowrap" }}>{title}</span>}
      </div>
      <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center" }}>
        {actions}
        <span style={{ position: "relative", display: "inline-flex" }}>
          <IconButton icon="notification" label={unread ? "Thông báo, " + unread + " mới" : "Thông báo"} onClick={onNotifications} />
          {unread > 0 && <span style={{ position: "absolute", top: 6, right: 6, minWidth: 16, height: 16, padding: "0 3px", boxSizing: "border-box", background: "var(--bg-inverse)", color: "var(--text-inverse)", font: "var(--type-mono-small)", fontSize: 10, lineHeight: "16px", textAlign: "center", borderRadius: 8, boxShadow: "0 0 0 2px var(--bg-primary)", pointerEvents: "none" }}>{unread}</span>}
        </span>
      </div>
    </header>
  );
}
