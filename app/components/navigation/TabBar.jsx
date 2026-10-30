import React, { useLayoutEffect, useRef, useState } from "react";
import { LINE_ICONS } from "../core/icons-line.js";
import { haptic } from "../core/motion.js";

export const DEFAULT_TABS = [
  { value: "home", label: "Tổng quan", icon: "dashboard" },
  { value: "analysis", label: "Phân tích", icon: "chart-bar" },
  { value: "plan", label: "Kế hoạch", icon: "calendar-month" },
  { value: "assets", label: "Tài sản", icon: "buildings" },
];

const HOLD_MS = 450;

/** Line icon that fills when active (outline → filled), one-beat bounce on change. */
function TabIcon({ name, on }) {
  return React.createElement("svg", {
    viewBox: "0 0 24 24", width: 24, height: 24, fill: on ? "currentColor" : "none", stroke: "currentColor", strokeWidth: on ? 1.75 : 1.5, strokeLinecap: "round", strokeLinejoin: "round", "aria-hidden": true,
    style: { display: "block", transition: "fill 120ms var(--ease-fade)" },
    dangerouslySetInnerHTML: { __html: LINE_ICONS[name] || "" },
  });
}

/** Icon-only floating pill: 4 tabs + centre ⊕. Active = filled icon + 4px dot that slides between tabs. Long-press a tab → tooltip with its name; aria-label keeps the name for screen readers.
    Motion: dot slides on spring/snappy; the new icon fills and bounces one beat. Haptic: selection.
    ⊕: tap → onCenter(el) (morphs into the camera). Press-and-hold grows to --hold-scale with an expanding ring; after 450ms the "+" morphs into a mic → onVoice(el) on release. Haptic: light on press, medium when voice starts.
    centerState ("press" | "voice") forces the hold visuals for docs. */
export function TabBar({ tabs = DEFAULT_TABS, value = "home", onChange, onCenter, onVoice, centerLabel = "Ghi", centerPressed, centerState, style }) {
  const half = Math.ceil(tabs.length / 2);
  const nav = useRef(null);
  const slots = useRef({});
  const circle = useRef(null);
  const timer = useRef(null);
  const [pill, setPill] = useState(null);
  const [anim, setAnim] = useState(false);
  const [bump, setBump] = useState(0);
  const [hold, setHold] = useState("idle");
  const prev = useRef(value);
  useLayoutEffect(() => {
    const s = slots.current[value], n = nav.current;
    if (!s || !n) { setPill(null); return; }
    const a = s.getBoundingClientRect(), b = n.getBoundingClientRect();
    const z = b.width / n.offsetWidth || 1;
    setPill({ x: (a.left - b.left) / z, y: (a.top - b.top) / z });
    if (prev.current !== value) { setAnim(true); setBump((x) => x + 1); prev.current = value; }
  }, [value]);
  const hs = centerState || hold;
  const down = (e) => {
    if (e.button && e.button !== 0) return;
    setHold("press"); haptic("light", "⊕ press");
    clearTimeout(timer.current);
    timer.current = setTimeout(() => { setHold("voice"); haptic("medium", "⊕ voice start"); }, HOLD_MS);
  };
  const up = () => {
    clearTimeout(timer.current);
    const h = hold; setHold("idle");
    if (h === "voice") (onVoice || onCenter) && (onVoice || onCenter)(circle.current);
    else if (h === "press") onCenter && onCenter(circle.current);
  };
  const cancel = () => { clearTimeout(timer.current); setHold("idle"); };
  const ease = "var(--spring-snappy-dur) var(--spring-snappy)";
  const [tip, setTip] = useState(null);
  const tipTimer = useRef(null);
  const tipDown = (t) => { clearTimeout(tipTimer.current); tipTimer.current = setTimeout(() => { haptic("selection", "Tab tooltip"); setTip(t.value); }, 450); };
  const tipUp = () => { clearTimeout(tipTimer.current); setTimeout(() => setTip(null), 900); };
  const Tip = ({ show, children }) => show ? <span role="tooltip" style={{ position: "absolute", bottom: "calc(100% + 10px)", left: "50%", transform: "translateX(-50%)", padding: "6px 10px", borderRadius: 9999, background: "var(--bg-inverse)", color: "var(--text-inverse)", font: "500 13px/16px var(--font-sans)", whiteSpace: "nowrap", pointerEvents: "none", animation: "mn-pop var(--spring-snappy-dur) var(--spring-snappy) both" }}>{children}</span> : null;
  const cell = (t) => {
    const on = t.value === value;
    return (
      <button key={t.value} type="button" aria-label={t.label} title={t.label} aria-current={on ? "page" : undefined} data-haptic="selection"
        onClick={() => { if (!on) haptic("selection", "Tab"); onChange && onChange(t.value); }}
        onPointerDown={() => tipDown(t)} onPointerUp={tipUp} onPointerLeave={tipUp} onContextMenu={(e) => e.preventDefault()}
        style={{ position: "relative", zIndex: 1, display: "flex", alignItems: "center", justifyContent: "center", background: "none", border: "none", cursor: "pointer", color: on ? "var(--text-primary)" : "var(--text-secondary)", padding: 0, minWidth: 0, transition: "color " + ease }}>
        <span ref={(el) => { slots.current[t.value] = el; }} style={{ width: 44, height: 44, display: "inline-flex", alignItems: "center", justifyContent: "center" }}>
          <span key={on ? "on" + bump : "off"} style={{ display: "inline-flex", animation: on && bump ? "mn-bounce-beat var(--spring-bouncy-dur) var(--spring-snappy)" : "none" }}><TabIcon name={t.icon} on={on} /></span>
        </span>
        <Tip show={tip === t.value}>{t.label}</Tip>
      </button>
    );
  };
  return (
    <nav ref={nav} aria-label="Điều hướng chính" style={{ position: "relative", display: "grid", gridTemplateColumns: onCenter ? "repeat(" + half + ",1fr) 64px repeat(" + (tabs.length - half) + ",1fr)" : "repeat(" + tabs.length + ",1fr)", height: 60, padding: "0 6px", background: "var(--bg-float)", borderRadius: 9999, boxShadow: "var(--shadow-float)", border: "var(--float-border)", margin: "0 28px 10px", flex: "none", ...style }}>
      {pill && <span aria-hidden="true" style={{ position: "absolute", left: 0, top: 0, width: 4, height: 4, borderRadius: 2, background: "var(--text-primary)", transform: "translate(" + (pill.x + 20) + "px," + (pill.y + 41) + "px)", transition: anim ? "transform var(--spring-smooth-dur) var(--spring-snappy)" : "none", zIndex: 0 }} />}
      {tabs.slice(0, onCenter ? half : tabs.length).map(cell)}
      {onCenter && (
        <button type="button" aria-label={centerLabel + " · giữ để nói"} data-haptic="light · medium (hold)"
          onPointerDown={down} onPointerUp={up} onPointerLeave={cancel} onPointerCancel={cancel} onContextMenu={(e) => e.preventDefault()}
          onClick={(e) => { if (e.detail === 0 && onCenter) onCenter(circle.current); }}
          style={{ position: "relative", zIndex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 4, border: "none", background: "none", color: "var(--text-primary)", cursor: "pointer", padding: 0, touchAction: "none", WebkitUserSelect: "none", userSelect: "none" }}>
          <span style={{ position: "relative", width: 48, height: 48, display: "inline-flex" }}>
            {hs !== "idle" && <>
              <span aria-hidden="true" style={{ position: "absolute", inset: 0, borderRadius: "var(--radius-full)", border: "2px solid var(--text-primary)", animation: "mn-ring 900ms var(--ease-fade) infinite" }} />
              <span aria-hidden="true" style={{ position: "absolute", inset: 0, borderRadius: "var(--radius-full)", border: "2px solid var(--text-primary)", animation: "mn-ring 900ms var(--ease-fade) 450ms infinite" }} />
            </>}
            <span ref={circle} data-mn-plus style={{ position: "relative", width: 48, height: 48, borderRadius: "var(--radius-full)", background: centerPressed || hs !== "idle" ? "var(--bg-inverse-pressed)" : "var(--bg-inverse)", color: "var(--text-inverse)", display: "inline-flex", alignItems: "center", justifyContent: "center",
              transform: hs !== "idle" ? "scale(var(--hold-scale))" : "scale(1)", transition: hs !== "idle" ? "transform " + HOLD_MS + "ms var(--spring-smooth)" : "transform var(--spring-bouncy-dur) var(--spring-bouncy)" }}>
              <span style={{ position: "absolute", display: "inline-flex", opacity: hs === "voice" ? 0 : 1, transform: hs === "voice" ? "rotate(90deg) scale(.4)" : "none", transition: "transform " + ease + ", opacity 120ms var(--ease-fade)" }}>
                {React.createElement("svg", { viewBox: "0 0 24 24", width: 28, height: 28, fill: "none", stroke: "currentColor", strokeWidth: 1.5, strokeLinecap: "round", "aria-hidden": true, style: { display: "block" }, dangerouslySetInnerHTML: { __html: LINE_ICONS.plus } })}
              </span>
              <span style={{ position: "absolute", display: "inline-flex", opacity: hs === "voice" ? 1 : 0, transform: hs === "voice" ? "none" : "scale(.4)", transition: "transform var(--spring-bouncy-dur) var(--spring-bouncy), opacity 120ms var(--ease-fade)" }}>
                {React.createElement("svg", { viewBox: "0 0 24 24", width: 28, height: 28, fill: "none", stroke: "currentColor", strokeWidth: 1.5, strokeLinecap: "round", "aria-hidden": true, style: { display: "block" }, dangerouslySetInnerHTML: { __html: LINE_ICONS.mic } })}
              </span>
            </span>
          </span>
          <Tip show={hs === "voice"}>Đang nghe… thả để gửi</Tip>
        </button>
      )}
      {onCenter && tabs.slice(half).map(cell)}
    </nav>
  );
}
