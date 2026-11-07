// Day 13: "my goal, one small step a day". The goal's path of days winds up the screen; each day is tapped (done,
// partly, or skipped), Ember hops along, and every 5 days you did your step (or part of it) the goal levels up,
// as goal_level does in mind/core.py.
import * as K from "../kit.js";
const { W, C, makeEmber, clamp, ease, out3, back, appear, bg, say, ember, pill, tap, endCard } = window;
const c = window.c;
const END = 10.9;
let e;

const KINDS = ["done", "done", "done", "done", "done", "done", "partly", "done", "done", "done", "skip", "done", "done", "done", "done", "done"];
const AT = KINDS.map((_, i) => .7 + i * .48);
const FILL = { done: C.btn, partly: "#c98b5a", skip: "#4a3a2e" };
// the level after each day: up one every 5 days that weren't skipped
const LEVEL = KINDS.map((_, i) => 1 + Math.floor(KINDS.slice(0, i + 1).filter(k => k !== "skip").length / 5));
const UPS = LEVEL.map((l, i) => i && l > LEVEL[i - 1] || (!i && l > 1) ? i : -1).filter(i => i >= 0);
const px = i => W / 2 + Math.sin(i * .78) * 250, wy = i => -i * 150;
const scrollFor = i => Math.max(0, i * 150 - 150);
const CAPS = [
  [0.1, 2.7, "one small step a day"],
  [3.0, 6.2, "every 5 days I show up, it levels up"],
  [8.3, 10.7, "day 16. goal level 4."],
];
const current = t => { let k = -1; AT.forEach((a, i) => { if (t >= a) k = i; }); return k; };

export default {
  dur: 13.4,
  caption: "My goal, one small step a day. Every 5 days I show up, it levels up. Day 16, goal level 4, still going.",
  tags: "#goals #consistency #habittracker #discipline #satisfying",
  sounds: [...KINDS.flatMap((k, i) => [["tap", AT[i] - .06], k === "skip" ? ["boop", AT[i], -8] : ["tick", AT[i], i * .7]]),
    ...UPS.flatMap(i => [["unlock", AT[i] + .15], ["sparkle", AT[i] + .2]]), ["chime", END + .1]],
  init() { e = makeEmber(300); e.state.level = { level: 8, stage: "Ember" }; },
  draw(t) {
    if (t < END + .5) {
      const k = current(t), prevK = Math.max(0, k - 1);
      const scroll = k < 0 ? 0 : scrollFor(prevK) + (scrollFor(k) - scrollFor(prevK)) * ease((t - AT[k]) / .35);
      const sy = i => 1350 + wy(i) + scroll;
      bg(1000, .6);
      // the path, then the days on it (kept below the header)
      c.save(); c.beginPath(); c.rect(0, 480, W, 1920); c.clip();
      c.save(); c.strokeStyle = C.raised; c.lineWidth = 20; c.lineCap = "round"; c.lineJoin = "round"; c.beginPath();
      KINDS.forEach((_, i) => { i ? c.lineTo(px(i), sy(i)) : c.moveTo(px(i), sy(i)); }); c.lineTo(px(16), sy(16)); c.lineTo(px(17), sy(17)); c.stroke(); c.restore();
      for (let i = 0; i < 18; i++) {
        const y = sy(i); if (y < 330 || y > 1700) continue;
        const kind = KINDS[i], done = i <= k && kind, p = done ? back((t - AT[i]) / .3) : 0;
        c.beginPath(); c.arc(px(i), y, 46, 0, Math.PI * 2); c.fillStyle = C.surface; c.fill(); c.strokeStyle = "rgba(255,245,235,.12)"; c.lineWidth = 3; c.stroke();
        if (p > 0) {
          c.beginPath(); c.arc(px(i), y, 46 * p, 0, Math.PI * 2); c.fillStyle = FILL[kind]; c.fill();
          c.save(); c.globalAlpha = clamp(p); c.font = `900 40px ${K.F}`; c.fillStyle = kind === "skip" ? C.faint : C.ink; c.textAlign = "center"; c.textBaseline = "middle";
          c.fillText(kind === "skip" ? "–" : kind === "partly" ? "½" : "✓", px(i), y + 2); c.restore();
        }
        if (i < KINDS.length) tap(t, AT[i] - .06, px(i), y);
        const up = UPS.indexOf(i);
        if (up >= 0 && t > AT[i] + .1) pill(`Goal level ${LEVEL[i]}`, px(i) + (px(i) > W / 2 ? -300 : 300), y + 10, { size: 38, scale: back((t - AT[i] - .1) / .35) });
      }
      c.restore();
      // Ember hops from day to day, standing just above the newest one
      const from = Math.max(0, k - 1), to = Math.max(0, k), h = k < 0 ? 0 : clamp((t - AT[to]) / .35);
      const spot = i => [px(i) + (W / 2 - px(i)) * .3, sy(i) - 120];
      const ex = spot(from)[0] + (spot(to)[0] - spot(from)[0]) * ease(h);
      const ey = spot(from)[1] + (spot(to)[1] - spot(from)[1]) * ease(h) - Math.sin(h * Math.PI) * 70;
      const upNow = UPS.some(i => t >= AT[i] && t < AT[i] + .6);
      e.face(upNow ? "surprised" : KINDS[to] === "skip" && k >= 0 && t - AT[to] < .8 ? "calm" : "happy", .9);
      if (UPS.some(i => t >= AT[i] + .1 && t < AT[i] + .1 + 1 / 30)) e.burst(20);
      if (t < END) ember(e, t, ex, ey, 230);
      // the goal's header
      const lv = k < 0 ? 1 : LEVEL[k];
      pill(`Run 5 km · Goal level ${lv}`, W / 2, 410, { size: 44, fill: C.raised, color: C.text, scale: UPS.some(i => t >= AT[i] + .1 && t < AT[i] + .5) ? 1.08 : 1 });
      for (const i of UPS) K.flash(t, AT[i] + .1, .3, .22);
      K.captions(t, CAPS);
    }
    if (t >= END) endCard(t, END, e, "Your companion who checks up on you");
    K.grain();
  },
};
