// Day 4: "every Monday since October". A notes list of Mondays that never started, each struck through, then
// Ember's notification on a Tuesday: start today, with 5 minutes. You do, and it's day 1 (and a level up).
import * as K from "../kit.js";
const { C, makeEmber, clamp, out3, endCard } = window;
const END = 12.3, BANNER = 3.6, OPEN = 4.6, CUT = 8.7, LEVEL = 9.35;
let e;

const MONDAYS = ["Mon 6 Oct · start running", "Mon 13 Oct · start running (for real)", "Mon 20 Oct · ok THIS monday",
  "Mon 27 Oct · new month, new me", "Mon 3 Nov · actually start running", "Mon 10 Nov · ..."];
const STRIKE = i => .7 + i * .5;      // when each one is crossed out (the last stays)
function notes(t) {
  const s = K.s;
  s.fillStyle = "#1a1613"; s.fillRect(0, 0, K.SW, K.SH);
  K.statusBar("8:12");
  K.txt("‹ Notes", 34, 118, 32, 600, "#f2b45a");
  K.txt("starting on monday", 44, 236, 56, 900, C.text);
  K.txt("6 October 2026 at 21:40", 44, 302, 26, 600, C.faint);
  MONDAYS.forEach((m, i) => {
    const y = 400 + i * 92;
    K.txt("•", 44, y, 34, 900, C.dim);
    K.txt(m, 84, y, 33, 600, i < MONDAYS.length - 1 && t > STRIKE(i) + .2 ? C.faint : C.text);
    if (i < MONDAYS.length - 1) {
      const k = out3((t - STRIKE(i)) / .2); if (k <= 0) return;
      s.font = `600 33px ${K.F}`; const w = s.measureText(m).width;
      s.strokeStyle = "#ff8c5a"; s.lineWidth = 5; s.lineCap = "round";
      s.beginPath(); s.moveTo(80, y + 2); s.lineTo(80 + (w + 10) * k, y - 1); s.stroke();
    }
  });
  if ((t * 2) % 1 < .6) { s.fillStyle = "#f2b45a"; s.fillRect(84, 400 + MONDAYS.length * 92 - 22, 3, 44); }
}
// Ember's banner notification, sliding down over whatever is on the screen
function banner(t) {
  const k = out3((t - BANNER) / .35); if (k <= 0) return [0, 0];
  const s = K.s, y = -220 + k * 270, ls = K.wrap("It's Tuesday. What if we start today, with just 5 minutes?", 520, `500 29px ${K.F}`);
  s.save(); s.shadowColor = "rgba(0,0,0,.5)"; s.shadowBlur = 40;
  K.rr(26, y, K.SW - 52, 106 + ls.length * 38, 34); s.fillStyle = "#3b2c22"; s.fill(); s.restore();
  s.save(); K.rr(54, y + 28, 64, 64, 15); s.clip(); if (window.IMGS?.icon) s.drawImage(window.IMGS.icon, 54, y + 28, 64, 64); s.restore();
  K.txt("Ember sent you a message", 138, y + 46, 29, 800, "#fff4e8");
  K.txt("now", K.SW - 56, y + 46, 25, 600, "rgba(255,240,228,.6)", "right");
  ls.forEach((l, i) => K.txt(l, 138, y + 86 + i * 38, 29, 500, "rgba(255,244,232,.92)"));
  return [K.SW / 2, y + 90];
}
const chat = {
  title: "Start running",
  clock: t => t >= CUT ? "8:38" : "8:13",
  face: K.timeline([[0, "eager", .8], [6.6, "happy", .9], [7.25, "eager", .95], [CUT, "curious", .8], [9.2, "happy", 1]]),
  level: t => t >= LEVEL ? { level: 2, stage: "Spark" } : { level: 1, stage: "Spark" }, levelAt: LEVEL,
  typing: [{ from: 5.35, to: 6.35, text: "ok. 5 minutes. today.", send: 6.6 }],
  keyboard: [[5.0, CUT]],
  fresh: CUT,
  msgs: [
    { who: "ember", text: "It's Tuesday. What if we start today, with just 5 minutes?", at: 0 },
    { who: "you", text: "ok. 5 minutes. today.", at: 6.6 },
    { who: "ember", text: "Today, not Monday. Shoes on, I'll wait.", at: 7.25 },
    { who: "check", how: "Did it", step: "walk and run 5 minutes", at: 9.2 },
    { who: "ember", text: "Day 1. On a Tuesday. That's how it starts.", at: 9.9 },
  ],
  xp: [{ at: 9.3, text: "+10 XP", until: 11.6 }],
};
const CAM = [
  { t: 0, x: 540, y: 1075, w: 900, r: -.02 }, { t: 3.4, x: 540, y: 1050, w: 930, r: -.01 },
  { t: OPEN + .05, x: 540, y: 1290, w: 820, r: 0 }, { t: CUT - .3, x: 540, y: 1270, w: 840, r: 0 },
  { t: CUT, cut: true, x: 540, y: 1134, w: 780, r: 0 }, { t: END, x: 540, y: 1120, w: 805, r: 0 },
];
const CAPS = [
  [0.1, 3.45, "every monday since october"],
  [3.65, 5.25, "then this showed up. on a tuesday.", 1330],
  [5.4, 8.4, "ok, today. not monday."],
  [9.25, 12.1, "day 1. on a tuesday."],
];

export default {
  dur: 14.8,
  caption: "Every Monday since October: \"I'll start running.\" Then it texted me on a Tuesday: start today, with just 5 minutes. Day 1.",
  tags: "#procrastination #mondaymotivation #running #habits #accountability",
  sounds: [...MONDAYS.slice(0, -1).map((_, i) => ["strike", STRIKE(i)]), ["buzz", BANNER - .05], ["ding", BANNER], ["tap", OPEN - .15], ["whoosh", OPEN],
    ...K.chatSounds(chat), ["whoosh", CUT - .3], ["thump", 9.2], ["levelup", LEVEL], ["xp", 9.3], ["chime", END + .1]],
  init() { e = makeEmber(640); },
  draw(t) {
    const cam = K.camera(t, CAM, [[BANNER, BANNER + .35, 6]]);
    if (t < END + .5) {
      if (t < OPEN) {
        if (t < END) e.at(t);
        notes(t); const [bx, by] = banner(t); K.ring(t, OPEN - .15, bx, by);
      } else {
        K.chatScreen(t, chat, e, t < END);
        const k = clamp((t - OPEN) / .3);
        if (k < 1) { K.s.save(); K.s.globalAlpha = 1 - k; notes(t); banner(t); K.s.restore(); }
      }
      K.room(cam); K.phone(cam);
      K.captions(t, CAPS);
      K.titleCard(t, CUT, "25 minutes later");
    }
    if (t >= END) endCard(t, END, e, "Your companion who checks up on you");
    K.grain();
  },
};
