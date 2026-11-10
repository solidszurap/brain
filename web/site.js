// Ember's website: the phone menu, the header's edge once you scroll, Ember hopping when tapped, and the
// pricing page's monthly/yearly switch. Nothing else moves on its own.
(() => {
  const $ = s => document.querySelector(s);
  const btn = $("#menuBtn"), menu = $("#navMenu"), nav = $("#nav");
  if (btn && menu) {
    const set = on => { btn.setAttribute("aria-expanded", String(on)); menu.classList.toggle("on", on); };
    btn.addEventListener("click", () => set(btn.getAttribute("aria-expanded") !== "true"));
    document.addEventListener("keydown", e => { if (e.key === "Escape") set(false); });
    menu.addEventListener("click", e => { if (e.target.closest("a")) set(false); });
  }
  if (nav) {
    const edge = () => nav.classList.toggle("scrolled", scrollY > 4);
    addEventListener("scroll", edge, {passive: true}); edge();
  }
  for (const e of document.querySelectorAll(".creature")) {
    e.addEventListener("click", () => { e.classList.remove("hop"); void e.offsetWidth; e.classList.add("hop"); });
    e.addEventListener("animationend", ev => { if (ev.animationName === "hop") setTimeout(() => e.classList.remove("hop"), 500); });
  }
  // the front page's demo video: one big button over its poster; a tap plays it with the player's own controls
  for (const f of document.querySelectorAll(".filmwrap")) {
    const v = f.querySelector("video"), b = f.querySelector(".playbtn");
    if (!v || !b) continue;
    v.controls = false; b.hidden = false;
    const play = () => { b.hidden = true; v.controls = true; v.play().catch(() => {}); };
    b.addEventListener("click", play);
    v.addEventListener("click", () => { if (!v.controls) play(); });
  }
  // TikTok, Instagram and the like open links in their own small browser, where Google won't sign anyone in (2026-11-10).
  // There, every "Start free" / "Log in" opens a sheet that says how to get to Safari or Chrome instead. The visit also
  // remembers which app it was opened in, and the Safari/Chrome link carries it (from=), for the owner page's sign-ups
  // by source; the app sends it once (web/index.html keeps the same list of apps). One link for every profile: no ?from.
  const ua = navigator.userAgent;
  const app = /Instagram/i.test(ua) ? "ig" : /musical_ly|Bytedance|TikTok/i.test(ua) ? "tt" : /FBAN|FBAV|FB_IAB/.test(ua) ? "fb"
    : /Snapchat/i.test(ua) ? "sc" : /LinkedInApp/i.test(ua) ? "li" : "";
  let from = "";
  try {
    from = localStorage.getItem("ember.from") || new URLSearchParams(location.search).get("from") || app;
    if (from) localStorage.setItem("ember.from", from);
  } catch (e) { from = new URLSearchParams(location.search).get("from") || app; }
  if (app) {
    const ios = /iPhone|iPad|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1), android = /Android/.test(ua);
    const name = { ig: "Instagram", tt: "TikTok", fb: "Facebook", sc: "Snapchat", li: "LinkedIn" }[app];
    const browser = ios ? "Safari" : "your browser";
    const path = "/?login=google" + (from ? "&from=" + encodeURIComponent(from) : ""), link = location.origin + path;
    const open = ios ? "x-safari-" + link : android ? `intent://${location.host}${path}#Intent;scheme=https;end` : "";
    const sheet = document.createElement("div");
    sheet.className = "inapp"; sheet.hidden = true;
    sheet.innerHTML = `<div class="inappcard" role="dialog" aria-modal="true" aria-labelledby="inappTitle">
      <h2 id="inappTitle">Open Ember in ${browser}</h2>
      <p>${name} opens links in its own browser, and Google sign-in doesn't work there. In ${browser} it takes a moment.</p>
      <ol><li>Tap <b>⋯</b> at the top of the screen</li><li>Tap <b>Open in ${ios ? "external browser" : "browser"}</b></li><li>Tap <b>Start free</b> there</li></ol>
      ${open ? `<a class="go" href="${open}">Open in ${browser}</a>` : ""}
      <p class="inapplink">Or copy the link and paste it into ${browser}:<br><span>${link.replace(/^https?:\/\//, "")}</span></p>
      <div class="inapprow"><button type="button" class="inappbtn" data-copy>Copy link</button><button type="button" class="inappbtn" data-close>Not now</button></div>
    </div>`;
    document.body.append(sheet);
    let back = null;
    const show = on => { sheet.hidden = !on; if (on) { back = document.activeElement; sheet.querySelector("h2").focus(); } else back?.focus?.(); };
    sheet.querySelector("h2").tabIndex = -1;
    document.addEventListener("click", e => {
      const a = e.target.closest('a[href*="login=google"]');
      if (a && !sheet.contains(a)) { e.preventDefault(); show(true); }
    }, true);
    sheet.addEventListener("click", async e => {
      if (e.target === sheet || e.target.closest("[data-close]")) show(false);
      const c = e.target.closest("[data-copy]");
      if (c) {
        try { await navigator.clipboard.writeText(link); c.textContent = "Copied"; }
        catch { const r = document.createRange(); r.selectNodeContents(sheet.querySelector(".inapplink span")); getSelection().removeAllRanges(); getSelection().addRange(r); c.textContent = "Selected: copy it"; }
        setTimeout(() => c.textContent = "Copy link", 2000);
      }
    });
    document.addEventListener("keydown", e => { if (e.key === "Escape" && !sheet.hidden) show(false); });
  }
  const toggle = $("#billing");
  if (toggle) {
    const show = yearly => {
      for (const b of toggle.querySelectorAll("button")) b.setAttribute("aria-pressed", String((b.dataset.period === "year") === yearly));
      $("#plusPrice").innerHTML = yearly ? "$49.99<small>a year</small>" : "$7.99<small>a month</small>";
      $("#plusNote").textContent = yearly ? "That's $4.17 a month, billed once a year." : "Billed every month. Cancel anytime.";
    };
    toggle.addEventListener("click", e => { const b = e.target.closest("button"); if (b) show(b.dataset.period === "year"); });
    show(true);
  }
})();
