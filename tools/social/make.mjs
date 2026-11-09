// Makes the videos: node tools/social/make.mjs [scene ids...] [--stills DIR] [--avatar (the profile picture only)] [--at 1,4.5 (when the stills are)]
//   [--out DIR --bitrate 4500000 (lighter copies somewhere else, e.g. for a preview page)] [--scale 0.6667 (smaller, e.g. 1280×720)]
//   [--poster 3 (only <id>-poster.webp: that moment, 1280 wide)]
// The website's demo: node tools/social/make.mjs ember-demo --scale 0.6667 --bitrate 1600000 --out web/img, then --poster 3 --out web/img
// Needs a Chrome with remote debugging on port 9333, for example:
//   chrome --headless=new --remote-debugging-port=9333 --user-data-dir=<a scratch folder>
// Serves the repo on http://localhost:8790 (the studio reads Ember's face from web/index.html), opens
// tools/social/studio.html, and writes tools/social/out/<id>.mp4 (1080×1920, or the scene's own size; 30 fps, with its sound).
// With --stills DIR it writes PNGs at the start, middle and end of each video instead, for checking.
import { createServer } from "node:http";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { join, extname, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const flag = name => { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : null; };
const OUT = flag("--out") ? resolve(flag("--out")) : join(ROOT, "tools/social/out");
const BITRATE = +(flag("--bitrate") || 0) || null;       // e.g. --bitrate 4500000 for lighter preview copies
const SCALE = +(flag("--scale") || 0) || 1;               // e.g. --scale 0.6667: the demo's 1280×720 copy for the website
const POSTER = flag("--poster");                          // e.g. --poster 3: only <id>-poster.webp, that moment, 1280 wide
const args = process.argv.slice(2), si = args.indexOf("--stills");
const stills = si >= 0 ? resolve(args[si + 1]) : null;
const only = args.filter((a, i) => !a.startsWith("--") && !["--stills", "--at", "--out", "--bitrate", "--scale", "--poster"].includes(args[i - 1]));

const TYPES = { ".html": "text/html", ".js": "text/javascript", ".png": "image/png", ".webp": "image/webp", ".svg": "image/svg+xml", ".mp4": "video/mp4" };
const server = createServer(async (req, res) => {
  const path = join(ROOT, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (!path.startsWith(ROOT)) { res.writeHead(403).end(); return; }
  try { const body = await readFile(path); res.writeHead(200, { "content-type": TYPES[extname(path)] || "application/octet-stream" }).end(body); }
  catch { res.writeHead(404).end(); }
}).listen(8790);

const page = await (await fetch("http://127.0.0.1:9333/json/new?about:blank", { method: "PUT" })).json();
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise(ok => ws.onopen = ok);
let id = 0; const waiting = {};
ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && waiting[d.id]) { waiting[d.id](d); delete waiting[d.id]; } };
const send = (method, params = {}) => new Promise(ok => { const i = ++id; waiting[i] = ok; ws.send(JSON.stringify({ id: i, method, params })); });
const js = async e => {
  const r = await send("Runtime.evaluate", { expression: e, awaitPromise: true, returnByValue: true });
  if (r.result.exceptionDetails) throw new Error(r.result.exceptionDetails.exception?.description || JSON.stringify(r.result.exceptionDetails));
  return r.result.result.value;
};
try {
  await send("Page.navigate", { url: "http://localhost:8790/tools/social/studio.html" });
  for (let i = 0; i < 100 && !(await js("typeof window.ready === 'object'").catch(() => false)); i++) await new Promise(ok => setTimeout(ok, 100));
  await js("window.ready");
  if (args.includes("--avatar")) {
    await mkdir(OUT, { recursive: true });
    await writeFile(join(OUT, "profile.png"), Buffer.from((await js("avatar()")).split(",")[1], "base64"));
    console.log("profile.png"); only.push("-none-");
  }
  const list = (await js("sceneList()")).filter(s => !only.length || only.some(o => s.id.startsWith(o)));
  await mkdir(stills || OUT, { recursive: true });
  for (const s of list) {
    const t0 = Date.now();
    if (POSTER) {
      const url = await js(`poster(${JSON.stringify(s.id)}, ${+POSTER}, 1280)`);
      await writeFile(join(OUT, `${s.id}-poster.webp`), Buffer.from(url.split(",")[1], "base64"));
    } else if (stills) {
      const ai = args.indexOf("--at"), at = ai >= 0 ? args[ai + 1].split(",").map(Number) : [.9, s.dur * .45, s.dur * .7, s.dur - .1];
      for (const [k, t] of at.entries()) { const name = "abcdefghij"[k];
        const url = await js(`still(${JSON.stringify(s.id)}, ${t})`);
        await writeFile(join(stills, `${s.id}-${name}.png`), Buffer.from(url.split(",")[1], "base64"));
      }
    } else {
      const bytes = await js(`render(${JSON.stringify(s.id)}, ${BITRATE}, ${SCALE})`), parts = [];
      for (let at = 0; at < bytes; at += 6_000_000) parts.push(Buffer.from(await js(`chunk(${at}, 6000000)`), "base64"));   // in pieces: a long video is too big for one message
      await writeFile(join(OUT, `${s.id}.mp4`), Buffer.concat(parts));
    }
    console.log(s.id, `${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
} finally {
  ws.close(); await fetch("http://127.0.0.1:9333/json/close/" + page.id).catch(() => null); server.close();
}
process.exit(0);
