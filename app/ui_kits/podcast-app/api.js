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
    const msg = (data && (data.detail || data.message || data.error)) || res.statusText;
    const err = new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    err.status = res.status;
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
  getShow: () => req("/me/show"),
  createShow: (body) => req("/me/show", { method: "POST", body: JSON.stringify(body) }),
  updateShow: (body) => req("/me/show", { method: "PATCH", body: JSON.stringify(body) }),
  rotateToken: () => req("/me/show/rotate-feed-token", { method: "POST", body: "{}" }),
  feedTest: (topic, lookback_hours = 72) =>
    req("/me/feed-test", { method: "POST", body: JSON.stringify({ ...topic, lookback_hours }) }),
  build: (max_minutes) =>
    req("/me/build", { method: "POST", body: JSON.stringify({ max_minutes: max_minutes ?? null }) }),
  jobs: () => req("/me/jobs"),
  deleteAccount: () => req("/me/account", { method: "DELETE" }),
};

/** Sign in with Apple via de iOS-host (WKScriptMessageHandler "appleSignIn"). Null buiten de app. */
export const hasNativeApple = () => !!(window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.appleSignIn);

export function nativeAppleSignIn() {
  return new Promise((resolve, reject) => {
    window.__appleSignInResult = (res) => (res && res.identityToken ? resolve(res) : reject(new Error((res && res.error) || "Apple-login geannuleerd")));
    window.webkit.messageHandlers.appleSignIn.postMessage({});
  });
}
