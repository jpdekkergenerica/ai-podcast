import React from "react";
import { Icon } from "./Icon.jsx";

export const CATEGORIES = {
  food: { label: "Ăn uống", icon: "coffee" },
  shopping: { label: "Mua sắm", icon: "shopping-bag" },
  housing: { label: "Nhà ở", icon: "home" },
  transport: { label: "Di chuyển", icon: "car" },
  entertainment: { label: "Giải trí", icon: "gamepad" },
  health: { label: "Sức khoẻ", icon: "heart" },
  education: { label: "Giáo dục", icon: "book-open" },
  bills: { label: "Hoá đơn", icon: "reciept" },
  income: { label: "Thu nhập", icon: "coin" },
  transfer: { label: "Chuyển khoản", icon: "arrows-horizontal" },
  savings: { label: "Tiết kiệm", icon: "bullseye-arrow" },
  other: { label: "Khác", icon: "more-horizontal" },
};

/** 40×40 soft tile (radius 12) holding a pixel category glyph. selected → inverted. */
export function CategoryIcon({ category = "other", selected = false, size = 40, style }) {
  const c = CATEGORIES[category] || CATEGORIES.other;
  return (
    <span title={c.label} style={{
      width: size, height: size, flex: "none", display: "inline-flex", alignItems: "center", justifyContent: "center",
      border: "var(--border-1) solid " + (selected ? "var(--border-strong)" : "var(--border-default)"),
      background: selected ? "var(--bg-inverse)" : "var(--bg-primary)",
      color: selected ? "var(--text-inverse)" : "var(--text-primary)", borderRadius: "var(--radius-md)", boxSizing: "border-box", ...style,
    }}>
      <Icon name={c.icon} pixel />
    </span>
  );
}
