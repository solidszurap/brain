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
