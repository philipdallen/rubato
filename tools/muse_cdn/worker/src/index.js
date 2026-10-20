/**
 * rubato-samples-cdn — token-gated Cloudflare Worker serving CC-licensed
 * sample libraries from an R2 bucket.
 *
 * Routes (all require auth; the worker fails closed without CDN_TOKEN):
 *   GET /                    corpus browser console (HTML)
 *   GET /manifest.json       library index (sha256 per file)
 *   GET /libs/<lib>/<path>   file bytes, Range-aware (206 partial content)
 *   HEAD /libs/<lib>/<path>  headers only
 *   GET /workbench/*         static seed-workbench site (coaching UI) from R2
 *   GET /audio/* /explorer/* /boardroom/* /index.html
 *                            companion QA surfaces from R2
 *
 * Auth: `Authorization: Bearer <CDN_TOKEN>` header, `?token=` query param,
 * or the `rubato_token` cookie (set on any ?token= visit, so the static
 * site's plain fetch() and <audio> calls stay authenticated).
 * Presented tokens are compared in constant time (SHA-256 both sides, then a
 * fixed-length byte compare) so comparison timing cannot leak the secret one
 * byte at a time.
 * If the CDN_TOKEN secret is not set, the worker refuses everything (fail
 * closed) rather than serving samples to the open internet.
 *
 * LICENSE BOUNDARY: this bucket must only ever hold CC0 / CC-licensed
 * content (VSCO 2 CE, Sonatina SSO). Spitfire libraries (BBCSO Discover,
 * SSO Discover, paid tiers) must NEVER be uploaded here — their EULA
 * forbids redistribution and reformatting for another sampler.
 */

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

function bearerToken(request) {
  const h = request.headers.get("Authorization");
  if (h && /^bearer /i.test(h)) return { token: h.slice(7).trim(), via: "header" };
  const u = new URL(request.url);
  const q = u.searchParams.get("token");
  if (q) return { token: q, via: "query" };
  // Cookie set by an earlier ?token= visit, so the static site's plain
  // fetch() and <audio> calls stay authenticated without page changes.
  const cookie = request.headers.get("Cookie") || "";
  const m = /(?:^|;\s*)rubato_token=([^;]+)/.exec(cookie);
  if (m) {
    try { return { token: decodeURIComponent(m[1]), via: "cookie" }; }
    catch { return { token: null, via: null }; }
  }
  return { token: null, via: null };
}

/**
 * Constant-time token comparison. Hashing both sides to a fixed 32-byte
 * digest removes the length difference, so the byte loop below always runs
 * the same number of iterations and no early exit leaks the prefix length.
 * A missing presented token is hashed as the empty string, which still
 * yields a well-defined (mismatching) digest.
 */
async function tokenMatches(presented, expected) {
  const enc = new TextEncoder();
  const [a, b] = await Promise.all([
    crypto.subtle.digest("SHA-256", enc.encode(presented ?? "")),
    crypto.subtle.digest("SHA-256", enc.encode(expected)),
  ]);
  const x = new Uint8Array(a);
  const y = new Uint8Array(b);
  let diff = 0;
  for (let i = 0; i < x.length; i++) diff |= x[i] ^ y[i];
  return diff === 0;
}

/**
 * Parse a single `Range: bytes=...` header into an R2 range option.
 * Returns { offset, length } | { offset } | { suffix } | null (unsatisfiable).
 */
function parseRange(header, size) {
  // Single ranges only. A multi-range header (e.g. `bytes=0-1,5-6`) or any
  // malformed value falls through to null -> 416; clients that need multiple
  // ranges can issue separate requests.
  const m = /^bytes=(\d*)-(\d*)$/.exec(header.trim());
  if (!m) return null;
  const [, startS, endS] = m;
  if (startS === "" && endS === "") return null;
  if (startS === "") {
    // suffix range: last N bytes
    const suffix = parseInt(endS, 10);
    if (!(suffix > 0)) return null;
    return { suffix: Math.min(suffix, size) };
  }
  const offset = parseInt(startS, 10);
  if (offset >= size) return null;
  if (endS === "") return { offset };
  const end = parseInt(endS, 10);
  if (end < offset) return null;
  return { offset, length: Math.min(end, size - 1) - offset + 1 };
}

const CONSOLE_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>rubato sample corpus</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin: 0; font: 14px/1.45 system-ui, -apple-system, sans-serif;
         background: #111; color: #ddd; }
  header { padding: 12px 16px; background: #1a1a1a; border-bottom: 1px solid #333;
           display: flex; gap: 16px; align-items: center; flex-wrap: wrap;
           position: sticky; top: 0; z-index: 5; }
  header h1 { font-size: 16px; margin: 0; font-weight: 600; }
  header h1 span { color: #888; font-weight: 400; font-size: 12px; }
  .tabs button { background: #222; color: #ccc; border: 1px solid #444;
                 padding: 6px 12px; cursor: pointer; border-radius: 4px; }
  .tabs button.active { background: #2d4a2d; border-color: #5a8a5a; color: #fff; }
  #search { background: #222; border: 1px solid #444; color: #eee;
            padding: 6px 10px; border-radius: 4px; width: 260px; }
  #layout { display: flex; height: calc(100vh - 57px); }
  #tree { width: 320px; min-width: 220px; overflow: auto; border-right: 1px solid #333;
          padding: 8px; background: #151515; }
  #tree details { margin-left: 12px; }
  #tree summary { cursor: pointer; padding: 2px 4px; border-radius: 3px;
                  white-space: nowrap; }
  #tree summary:hover, #tree .dir.active > summary { background: #2a2a2a; }
  #files { flex: 1; overflow: auto; padding: 8px 16px; }
  #crumb { color: #888; font-size: 12px; margin: 4px 0 8px; }
  table { border-collapse: collapse; width: 100%; }
  th { text-align: left; color: #888; font-weight: 400; font-size: 12px;
       padding: 4px 8px; border-bottom: 1px solid #333; }
  td { padding: 4px 8px; border-bottom: 1px solid #222; }
  tr.file { cursor: pointer; }
  tr.file:hover td { background: #1e2a1e; }
  tr.file.playing td { background: #243524; }
  .size { color: #888; text-align: right; white-space: nowrap; }
  #playerbar { position: sticky; bottom: 0; background: #1a1a1a;
               border-top: 1px solid #333; padding: 8px 16px;
               display: none; align-items: center; gap: 12px; }
  #playerbar.show { display: flex; }
  #playerbar audio { flex: 1; height: 32px; }
  #playerbar .name { font-size: 12px; color: #aaa; max-width: 40%;
                     overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  #preview { position: fixed; inset: 10% 15%; background: #1a1a1a;
             border: 1px solid #555; border-radius: 6px; padding: 16px;
             display: none; flex-direction: column; z-index: 10; }
  #preview.show { display: flex; }
  #preview pre { overflow: auto; flex: 1; background: #111; padding: 12px;
                 border-radius: 4px; font-size: 12px; }
  #preview button { align-self: flex-end; }
  #tokenform { position: fixed; inset: 0; background: rgba(0,0,0,.85);
               display: none; align-items: center; justify-content: center; z-index: 20; }
  #tokenform.show { display: flex; }
  #tokenform div { background: #1c1c1c; padding: 24px; border-radius: 8px;
                   border: 1px solid #444; }
  #tokenform input { width: 320px; padding: 8px; margin: 8px 0; }
  .meta { font-size: 12px; color: #777; }
</style>
</head>
<body>
<header>
  <h1>rubato sample corpus <span id="counts"></span></h1>
  <div class="tabs" id="tabs"></div>
  <input id="search" type="search" placeholder="filter files in this folder…">
</header>
<div id="layout">
  <nav id="tree"></nav>
  <main id="files">
    <div id="crumb"></div>
    <table><thead><tr><th>file</th><th style="text-align:right">size</th></tr></thead>
    <tbody id="rows"></tbody></table>
  </main>
</div>
<div id="playerbar"><span class="name" id="pname"></span><audio id="audio" controls preload="none"></audio></div>
<div id="preview"><button id="previewclose">close</button><pre id="previewbody"></pre></div>
<div id="tokenform"><div>
  <h3 style="margin-top:0">corpus token</h3>
  <p class="meta">This console is token-gated like the rest of the CDN.<br>
  Paste the CDN_TOKEN once; it stays in this tab's session storage.</p>
  <input id="tokeninput" type="password" placeholder="CDN_TOKEN"><br>
  <button id="tokensubmit">unlock</button>
</div></div>
<script>
"use strict";
const qs = new URLSearchParams(location.search);
let token = qs.get("token") || sessionStorage.getItem("rubato_cdn_token") || "";
const tokenForm = document.getElementById("tokenform");
if (!token) tokenForm.classList.add("show");
document.getElementById("tokensubmit").onclick = () => {
  token = document.getElementById("tokeninput").value.trim();
  if (!token) return;
  sessionStorage.setItem("rubato_cdn_token", token);
  tokenForm.classList.remove("show");
  boot();
};
const authHeaders = () => ({ "Authorization": "Bearer " + token });
const esc = (s) => s.replace(/[&<>"']/g, (c) =>
  ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmtSize = (n) => n > 1048576 ? (n/1048576).toFixed(1)+" MB"
  : n > 1024 ? (n/1024).toFixed(1)+" KB" : n+" B";
const isAudio = (p) => /\\.(wav|aif|aiff|mp3|ogg|flac)$/i.test(p);
const isText = (p) => /\\.(sfz|txt|md|xml|json)$/i.test(p);

let manifest = null, curLib = null, curDir = "", dirIndex = {};

async function boot() {
  const r = await fetch("manifest.json", { headers: authHeaders() });
  if (r.status === 401) {
    sessionStorage.removeItem("rubato_cdn_token"); token = "";
    tokenForm.classList.add("show"); return;
  }
  if (!r.ok) { document.getElementById("crumb").textContent = "manifest fetch failed: "+r.status; return; }
  manifest = await r.json();
  const libs = Object.keys(manifest.libraries || {});
  const tabs = document.getElementById("tabs");
  tabs.innerHTML = "";
  let totalFiles = 0, totalBytes = 0;
  for (const lib of libs) {
    const info = manifest.libraries[lib];
    totalFiles += info.file_count || 0; totalBytes += info.bytes || 0;
    const b = document.createElement("button");
    b.textContent = lib;
    b.onclick = () => selectLib(lib);
    b.dataset.lib = lib;
    tabs.appendChild(b);
  }
  document.getElementById("counts").textContent =
    totalFiles.toLocaleString()+" files · "+(totalBytes/1073741824).toFixed(2)+" GB";
  if (libs.length) selectLib(libs[0]);
}

function buildIndex(lib) {
  // dir path -> { subdirs: Set, files: [{name, size, path}] }
  const idx = { "": { subdirs: new Set(), files: [] } };
  const files = (manifest.libraries[lib].files || []);
  for (const f of files) {
    const rel = f.path.replace("libs/"+lib+"/", "");
    const parts = rel.split("/");
    const name = parts.pop();
    let d = "";
    for (const p of parts) {
      const parent = d;
      d = d ? d+"/"+p : p;
      if (!idx[d]) idx[d] = { subdirs: new Set(), files: [] };
      idx[parent].subdirs.add(p);
    }
    idx[d].files.push({ name, size: f.size, path: f.path });
  }
  for (const d of Object.values(idx)) {
    d.files.sort((a,b) => a.name.localeCompare(b.name));
    d.subdirs = [...d.subdirs].sort();
  }
  return idx;
}

function selectLib(lib) {
  curLib = lib; curDir = "";
  document.querySelectorAll("#tabs button").forEach(b =>
    b.classList.toggle("active", b.dataset.lib === lib));
  dirIndex = buildIndex(lib);
  renderTree(); renderFiles();
}

function renderTree() {
  const nav = document.getElementById("tree");
  nav.innerHTML = "";
  const mk = (dir, label) => {
    const det = document.createElement("details");
    det.open = true;
    const sum = document.createElement("summary");
    sum.textContent = label;
    sum.onclick = (e) => { e.preventDefault(); curDir = dir; renderFiles(); markActive(); };
    det.appendChild(sum);
    const wrap = document.createElement("div");
    wrap.className = "dir"; wrap.dataset.dir = dir;
    det.appendChild(wrap);
    for (const sub of dirIndex[dir].subdirs) {
      wrap.appendChild(mk(dir ? dir+"/"+sub : sub, sub));
    }
    return det;
  };
  nav.appendChild(mk("", "(root)"));
  markActive();
}
function markActive() {
  document.querySelectorAll("#tree .dir").forEach(el =>
    el.classList.toggle("active", el.dataset.dir === curDir));
}

function renderFiles() {
  const q = document.getElementById("search").value.trim().toLowerCase();
  document.getElementById("crumb").textContent =
    curLib + (curDir ? " / " + curDir : "") + " — " +
    dirIndex[curDir].files.length + " files";
  const tb = document.getElementById("rows");
  tb.innerHTML = "";
  for (const f of dirIndex[curDir].files) {
    if (q && !f.name.toLowerCase().includes(q)) continue;
    const tr = document.createElement("tr");
    tr.className = "file";
    const icon = isAudio(f.name) ? "♪ " : isText(f.name) ? "≣ " : "· ";
    tr.innerHTML = "<td>"+esc(icon+f.name)+"</td>"+
      '<td class="size">'+fmtSize(f.size)+"</td>";
    tr.onclick = () => openFile(f, tr);
    tb.appendChild(tr);
  }
}
document.getElementById("search").addEventListener("input", renderFiles);

function fileURL(f) {
  return "/" + f.path.split("/").map(encodeURIComponent).join("/") +
    "?token=" + encodeURIComponent(token);
}

function openFile(f, tr) {
  document.querySelectorAll("tr.file.playing").forEach(el => el.classList.remove("playing"));
  if (isAudio(f.name)) {
    tr.classList.add("playing");
    const bar = document.getElementById("playerbar");
    bar.classList.add("show");
    document.getElementById("pname").textContent = f.name;
    const a = document.getElementById("audio");
    a.src = fileURL(f);
    a.play().catch(()=>{});
  } else if (isText(f.name) && f.size < 200*1024) {
    fetch(fileURL(f), { headers: { ...authHeaders(), "Range": "bytes=0-8191" } })
      .then(r => r.text()).then(t => {
        document.getElementById("previewbody").textContent = t;
        document.getElementById("preview").classList.add("show");
      });
  } else {
    const a = document.createElement("a");
    a.href = fileURL(f); a.download = f.name;
    document.body.appendChild(a); a.click(); a.remove();
  }
}
document.getElementById("previewclose").onclick = () =>
  document.getElementById("preview").classList.remove("show");

if (token) boot();
</script>
</body>
</html>`;

const SITE_PREFIXES = {
  "/workbench/": "site/workbench/",
  "/audio/": "site/audio/",
  "/explorer/": "site/explorer/",
  "/boardroom/": "site/boardroom/",
};

function contentTypeFor(key) {
  const dot = key.lastIndexOf(".");
  const ext = dot === -1 ? "" : key.slice(dot).toLowerCase();
  return {
    ".html": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".yaml": "text/yaml; charset=utf-8",
    ".yml": "text/yaml; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".mjs": "application/javascript; charset=utf-8",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
  }[ext] || "application/octet-stream";
}

export default {
  async fetch(request, env) {
    // Fail closed if the secret was never set.
    if (!env.CDN_TOKEN) {
      return json({ error: "cdn token not configured" }, 503);
    }
    const presented = bearerToken(request);
    if (!(await tokenMatches(presented.token, env.CDN_TOKEN))) {
      return json({ error: "unauthorized" }, 401);
    }
    // Authenticated via ?token=: drop a cookie so the static site's plain
    // fetch() and <audio> calls stay authenticated for the session.
    let setCookie = null;
    if (presented.via === "query" && presented.token) {
      setCookie = `rubato_token=${encodeURIComponent(presented.token)}; Path=/; Max-Age=86400; SameSite=Lax; HttpOnly`;
    }

    const url = new URL(request.url);
    const path = url.pathname;

    // Corpus browser console for humans.
    if (path === "/") {
      if (request.method !== "GET" && request.method !== "HEAD") {
        return json({ error: "method not allowed" }, 405);
      }
      const headers = new Headers({
        "Content-Type": "text/html; charset=utf-8",
        "Cache-Control": "no-store",
      });
      if (request.method === "HEAD") {
        headers.set("Content-Length", String(new TextEncoder().encode(CONSOLE_HTML).length));
        return new Response(null, { headers });
      }
      return new Response(CONSOLE_HTML, { headers });
    }

    if (path === "/manifest.json") {
      if (request.method !== "GET" && request.method !== "HEAD") {
        return json({ error: "method not allowed" }, 405);
      }
      const obj = await env.SAMPLES.get("manifest.json");
      if (!obj) return json({ error: "manifest not uploaded yet" }, 404);
      const headers = new Headers();
      obj.writeHttpMetadata(headers);
      headers.set("Content-Type", "application/json; charset=utf-8");
      headers.set("Cache-Control", "public, max-age=300");
      if (request.method === "HEAD") {
        headers.set("Content-Length", String(obj.size));
        return new Response(null, { headers });
      }
      return new Response(obj.body, { headers });
    }

    // Static QA site (workbench, explorer, boardroom) + audio, served from
    // R2 under site/. The workbench page is the seed-coaching interface:
    // seed/probe/growth/audio panels plus the Rehearse pane (directive
    // dry-run/commit). The Rehearse pane POSTs to /api/run, which needs the
    // Python runner (tools/muse_workbench_runner) — not available on Workers —
    // so it degrades to its "runner unreachable" note; everything else works.
    {
      let siteKey = null;
      if (path === "/index.html") {
        siteKey = "site/index.html";
      } else {
        for (const [prefix, r2prefix] of Object.entries(SITE_PREFIXES)) {
          if (path.startsWith(prefix)) {
            let rest = path.slice(prefix.length);
            try { rest = decodeURIComponent(rest); }
            catch { return json({ error: "bad path encoding" }, 400); }
            if (rest === "" || rest.endsWith("/")) rest += "index.html";
            if (rest.includes("..")) return json({ error: "not found" }, 404);
            siteKey = r2prefix + rest;
            break;
          }
        }
      }
      if (siteKey) {
        if (request.method !== "GET" && request.method !== "HEAD") {
          return json({ error: "method not allowed" }, 405);
        }
        const obj = await env.SAMPLES.get(siteKey);
        if (!obj) return json({ error: "not found" }, 404);
        const headers = new Headers();
        headers.set("Content-Type", contentTypeFor(siteKey));
        headers.set("Cache-Control", "public, max-age=300");
        if (setCookie) headers.set("Set-Cookie", setCookie);
        if (request.method === "HEAD") {
          headers.set("Content-Length", String(obj.size));
          return new Response(null, { headers });
        }
        return new Response(obj.body, { headers });
      }
    }

    const m = /^\/libs\/([A-Za-z0-9._-]+)\/(.+)$/.exec(path);
    if (!m) return json({ error: "not found" }, 404);
    let rest;
    try {
      // pathname arrives percent-encoded; R2 keys are stored decoded.
      rest = decodeURIComponent(m[2]);
    } catch {
      return json({ error: "bad path encoding" }, 400);
    }
    const key = `libs/${m[1]}/${rest}`;

    if (request.method === "HEAD") {
      const head = await env.SAMPLES.head(key);
      if (!head) return json({ error: "not found" }, 404);
      const headers = new Headers();
      head.writeHttpMetadata(headers);
      headers.set("Accept-Ranges", "bytes");
      headers.set("Cache-Control", "public, max-age=31536000, immutable");
      headers.set("Content-Length", String(head.size));
      return new Response(null, { headers });
    }

    if (request.method !== "GET") {
      return json({ error: "method not allowed" }, 405);
    }

    let range;
    const rangeHeader = request.headers.get("Range");
    if (rangeHeader) {
      // Need the size first to validate the range.
      const head = await env.SAMPLES.head(key);
      if (!head) return json({ error: "not found" }, 404);
      range = parseRange(rangeHeader, head.size);
      if (!range) return new Response("Range Not Satisfiable", { status: 416 });
    }

    const obj = await env.SAMPLES.get(key, range ? { range } : undefined);
    if (!obj) return json({ error: "not found" }, 404);

    const headers = new Headers();
    obj.writeHttpMetadata(headers);
    headers.set("Accept-Ranges", "bytes");
    headers.set("Cache-Control", "public, max-age=31536000, immutable");

    if (range && obj.range) {
      const start = obj.range.offset;
      const end = start + obj.range.length - 1;
      headers.set("Content-Range", `bytes ${start}-${end}/${obj.size}`);
      return new Response(obj.body, { status: 206, headers });
    }
    return new Response(obj.body, { headers });
  },
};
