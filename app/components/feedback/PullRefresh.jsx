import React, { useRef, useState } from "react";
import { haptic, reduced } from "../core/motion.js";

const THRESH = 72;
const DOTS = 8;
const SCATTER = [[-14, -10], [12, -14], [16, 6], [6, 16], [-8, 14], [-16, 2], [-4, -16], [14, -4]];

/** Pixel ring: dots assemble from scatter as progress (0–1) grows, in steps; spins in steps(8) while refreshing. */
export function PixelRing({ progress = 0, spinning, size = 32, style }) {
  const r = size * 0.34;
  return (
    <span aria-hidden="true" style={{ position: "relative", display: "inline-block", width: size, height: size, animation: spinning ? "mn-spin-steps 800ms steps(8, end) infinite" : "none", ...style }}>
      {Array.from({ length: DOTS }, (_, i) => {
        const a = (i / DOTS) * Math.PI * 2 - Math.PI / 2;
        const on = spinning || progress >= (i + 1) / DOTS;
        const seen = spinning || progress > (i / DOTS) * 0.85;
        const [sx, sy] = SCATTER[i];
        const x = on ? Math.cos(a) * r : sx * 0.9, y = on ? Math.sin(a) * r : sy * 0.9;
        return <span key={i} style={{ position: "absolute", left: size / 2 - 2, top: size / 2 - 2, width: 4, height: 4, background: "var(--text-primary)", opacity: seen ? (on ? 1 - (spinning ? i * 0.09 : 0) : 0.35) : 0, transform: "translate(" + Math.round(x) + "px," + Math.round(y) + "px)", transition: "transform 120ms steps(3, end), opacity 80ms steps(2, end)" }} />;
      })}
    </span>
  );
}

/** Scroll container with pull-to-refresh. Motion: pull follows the finger at 0.5× resistance; the indicator's pixel dots assemble into a ring,
    past 72px release → ring spins (steps) → collapses on spring/smooth. Haptic: light at threshold, success when done. */
export function PullRefresh({ children, onRefresh, onScroll, scrollRef, demoPull, style }) {
  const el = useRef(null);
  const [pullS, setPull] = useState(0);
  const [busy, setBusy] = useState(false);
  const [drag, setDrag] = useState(false);
  const start = useRef(null);
  const armed = useRef(false);
  const pull = demoPull != null ? demoPull : busy ? 56 : pullS;
  const setRef = (n) => { el.current = n; if (typeof scrollRef === "function") scrollRef(n); else if (scrollRef) scrollRef.current = n; };
  const down = (e) => { if (busy || el.current.scrollTop > 0 || (e.button && e.button !== 0)) return; start.current = { y: e.clientY, cap: false }; };
  const move = (e) => {
    if (!start.current) return;
    const d = e.clientY - start.current.y;
    if (d <= 0) { if (!start.current.cap) { start.current = null; } setPull(0); return; }
    if (!start.current.cap && d > 6) { start.current.cap = true; setDrag(true); e.currentTarget.setPointerCapture && e.currentTarget.setPointerCapture(e.pointerId); }
    if (!start.current.cap) return;
    const v = Math.min(140, d * 0.5);
    const a = v >= THRESH;
    if (a !== armed.current) { armed.current = a; if (a) haptic("light", "Pull threshold"); }
    setPull(v);
  };
  const up = () => {
    if (!start.current) return;
    const wasDrag = start.current.cap; start.current = null; setDrag(false);
    if (!wasDrag) return;
    if (armed.current) {
      armed.current = false; setBusy(true);
      Promise.all([Promise.resolve(onRefresh && onRefresh()), new Promise((r) => setTimeout(r, 900))]).then(() => { haptic("success", "Refreshed"); setBusy(false); setPull(0); });
    } else setPull(0);
  };
  const rm = el.current ? reduced(el.current) : false;
  return (
    <div ref={setRef} onScroll={onScroll} onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up}
      style={{ flex: 1, overflowY: "auto", scrollbarWidth: "none", display: "flex", flexDirection: "column", position: "relative", ...style }}>
      <div aria-live="polite" style={{ height: pull, flex: "none", overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center", transition: drag || demoPull != null ? "none" : "height var(--spring-smooth-dur) var(--spring-smooth)" }}>
        <PixelRing progress={Math.min(1, pull / THRESH)} spinning={busy && !rm} />
        {busy && <span style={{ position: "absolute", width: 1, height: 1, overflow: "hidden", clip: "rect(0 0 0 0)" }}>Đang làm mới</span>}
      </div>
      {children}
    </div>
  );
}
