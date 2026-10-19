// Worker test harness — verifies the deployed worker against its contract.
// Usage:  node worker_test.mjs <base_url> <token>
//
// Checks (17):
//   auth gating: no token -> 401, wrong token -> 401
//   manifest: 200, both libraries present, sha256 on entries
//   per library: file 200 + sha256 match (2 libraries x 2)
//   Range: 206 + correct Content-Range
//   plain GET -> 200 (regression: worker once returned 206)
//   HEAD -> 200 + Content-Length
//   percent-encoded path -> 200 (regression: worker once 404'd)
//
// Requires node >= 18 (global fetch) and the worker's CDN_TOKEN.
import { createHash } from "crypto";

const [base, token] = process.argv.slice(2);
if (!base || !token) {
  console.error("usage: node worker_test.mjs <base_url> <token>");
  process.exit(2);
}
const root = base.replace(/\/+$/, "");
const auth = { Authorization: "Bearer " + token };

let pass = 0, fail = 0;
const check = (name, cond) => {
  console.log((cond ? "PASS" : "FAIL") + " " + name);
  cond ? pass++ : fail++;
};

// Manifest entry paths are R2 keys of the form `libs/<lib>/<rel>`; the worker
// serves them verbatim at /libs/<lib>/<rel>. Build the URL from the path.
const url = (p) => root + "/" + p.split("/").map(encodeURIComponent).join("/");
const get = (p, opts = {}) =>
  fetch(url(p), { headers: { ...auth, ...(opts.headers || {}) }, method: opts.method || "GET" });

// 1-2: auth gating
{
  const r = await fetch(root + "/manifest.json");
  check("no-token manifest -> 401", r.status === 401);
  await r.arrayBuffer().catch(() => {});
}
{
  const r = await fetch(root + "/manifest.json", { headers: { Authorization: "Bearer wrong" } });
  check("wrong-token manifest -> 401", r.status === 401);
  await r.arrayBuffer().catch(() => {});
}

// 3-6: manifest 200, both libraries, sha256 fields
let firstSonatina = null, firstVsco = null;
{
  const r = await get("manifest.json");
  check("authed manifest -> 200", r.status === 200);
  const manifest = await r.json();
  const libs = manifest.libraries || {};
  check("manifest has sonatina-sso", Array.isArray(libs["sonatina-sso"]?.files));
  check("manifest has vsco2-ce", Array.isArray(libs["vsco2-ce"]?.files));
  firstSonatina = libs["sonatina-sso"]?.files.find((f) => f.sha256 && f.path.endsWith(".wav"));
  firstVsco = libs["vsco2-ce"]?.files.find((f) => f.sha256 && f.path.endsWith(".wav"));
  check("sonatina manifest entries have sha256", !!firstSonatina);
  check("vsco2-ce manifest entries have sha256", !!firstVsco);
}

// 7-10: file fetch + sha256 match, both libraries
for (const [lib, entry] of [["sonatina-sso", firstSonatina], ["vsco2-ce", firstVsco]]) {
  if (!entry) { check(`${lib} file 200`, false); check(`${lib} sha256 matches manifest`, false); continue; }
  const r = await get(entry.path);
  const buf = Buffer.from(await r.arrayBuffer());
  const sha = createHash("sha256").update(buf).digest("hex");
  check(`${lib} file 200`, r.status === 200);
  check(`${lib} sha256 matches manifest`, sha === entry.sha256);
}

// 11-12: Range request -> 206 with correct Content-Range
{
  const entry = firstVsco;
  const r = await get(entry.path, { headers: { Range: "bytes=0-99" } });
  check("range request -> 206", r.status === 206);
  const cr = r.headers.get("content-range");
  check("content-range header correct", cr === `bytes 0-99/${entry.size}`);
  await r.arrayBuffer().catch(() => {});
}

// 13: plain GET -> 200 (regression: worker once returned 206 on plain GETs)
{
  const r = await get(firstSonatina.path);
  check("plain GET -> 200 not 206", r.status === 200);
  await r.arrayBuffer().catch(() => {});
}

// 14-15: HEAD -> 200 with content-length
{
  const r = await get(firstVsco.path, { method: "HEAD" });
  check("HEAD -> 200", r.status === 200);
  check("HEAD has content-length", r.headers.get("content-length") === String(firstVsco.size));
}

// 16: percent-encoded path -> 200 (regression: worker once 404'd on encoded paths)
// `url()` above already percent-encodes each segment.
{
  const r = await get(firstVsco.path);
  check("encoded path -> 200 not 404", r.status === 200);
  await r.arrayBuffer().catch(() => {});
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
