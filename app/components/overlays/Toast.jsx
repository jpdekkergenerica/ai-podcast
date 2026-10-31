import React from "react";
import { Icon } from "../core/Icon.jsx";
import { haptic } from "../core/motion.js";

/** Snackbar. default → inverted bar; error → outlined 2px + alert icon.
    Motion: springs up (spring/smooth, 32px). With an action, a countdown bar steps down in 10 steps over `duration`.
    Haptic: success (check) / error on show — fired by the caller; medium on "Ongedaan maken". */
export function Toast({ message, action, onAction, icon, variant = "default", duration = 3500, style }) {
  const err = variant === "error";
  return (
    <div role={err ? "alert" : "status"} style={{ position: "relative", overflow: "hidden", display: "flex", alignItems: "center", gap: 12, minHeight: 48, padding: "8px 8px 8px 12px", boxSizing: "border-box",
      background: err ? "var(--bg-elevated)" : "var(--toast-bg)", color: err ? "var(--text-primary)" : "var(--toast-fg)", borderRadius: "var(--radius-input)", boxShadow: "var(--shadow-float)", border: err ? "var(--border-2) solid var(--negative-text)" : "var(--float-border)", animation: "mn-toast-up var(--spring-smooth-dur) var(--spring-smooth) both", ...style }}>
      {(icon || err) && (err ? <span style={{ color: "var(--negative-text)", display: "inline-flex" }}><Icon name={icon || "alert"} /></span> : icon === "check" ? <span style={{ width: 24, height: 24, borderRadius: "var(--radius-full)", background: "var(--positive-fill)", color: "var(--positive-on)", display: "inline-flex", alignItems: "center", justifyContent: "center", flex: "none", animation: "mn-pop var(--spring-bouncy-dur) var(--spring-bouncy) 80ms both" }}><Icon name="check" size={20} /></span> : <Icon name={icon} />)}
      <span style={{ flex: 1, font: "var(--type-body-small)", textWrap: "pretty" }}>{message}</span>
      {action && <button type="button" data-haptic="medium" onClick={() => { haptic("medium", "Ongedaan maken"); onAction && onAction(); }} style={{ background: "none", border: "none", minHeight: 44, padding: "0 12px", borderRadius: "var(--radius-btn)", font: "var(--type-label)", color: "inherit", textDecoration: "underline", textUnderlineOffset: 4, cursor: "pointer" }}>{action}</button>}
      {action && duration > 0 && <span aria-hidden="true" style={{ position: "absolute", left: 12, right: 12, bottom: 3, height: 2, background: "currentColor", opacity: 0.6, transformOrigin: "left center", animation: "mn-countdown " + duration + "ms steps(10, end) both" }} />}
    </div>
  );
}
