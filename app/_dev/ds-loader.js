/* Preview helper for cards & UI kits.
   Uses the compiled bundle when present; otherwise transpiles the component sources in-browser.
   Usage: MonseyReady(["components/core/Button.jsx", ...]).then(NS => ...) */
(function () {
  var here = document.currentScript.src;
  var ROOT = here.replace(/_dev\/ds-loader\.js.*$/, "");
  var cache = {};
  function norm(p) {
    var out = [];
    p.split("/").forEach(function (s) { if (s === "..") out.pop(); else if (s !== "." && s !== "") out.push(s); });
    return out.join("/");
  }
  function dir(p) { return p.slice(0, p.lastIndexOf("/") + 1); }
  async function load(path) {
    if (cache[path]) return cache[path];
    cache[path] = (async function () {
      var src = await (await fetch(ROOT + path, { cache: "no-cache" })).text();
      var code = Babel.transform(src, { presets: ["react"], plugins: ["transform-modules-commonjs"], filename: path }).code;
      var deps = [];
      code.replace(/require\("([^"]+)"\)/g, function (_, d) { if (d[0] === ".") deps.push(d); });
      var mods = {};
      var got = await Promise.all(deps.map(function (d) { return load(norm(dir(path) + d)); }));
      deps.forEach(function (d, i) { mods[d] = got[i]; });
      var module = { exports: {} };
      var req = function (d) { if (d === "react") return window.React; if (d === "react-dom") return window.ReactDOM; return mods[d]; };
      new Function("require", "module", "exports", "React", code)(req, module, module.exports, window.React);
      return module.exports;
    })();
    return cache[path];
  }
  function findBundle() {
    var keys = Object.keys(window);
    for (var i = 0; i < keys.length; i++) {
      try { var v = window[keys[i]]; if (v && typeof v === "object" && v.Button && v.Icon && v.TransactionRow) return v; } catch (e) {}
    }
    return null;
  }
  window.addEventListener("unhandledrejection", function (e) { console.error("[Monsey preview]", e.reason && (e.reason.stack || e.reason.message || e.reason)); });
  /* Always load from source (UI kit screens that import components relatively). */
  window.MonseyLoad = async function (files) {
    var NS = {};
    (await Promise.all(files.map(load))).forEach(function (m) { Object.assign(NS, m); });
    return NS;
  };
  window.MonseyReady = async function (files) {
    var b = findBundle();
    if (b) return b;
    var NS = {};
    (await Promise.all(files.map(load))).forEach(function (m) { Object.assign(NS, m); });
    return NS;
  };
})();
