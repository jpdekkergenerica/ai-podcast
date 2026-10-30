import React from "react";
import { ICONS } from "./icons.js";
import { LINE_ICONS } from "./icons-line.js";

/** UI icons: 1.5px round line (LINE_ICONS). Pixel glyphs (ICONS) only when pixel or the name has no line version (categories, brand). filled → rounded inverted tile. */
export function Icon({ name, size = 24, filled = false, pixel = false, color, onColor, title, style }) {
  const line = !pixel && LINE_ICONS[name];
  const glyph = line || ICONS[name] || ICONS["more-horizontal"];
  const svg = React.createElement("svg", {
    viewBox: "0 0 24 24", width: size, height: size, fill: line ? "none" : "currentColor",
    stroke: line ? "currentColor" : undefined, strokeWidth: line ? 1.5 : undefined, strokeLinecap: line ? "round" : undefined, strokeLinejoin: line ? "round" : undefined,
    "aria-hidden": title ? undefined : true, role: title ? "img" : undefined,
    style: { display: "block", shapeRendering: line ? undefined : "crispEdges", flex: "none" },
    dangerouslySetInnerHTML: { __html: (title ? "<title>" + title + "</title>" : "") + glyph },
  });
  if (!filled) return <span style={{ display: "inline-flex", color: color || "currentColor", ...style }}>{svg}</span>;
  return (
    <span style={{ display: "inline-flex", width: size, height: size, flex: "none", borderRadius: Math.round(size / 3), background: color || "var(--text-primary)", color: onColor || "var(--bg-primary)", ...style }}>{svg}</span>
  );
}
