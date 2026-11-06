// Ember's service worker: makes Ember installable as an app, shows a plain message instead of a
// browser error when there's no internet, and shows Ember's check-ups as notifications. It caches
// nothing, so you always get the current Ember.
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

// a check-up from Ember: {title, body, chat}
self.addEventListener("push", e => {
  let m = {};
  try { m = e.data ? e.data.json() : {}; } catch (err) { m = {body: e.data ? e.data.text() : ""}; }
  e.waitUntil(self.registration.showNotification(m.title || "Ember sent you a message", {
    body: m.body || "", icon: "/icons/icon-192.png", badge: "/icons/icon-192.png",
    tag: "ember-" + (m.chat || ""), data: {chat: m.chat || ""}}));
});

// tapping it opens Ember at that chat (an open window if there is one)
self.addEventListener("notificationclick", e => {
  e.notification.close();
  const url = "/?chat=" + encodeURIComponent((e.notification.data || {}).chat || "");
  e.waitUntil(self.clients.matchAll({type: "window", includeUncontrolled: true}).then(list => {
    for (const c of list) {
      if ("focus" in c) { c.postMessage({chat: (e.notification.data || {}).chat || ""}); return c.focus(); }
    }
    return self.clients.openWindow(url);
  }));
});
