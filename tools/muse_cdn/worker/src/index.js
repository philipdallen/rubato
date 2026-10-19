/**
 * rubato-samples-cdn — token-gated Cloudflare Worker serving CC-licensed
 * sample libraries from an R2 bucket.
 *
 * Routes:
 *   GET /manifest.json        library index (sha256 per file)
 *   GET /libs/<lib>/<path>    file bytes, Range-aware (206 partial content)
 *   HEAD /libs/<lib>/<path>   headers only
 *
 * Auth: `Authorization: Bearer <CDN_TOKEN>` header or `?token=` query param.
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
  if (h && /^bearer /i.test(h)) return h.slice(7).trim();
  const u = new URL(request.url);
  return u.searchParams.get("token");
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

export default {
  async fetch(request, env) {
    // Fail closed if the secret was never set.
    if (!env.CDN_TOKEN) {
      return json({ error: "cdn token not configured" }, 503);
    }
    if (bearerToken(request) !== env.CDN_TOKEN) {
      return json({ error: "unauthorized" }, 401);
    }

    const url = new URL(request.url);
    const path = url.pathname;

    if (path === "/" || path === "/manifest.json") {
      if (request.method !== "GET" && request.method !== "HEAD") {
        return json({ error: "method not allowed" }, 405);
      }
      const obj = await env.SAMPLES.get("manifest.json");
      if (!obj) return json({ error: "manifest not uploaded yet" }, 404);
      const headers = new Headers();
      obj.writeHttpMetadata(headers);
      headers.set("Content-Type", "application/json; charset=utf-8");
      headers.set("Cache-Control", "public, max-age=300");
      return new Response(obj.body, { headers });
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
