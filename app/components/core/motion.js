/* Monsey motion runtime: spring tokens for WAAPI, reduce-motion check, haptic bus, shared-element store.
   CSS twins live in tokens/motion.css — keep the linear() strings identical. */

export const SPRING = {
  snappy: { dur: 250, ease: "linear(0, 0.043, 0.142, 0.266, 0.395, 0.517, 0.625, 0.716, 0.791, 0.851, 0.897, 0.931, 0.957, 0.975, 0.987, 0.995, 1, 1.003, 1.005, 1.005, 1)" },
  smooth: { dur: 350, ease: "linear(0, 0.043, 0.148, 0.283, 0.428, 0.567, 0.691, 0.795, 0.878, 0.942, 0.987, 1.017, 1.035, 1.044, 1.046, 1.044, 1.039, 1.032, 1.026, 1.019, 1.014, 1.009, 1.005, 1.002, 1)" },
  bouncy: { dur: 450, ease: "linear(0, 0.065, 0.226, 0.435, 0.652, 0.849, 1.007, 1.118, 1.182, 1.205, 1.196, 1.166, 1.124, 1.079, 1.038, 1.004, 0.979, 0.964, 0.958, 0.959, 0.965, 0.973, 0.982, 0.991, 0.998, 1.004, 1.007, 1.008, 1.009, 1.008, 1)" },
};
export const STEP = { fast: 150, base: 250, slow: 400 };

/** Haptic vocabulary → platform mapping for engineering. */
export const HAPTICS = {
  selection: { label: "Selection tick", ios: "UISelectionFeedbackGenerator.selectionChanged()", android: "HapticFeedbackConstants.CLOCK_TICK" },
  light: { label: "Light impact", ios: "UIImpactFeedbackGenerator(.light)", android: "HapticFeedbackConstants.VIRTUAL_KEY" },
  medium: { label: "Medium impact", ios: "UIImpactFeedbackGenerator(.medium)", android: "HapticFeedbackConstants.CONTEXT_CLICK" },
  heavy: { label: "Heavy sequence", ios: "UIImpactFeedbackGenerator(.heavy) ×3 · 80ms apart", android: "VibrationEffect.createWaveform([0,30,80,30,80,40])" },
  success: { label: "Success", ios: "UINotificationFeedbackGenerator(.success)", android: "HapticFeedbackConstants.CONFIRM" },
  warning: { label: "Warning", ios: "UINotificationFeedbackGenerator(.warning)", android: "HapticFeedbackConstants.GESTURE_THRESHOLD_ACTIVATE" },
  error: { label: "Error", ios: "UINotificationFeedbackGenerator(.error)", android: "HapticFeedbackConstants.REJECT" },
};

export function reduced(el) {
  try {
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return true;
    const n = el && el.closest ? el : document.documentElement;
    return !!(n.closest && n.closest("[data-reduce-motion]"));
  } catch (e) { return false; }
}

/** Fire a haptic. In the prototype it dispatches "mn-haptic" (the Shell shows a HUD). */
export function haptic(kind, label) {
  try { window.dispatchEvent(new CustomEvent("mn-haptic", { detail: { kind, label } })); } catch (e) {}
}

/** Spring-animate an element. Reduce Motion → 150ms opacity fade (dir "in" | "out" | null). */
export function animate(el, frames, kind = "smooth", opts = {}) {
  if (!el || !el.animate) return null;
  if (reduced(el)) {
    if (!opts.fade) return null;
    return el.animate(opts.fade === "out" ? [{ opacity: 1 }, { opacity: 0 }] : [{ opacity: 0 }, { opacity: 1 }], { duration: 150, easing: "cubic-bezier(0.2,0,0,1)", fill: opts.fill || "none" });
  }
  const s = SPRING[kind] || { dur: opts.duration || 250, ease: kind };
  return el.animate(frames, { duration: opts.duration || s.dur, easing: s.ease, delay: opts.delay || 0, fill: opts.fill || "none" });
}

/** Shared-element store (row → detail). */
const store = (window.__mnShared = window.__mnShared || {});
export function setShared(key, data) { store[key] = data; }
export function getShared(key) { return store[key]; }
export function clearShared(key) { delete store[key]; }

/** Rects of every [data-shared] child, relative to the device frame. */
export function sharedRects(root) {
  const frame = root.closest("[data-mn-frame]") || document.body;
  const f = frame.getBoundingClientRect();
  const z = frame.offsetWidth ? f.width / frame.offsetWidth : 1;
  const rel = (r) => ({ x: (r.left - f.left) / z, y: (r.top - f.top) / z, w: r.width / z, h: r.height / z });
  const out = { box: rel(root.getBoundingClientRect()) };
  root.querySelectorAll("[data-shared]").forEach((n) => { out[n.getAttribute("data-shared")] = rel(n.getBoundingClientRect()); });
  return out;
}
export function frameOf(el) { return el && el.closest ? el.closest("[data-mn-frame]") : null; }
export function relRect(el) {
  const frame = frameOf(el);
  const f = frame ? frame.getBoundingClientRect() : { left: 0, top: 0, width: 1 };
  const z = frame && frame.offsetWidth ? f.width / frame.offsetWidth : 1;
  const r = el.getBoundingClientRect();
  return { x: (r.left - f.left) / z, y: (r.top - f.top) / z, w: r.width / z, h: r.height / z };
}
