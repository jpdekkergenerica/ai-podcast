import React, { useLayoutEffect, useEffect, useRef, useState } from "react";
import { IconButton } from "../core/IconButton.jsx";
import { animate, haptic, reduced } from "../core/motion.js";

const DISMISS = 110;

/** Sheet anchored to the bottom of the device frame (portals into [data-mn-overlay]). inline → in-flow, for docs.
    Motion: enters on spring/smooth; the grabber/header follows the finger, rubber-bands when pulled up (0.25×), dismisses past 110px or on a flick.
    While open the screen underneath scales to --sheet-under-scale (0.96) and dims, iOS-modal style; both track drag progress.
    Haptic: light on dismiss, selection when the drag crosses the dismiss threshold. demoDy forces a drag offset for docs. */
export function BottomSheet({ open = true, title, onClose, children, footer, inline, demoDy, bare, dismiss, style }) {
  const anchor = useRef(null);
  const sheet = useRef(null);
  const scrim = useRef(null);
  const [host, setHost] = useState(undefined);
  const [dyS, setDy] = useState(0);
  const [drag, setDrag] = useState(false);
  const start = useRef(null);
  const past = useRef(false);
  const dy = demoDy != null ? demoDy : dyS;

  useLayoutEffect(() => {
    if (inline) return;
    const f = anchor.current && anchor.current.closest("[data-mn-frame]");
    setHost((f && f.querySelector("[data-mn-overlay]")) || null);
  }, [inline]);

  const content = () => { const f = host && host.closest("[data-mn-frame]"); return f && f.querySelector("[data-mn-content]"); };
  useLayoutEffect(() => {
    if (!host || !open) return;
    animate(sheet.current, [{ transform: "translateY(100%)" }, { transform: "translateY(0)" }], "smooth", { fade: "in" });
    if (scrim.current) scrim.current.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 200, easing: "cubic-bezier(0.2,0,0,1)" });
    const c = content();
    if (c) { c.style.transition = "transform var(--spring-smooth-dur) var(--spring-smooth), border-radius var(--spring-smooth-dur) var(--spring-smooth)"; c.style.transformOrigin = "50% 0"; }
    return () => { const c2 = content(); if (c2) { c2.style.transform = ""; c2.style.borderRadius = ""; } };
  }, [host, open]);
  useEffect(() => {
    const c = content();
    if (!c || !open) return;
    const k = parseFloat(getComputedStyle(c).getPropertyValue("--sheet-under-scale")) || 1;
    const h = (sheet.current && sheet.current.offsetHeight) || 400;
    const p = Math.max(0, Math.min(1, 1 - Math.max(0, dy) / h));
    c.style.transition = drag ? "none" : "transform var(--spring-smooth-dur) var(--spring-smooth), border-radius var(--spring-smooth-dur) var(--spring-smooth)";
    c.style.transform = k < 1 ? "translateY(" + 10 * p + "px) scale(" + (1 - (1 - k) * p) + ")" : "";
    c.style.borderRadius = k < 1 ? 16 * p + "px" : "";
    if (scrim.current) scrim.current.style.opacity = String(p);
  }, [dy, drag, host, open]);

  const close = () => {
    haptic("light", "Sheet dismiss");
    const s = sheet.current;
    if (!s || !host) { onClose && onClose(); return; }
    const c = content(); if (c) { c.style.transform = ""; c.style.borderRadius = ""; }
    const a = reduced(s) ? s.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 150, fill: "forwards" }) : s.animate([{ transform: "translateY(" + Math.max(0, dy) + "px)" }, { transform: "translateY(100%)" }], { duration: 250, easing: "cubic-bezier(0.3,0,0.8,0.15)", fill: "forwards" });
    if (scrim.current) scrim.current.animate([{ opacity: scrim.current.style.opacity || 1 }, { opacity: 0 }], { duration: 250, fill: "forwards" });
    a.onfinish = () => onClose && onClose();
  };
  useEffect(() => { if (dismiss && host) close(); }, [dismiss, host]);
  const down = (e) => { start.current = { y: e.clientY, t: performance.now() }; setDrag(true); e.currentTarget.setPointerCapture && e.currentTarget.setPointerCapture(e.pointerId); };
  const move = (e) => {
    if (!start.current) return;
    const d = e.clientY - start.current.y;
    const v = d < 0 ? d * 0.25 : d;
    const p = v > DISMISS;
    if (p !== past.current) { past.current = p; haptic("selection", "Sheet threshold"); }
    setDy(v);
  };
  const up = (e) => {
    if (!start.current) return;
    const vel = (e.clientY - start.current.y) / Math.max(1, performance.now() - start.current.t);
    start.current = null; setDrag(false); past.current = false;
    if ((dy > DISMISS || vel > 0.6) && onClose) close(); else setDy(0);
  };

  if (!open) return null;
  const grab = { onPointerDown: down, onPointerMove: move, onPointerUp: up, onPointerCancel: up, style: { touchAction: "none", cursor: "grab" } };
  const body = (
    <div ref={sheet} role="dialog" aria-modal={!inline} aria-label={title} style={{ position: "relative", background: "var(--bg-primary)", color: "var(--text-primary)", borderRadius: "var(--radius-xl) var(--radius-xl) 0 0", boxShadow: "var(--shadow-float)", borderTop: "var(--float-border)", display: "flex", flexDirection: "column", maxHeight: inline ? undefined : "88%", pointerEvents: "auto",
      transform: dy ? "translateY(" + dy + "px)" : undefined, transition: drag ? "none" : "transform var(--spring-smooth-dur) var(--spring-smooth)", ...style }}>
      {!inline && <span aria-hidden="true" style={{ position: "absolute", left: 0, right: 0, top: "100%", height: 240, background: "var(--bg-primary)" }} />}
      <div {...(inline ? {} : grab)} style={{ ...(inline ? {} : grab.style) }}>
        <div style={{ display: "flex", justifyContent: "center", paddingTop: 8, paddingBottom: title ? 0 : 8 }}><span style={{ width: 36, height: 5, borderRadius: "var(--radius-full)", background: "var(--border-control)" }} /></div>
        {title && !bare && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "4px 4px 4px 16px" }}>
            <span style={{ font: "var(--type-title)", letterSpacing: "var(--ls-title)" }}>{title}</span>
            {onClose && <span onPointerDown={(e) => e.stopPropagation()}><IconButton icon="close" label="Đóng" onClick={inline ? onClose : close} /></span>}
          </div>
        )}
      </div>
      {bare ? <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column", position: "relative", overflow: "hidden" }}>{children}</div> : <div style={{ padding: "0 16px", overflowY: "auto", flex: 1, scrollbarWidth: "none" }}>{children}</div>}
      {footer && <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 8 }}>{footer}</div>}
    </div>
  );
  if (inline) return body;
  const layer = (
    <div style={{ position: "absolute", inset: 0, zIndex: 20, display: "flex", flexDirection: "column", justifyContent: "flex-end", pointerEvents: "auto" }}>
      <div ref={scrim} onClick={close} style={{ position: "absolute", inset: 0, background: "var(--overlay)" }} />
      <div style={{ position: "relative", display: "flex", flexDirection: "column", justifyContent: "flex-end", height: "100%", pointerEvents: "none" }}>{body}</div>
    </div>
  );
  if (host === undefined) return <span ref={anchor} style={{ display: "none" }} />;
  if (host === null) return <><span ref={anchor} style={{ display: "none" }} />{layer}</>;
  return <><span ref={anchor} style={{ display: "none" }} />{window.ReactDOM.createPortal(layer, host)}</>;
}
