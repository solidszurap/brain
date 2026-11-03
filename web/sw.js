// Ember's service worker: makes Ember installable as an app, and shows a plain
// message instead of a browser error when there's no internet. It caches nothing,
// so you always get the current Ember. (Later: notifications arrive through here.)
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(self.clients.claim()));
self.addEventListener("fetch", e => {
  if (e.request.mode !== "navigate") return;
  e.respondWith(fetch(e.request).catch(() => new Response(
    `<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">
     <body style="background:#17130f;color:#f1e7dc;font:16px system-ui;display:grid;place-items:center;height:100vh;margin:0;text-align:center;padding:24px">
     <div><div style="font-size:42px">·</div><p>Ember needs the internet to think.<br>Try again when you're back online.</p></div>`,
    {headers: {"Content-Type": "text/html; charset=utf-8"}})));
});
