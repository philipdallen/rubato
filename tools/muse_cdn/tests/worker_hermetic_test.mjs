// Hermetic worker suite — exercises tools/muse_cdn/worker/src/index.js against
// a local `wrangler dev` (workerd) instance with a local R2 binding.
//
// No CDN_TOKEN, no network, no deployed endpoint: the test token is a literal
// passed via `--var`, and the R2 bucket is a throwaway --persist-to directory
// seeded from fixtures built here. This is the fast-tier counterpart to
// worker_test.mjs, which needs the live URL and the real secret.
//
// Usage:  node worker_hermetic_test.mjs
//   WRANGLER_BIN  path to the wrangler CLI (default: `wrangler` on PATH)
//
// Prints `N passed, M failed` and exits nonzero on any failure.
import { createHash } from "node:crypto";
import { spawn, spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const WORKER_DIR = join(HERE, "..", "worker");
const WRANGLER = process.env.WRANGLER_BIN || "wrangler";
const TOKEN = "hermetic-test-token"; // never the real secret
const BUCKET = "rubato-samples";
const PORT = 8799 + (process.pid % 100);

let pass = 0,
  fail = 0;
const check = (name, cond) => {
  console.log((cond ? "PASS" : "FAIL") + " " + name);
  cond ? pass++ : fail++;
};

// --- fixtures -------------------------------------------------------------
// A deterministic payload long enough that a 0-99 range is a strict prefix.
const bytes = Buffer.alloc(300);
for (let i = 0; i < bytes.length; i++) bytes[i] = (i * 7 + 3) & 0xff;
const sha = createHash("sha256").update(bytes).digest("hex");
const SPACED_NAME = "samples/my file.wav";
const PLAIN_NAME = "samples/hello.wav";

const manifest = {
  libraries: {
    "demo-lib": {
      files: [
        { path: `libs/demo-lib/${PLAIN_NAME}`, sha256: sha, size: bytes.length },
        { path: `libs/demo-lib/${SPACED_NAME}`, sha256: sha, size: bytes.length },
      ],
    },
  },
};

const stateDir = mkdtempSync(join(tmpdir(), "muse-cdn-hermetic-"));
const fixtureDir = join(stateDir, "fixtures");
mkdirSync(join(fixtureDir, "samples"), { recursive: true });
writeFileSync(join(fixtureDir, "manifest.json"), JSON.stringify(manifest));
writeFileSync(join(fixtureDir, "hello.wav"), bytes);

const wranglerEnv = {
  ...process.env,
  WRANGLER_SEND_METRICS: "false",
  NO_COLOR: "1",
  CI: "1", // never prompt interactively
};
const wranglerArgs = (rest) => rest;

function seed(key, file) {
  const r = spawnSync(
    WRANGLER,
    wranglerArgs([
      "r2", "object", "put", `${BUCKET}/${key}`,
      "--file", file, "--local", "--persist-to", stateDir,
    ]),
    { cwd: WORKER_DIR, env: wranglerEnv, encoding: "utf8", timeout: 90_000 },
  );
  if (r.status !== 0) {
    throw new Error(`seed ${key} failed (${r.status}): ${r.stderr || r.stdout}`);
  }
}

// --- start wrangler dev ---------------------------------------------------
seed("manifest.json", join(fixtureDir, "manifest.json"));
seed(`libs/demo-lib/${PLAIN_NAME}`, join(fixtureDir, "hello.wav"));
seed(`libs/demo-lib/${SPACED_NAME}`, join(fixtureDir, "hello.wav"));

const server = spawn(
  WRANGLER,
  wranglerArgs([
    "dev", "--local", "--port", String(PORT),
    "--persist-to", stateDir,
    "--var", `CDN_TOKEN:${TOKEN}`,
  ]),
  { cwd: WORKER_DIR, env: wranglerEnv, stdio: ["ignore", "pipe", "pipe"] },
);
let serverLog = "";
server.stdout.on("data", (d) => (serverLog += d));
server.stderr.on("data", (d) => (serverLog += d));

const root = `http://127.0.0.1:${PORT}`;
const auth = { Authorization: "Bearer " + TOKEN };
const url = (p) => root + "/" + p.split("/").map(encodeURIComponent).join("/");
const get = (p, opts = {}) =>
  fetch(url(p), { headers: { ...auth, ...(opts.headers || {}) }, method: opts.method || "GET" });

async function waitReady() {
  for (let i = 0; i < 120; i++) {
    try {
      await fetch(root + "/manifest.json", { headers: auth });
      return;
    } catch {
      await new Promise((r) => setTimeout(r, 500));
    }
  }
  throw new Error("wrangler dev did not become ready:\n" + serverLog);
}

function cleanup() {
  server.kill("SIGTERM");
  try { rmSync(stateDir, { recursive: true, force: true }); } catch {}
}
process.on("exit", cleanup);

try {
  await waitReady();

  // 1-3: auth gating
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
  {
    const r = await fetch(root + "/manifest.json", { headers: auth });
    check("correct-token manifest -> 200", r.status === 200);
    await r.arrayBuffer().catch(() => {});
  }

  // 4-5: manifest shape
  {
    const r = await get("manifest.json");
    const m = await r.json();
    const files = m.libraries?.["demo-lib"]?.files;
    check("manifest libraries[lib].files is an array", Array.isArray(files));
    check(
      "manifest entries carry sha256",
      Array.isArray(files) && files.length > 0 && files.every((f) => typeof f.sha256 === "string"),
    );
  }

  // 6: file fetch + sha256 match
  {
    const r = await get(`libs/demo-lib/${PLAIN_NAME}`);
    const buf = Buffer.from(await r.arrayBuffer());
    check("file fetch -> 200", r.status === 200);
    check("file sha256 matches fixture", createHash("sha256").update(buf).digest("hex") === sha);
  }

  // 7: Range -> 206 with Content-Range
  {
    const r = await get(`libs/demo-lib/${PLAIN_NAME}`, { headers: { Range: "bytes=0-99" } });
    check("Range: bytes=0-99 -> 206", r.status === 206);
    check(
      "Content-Range: bytes 0-99/<size>",
      r.headers.get("content-range") === `bytes 0-99/${bytes.length}`,
    );
    await r.arrayBuffer().catch(() => {});
  }

  // 8: plain GET -> 200 (regression: worker once returned 206)
  {
    const r = await get(`libs/demo-lib/${PLAIN_NAME}`);
    check("plain GET -> 200 not 206", r.status === 200);
    await r.arrayBuffer().catch(() => {});
  }

  // 9: HEAD -> 200 with Content-Length
  {
    const r = await get(`libs/demo-lib/${PLAIN_NAME}`, { method: "HEAD" });
    check("HEAD -> 200", r.status === 200);
    check("HEAD Content-Length", r.headers.get("content-length") === String(bytes.length));
  }

  // 10: percent-encoded path -> 200 (regression: worker once 404'd)
  {
    const r = await get(`libs/demo-lib/${SPACED_NAME}`);
    check("percent-encoded path -> 200", r.status === 200);
    await r.arrayBuffer().catch(() => {});
  }

  // 11: manifest route method gate -> 405 on POST
  {
    const r = await fetch(root + "/manifest.json", { method: "POST", headers: auth });
    check("POST /manifest.json -> 405", r.status === 405);
    await r.arrayBuffer().catch(() => {});
  }
} catch (e) {
  console.error("hermetic suite error:", e.message);
  fail++;
} finally {
  cleanup();
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
