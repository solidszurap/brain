// Day 5: "this app texts you first. here's how it works". A tour of the real app (screenshots of the demo Ember):
// the notification, the chat check-in, today's step and the goal's level, the memory page, the badges. The camera
// zooms into each part and a spotlight picks it out; the screens slide like switching tabs.
import * as K from "../kit.js";
const { makeEmber, clamp, out3, back, endCard } = window;
const END = 14.2;
let e;

const lock = { time: "9:00", date: "Saturday 8 November", notes: [{ at: .35, text: "Today's step: run 12 minutes without stopping. How did it go?" }] };
// [from, screenshot, spotlights [[from, x, y, w, h]]] in screen pixels (the screenshots are 390×844 at 2×)
const SHOTS = [
  [2.0, "talk", [[2.5, 30, 730, 700, 260]]],
  [5.0, "goal", [[5.35, 34, 378, 712, 396], [6.75, 34, 798, 712, 168]]],
  [8.2, "knows", [[8.6, 32, 1004, 708, 340]]],
  [11.4, "badges", [[11.8, 28, 370, 724, 890]]],
];
const SLIDE = .28;
// the camera: wide on the lock screen, then in on what each part is about
const fit = (t, sy, w, extra = {}) => ({ t, x: 540, y: 900 + (w * K.SH / K.SW) / 2 - sy * w / K.SW, w, r: 0, ...extra });
const CAM = [
  { t: 0, x: 540, y: 1010, w: 700, r: -.03 }, { t: 1.6, x: 540, y: 990, w: 740, r: -.015 },
  fit(2.3, 860, 900), fit(4.8, 860, 930),
  fit(5.3, 575, 950), fit(6.5, 600, 960), fit(6.9, 880, 960), fit(8.0, 880, 980),
  fit(8.6, 1172, 980), fit(11.2, 1172, 1010),
  fit(11.7, 810, 860), fit(END, 810, 880),
];
const CAPS = [
  [0.1, 2.0, "this app texts you first. here's how it works"],
  [2.25, 4.95, "1. it checks in on your goal every day"],
  [5.25, 8.15, "2. one small step a day. the goal levels up"],
  [8.45, 11.35, "3. it remembers your exact words"],
  [11.65, 14.0, "4. and it grows with you"],
];
function shotAt(t) { let i = -1; for (let k = 0; k < SHOTS.length; k++) if (t >= SHOTS[k][0]) i = k; return i; }
function screen(t, step) {
  if (step) e.at(t);
  const i = shotAt(t);
  if (i < 0) { const r = K.lockScreen(t, lock); if (r[0]) K.ring(t, 1.75, K.SW / 2, r[0].y + 80); return; }
  const [from, name, spots] = SHOTS[i], k = out3((t - from) / SLIDE);
  // slide the new screen in from the right, the old one out to the left
  K.s.save(); K.s.translate((1 - k) * K.SW, 0); K.shotScreen(name);
  for (const [at, x, y, w, h] of spots) { const next = spots.find(sp => sp[0] > at); K.spotlight(x, y, w, h, clamp(Math.min((t - at) / .3, next ? (next[0] - t) / .2 : 9))); }
  if (name === "goal") {
    K.ring(t, 5.75, 164, 584);
    const a = clamp(Math.min((t - 5.85) / .15, (7.4 - t) / .25));
    if (a > 0) { const s = K.s; s.save(); s.globalAlpha = a; s.translate(390, 440 - out3((t - 5.85) / 1.2) * 30); const b = back((t - 5.85) / .35); s.scale(b, b);
      K.rr(-110, -38, 220, 76, 38); s.fillStyle = window.C.btn; s.fill(); K.txt("+10 XP", 0, 2, 36, 900, window.C.ink, "center"); s.restore(); }
  }
  K.s.restore();
  if (k < 1) {
    K.s.save(); K.s.translate(-k * K.SW, 0);
    if (i === 0) K.lockScreen(t, lock); else K.shotScreen(SHOTS[i - 1][1]);
    K.s.restore();
  }
}

export default {
  dur: 16.7,
  caption: "This app texts you first. Here's how it works: it checks in on your goal every day, one small step at a time, remembers your exact words, and grows with you.",
  tags: "#productivityapp #goals #accountability #selfimprovement #apps",
  sounds: [["buzz", .3], ["ding", .35], ["tap", 1.75], ...SHOTS.map(([at]) => ["whoosh", at - .05]),
    ...SHOTS.flatMap(([, , spots]) => spots.map(([at], n) => ["boop", at, 4 + n * 3])),
    ["tap", 5.75], ["thump", 5.8], ["xp", 5.85], ["unlock", 11.85], ["chime", END + .1]],
  init() { e = makeEmber(640); },
  draw(t) {
    const cam = K.camera(t, CAM, [[.3, .65, 6]]);
    if (t < END + .5) {
      screen(t, t < END);
      K.room(cam); K.phone(cam);
      K.captions(t, CAPS);
    }
    if (t >= END) endCard(t, END, e, "Your companion who checks up on you");
    K.grain();
  },
};
