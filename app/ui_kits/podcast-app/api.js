/** API-client voor de config-app. Zet window.PODCAST_API_BASE of valt terug op localhost. */

const BASE = () => (typeof window !== "undefined" && window.PODCAST_API_BASE) || "http://127.0.0.1:8000";

function token() {
  return localStorage.getItem("pp_token") || "";
}

export function setToken(t) {
  if (t) localStorage.setItem("pp_token", t);
  else localStorage.removeItem("pp_token");
}

export function getToken() {
  return token();
}

async function req(path, opts = {}) {
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  const t = token();
  if (t) headers.Authorization = `Bearer ${t}`;
  const res = await fetch(BASE() + path, { ...opts, headers });
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = { detail: text }; }
  if (!res.ok) {
    const detail = data && (data.detail || data.message || data.error);
    const fields = detail && typeof detail === "object" && !Array.isArray(detail) ? detail.fields : null;
    const msg = fields ? detail.message : detail || res.statusText;
    const err = new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    err.status = res.status;
    err.fields = fields; // {veld: melding}, zodat het formulier fouten bij het juiste veld toont
    throw err;
  }
  return data;
}

export const api = {
  health: () => req("/health"),
  devLogin: (apple_sub = "dev-user", email = "dev@example.com") =>
    req("/auth/dev", { method: "POST", body: JSON.stringify({ apple_sub, email }) }),
  appleLogin: (identity_token, email) =>
    req("/auth/apple", { method: "POST", body: JSON.stringify({ identity_token, email }) }),
  me: () => req("/me"),
  setNotifications: (prefs) => req("/me/notifications", { method: "PATCH", body: JSON.stringify(prefs) }),
  registerDevice: (token) => req("/me/devices", { method: "POST", body: JSON.stringify({ token }) }),
  deleteAccount: () => req("/me/account", { method: "DELETE" }),
  podcasts: () => req("/me/podcasts"),
  podcast: (id) => req(`/me/podcasts/${id}`),
  createPodcast: (body) => req("/me/podcasts", { method: "POST", body: JSON.stringify(body) }),
  updatePodcast: (id, body) => req(`/me/podcasts/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deletePodcast: (id) => req(`/me/podcasts/${id}`, { method: "DELETE" }),
  pausePodcast: (id) => req(`/me/podcasts/${id}/pause`, { method: "POST", body: "{}" }),
  resumePodcast: (id) => req(`/me/podcasts/${id}/resume`, { method: "POST", body: "{}" }),
  rotateFeedToken: (id) => req(`/me/podcasts/${id}/rotate-feed-token`, { method: "POST", body: "{}" }),
  setCover: (id, image) => req(`/me/podcasts/${id}/cover`, { method: "POST", body: JSON.stringify({ image }) }),
  deleteCover: (id) => req(`/me/podcasts/${id}/cover`, { method: "DELETE" }),
  episodes: (id) => req(`/me/podcasts/${id}/episodes`),
  episode: (id, guid) => req(`/me/podcasts/${id}/episodes/${encodeURIComponent(guid)}`),
  voices: (q = "") => req(`/me/voices?q=${encodeURIComponent(q)}`),
  checkSource: (url) => req("/me/sources/check", { method: "POST", body: JSON.stringify({ url }) }),
};

/** Sign in with Apple via de iOS-host (WKScriptMessageHandler "appleSignIn"). Null buiten de app. */
export const hasNativeApple = () => !!(window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.appleSignIn);

export function nativeAppleSignIn() {
  return new Promise((resolve, reject) => {
    window.__appleSignInResult = (res) => (res && res.identityToken ? resolve(res) : reject(new Error((res && res.error) || "Apple-login geannuleerd")));
    window.webkit.messageHandlers.appleSignIn.postMessage({});
  });
}

/** Pushmeldingen via de iOS-host (handler "push"). Buiten de app: status "unsupported". */
export const hasNativePush = () => !!(window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.push);

function pushCall(action) {
  if (!hasNativePush()) return Promise.resolve({ status: "unsupported" });
  return new Promise((resolve) => {
    const timer = setTimeout(() => resolve({ status: "unknown" }), 8000);
    window.__pushResult = (res) => { clearTimeout(timer); resolve(res || { status: "unknown" }); };
    window.webkit.messageHandlers.push.postMessage({ action });
  });
}
export const pushStatus = () => pushCall("status"); // {status: authorized | denied | notDetermined | unsupported, token?}
export const pushRegister = () => pushCall("register"); // vraagt toestemming en geeft {status, token}
