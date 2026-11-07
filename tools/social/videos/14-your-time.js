// Day 14: "you pick when it checks up on you". The Check-ups screen: Regularly, the time wheel spins from 18:00 to
// 7:30, Saturday and Sunday switched off; then it's Monday, 7:30, and Ember's message arrives right on time.
// (As in the app: Ember tab → Check-ups, `checkup_at` and `checkup_days`; the default is 18:00, every day.)
import * as K from "../kit.js";
const { C, makeEmber, clamp, ease, out3, endCard } = window;
const END = 10.7, LOCK = 5.6, NOTE = 6.4, OPEN = 7.7;
const T_SEG = .7, H0 = 2.0, H1 = 3.4, M0 = 2.3, M1 = 3.5, SAT = 4.1, SUN = 4.6;
let e;

const hourAt = t => 18 + (7 - 18) * ease((t - H0) / (H1 - H0));
const minAt = t => 6 * ease((t - M0) / (M1 - M0));          // in steps of 5 minutes
function wheel(cx, value, n, fmt) {
  const s = K.s, base = Math.floor(value);
  for (let k = base - 2; k <= base + 3; k++) {
    const y = 712 + (k - value) * 84, d = Math.abs(y - 712) / 84; if (d > 2.4) continue;
    s.save(); s.globalAlpha = Math.max(0, 1 - d * .38);
    K.txt(fmt(((k % n) + n) % n), cx, y, d < .5 ? 60 : 46, d < .5 ? 900 : 700, d < .5 ? C.text : C.dim, "center"); s.restore();
  }
}
function settings(t) {
  const s = K.s;
  s.fillStyle = C.bg; s.fillRect(0, 0, K.SW, K.SH);
  K.statusBar("21:05");
  K.txt("‹ Ember", 34, 118, 30, 700, C.dim);
  K.txt("Check-ups", K.SW / 2, 118, 34, 900, C.text, "center");
  K.txt("Ember writes to you first, at your time.", K.SW / 2, 196, 28, 600, C.dim, "center");
  K.rr(30, 246, K.SW - 60, 1010, 36); s.fillStyle = C.surface; s.fill(); s.strokeStyle = "rgba(255,245,235,.1)"; s.lineWidth = 2; s.stroke();
  // how often
  K.txt("How often", 70, 316, 30, 800);
  const segs = ["Off", "When it matters", "Regularly"], on = t >= T_SEG ? 2 : 1;
  K.rr(64, 352, K.SW - 128, 84, 42); s.fillStyle = C.raised; s.fill();
  let x = 72; const widths = segs.map(g => { s.font = `800 28px ${K.F}`; return s.measureText(g).width + 56; }), extra = (K.SW - 144 - widths.reduce((a, b) => a + b)) / 3;
  segs.forEach((g, i) => { const w = widths[i] + extra; if (i === on) { K.rr(x, 360, w, 68, 34); s.fillStyle = C.btn; s.fill(); } K.txt(g, x + w / 2, 395, 28, 800, i === on ? C.ink : C.text, "center"); if (i === 2) K.ring(t, T_SEG - .1, x + w / 2, 395); x += w; });
  // the time wheel
  K.txt("Time", 70, 512, 30, 800);
  K.rr(150, 670, K.SW - 300, 84, 22); s.fillStyle = C.raised; s.fill();
  wheel(310, hourAt(t), 24, v => String(v).padStart(2, "0"));
  K.txt(":", K.SW / 2, 708, 60, 900, C.text, "center");
  wheel(470, minAt(t), 12, v => String(v * 5).padStart(2, "0"));
  if (t > H0 - .3 && t < H0) K.ring(t, H0 - .25, 310, 712);
  // days
  K.txt("Days", 70, 922, 30, 800);
  "MTWTFSS".split("").forEach((d, i) => {
    const off = (i === 5 && t >= SAT) || (i === 6 && t >= SUN), cx = 112 + i * 93, tapAt = i === 5 ? SAT : i === 6 ? SUN : null;
    const k = tapAt ? 1 - .12 * Math.max(0, Math.sin(clamp((t - tapAt + .05) / .25) * Math.PI)) : 1;
    s.save(); s.translate(cx, 1000); s.scale(k, k); s.beginPath(); s.arc(0, 0, 40, 0, Math.PI * 2); s.fillStyle = off ? C.raised : C.btn; s.fill();
    K.txt(d, 0, 2, 30, 900, off ? C.dim : C.ink, "center"); s.restore();
    if (tapAt) K.ring(t, tapAt - .1, cx, 1000);
  });
  const note = t < H1 ? "Next check-up: today at 18:00" : t < SUN ? "Next check-up: tomorrow at 07:30" : "Next check-up: Monday at 07:30";
  K.txt(note, K.SW / 2, 1150, 30, 800, C.btn, "center");
}
const lock = { time: "7:30", date: "Monday 9 November", notes: [{ at: NOTE, text: "Morning! Today's step: 10 minutes of sketching before work. You in?" }] };
const chat = {
  title: "Sketch every day",
  clock: () => "7:31",
  face: K.timeline([[0, "eager", .85], [9.0, "happy", .95]]),
  level: () => ({ level: 6, stage: "Ember" }),
  typing: [{ from: 8.15, to: 8.8, text: "in. coffee first", send: 9.0 }],
  keyboard: [[OPEN + .2, END + 1]],
  msgs: [
    { who: "ember", text: "Morning! Today's step: 10 minutes of sketching before work. You in?", at: 0 },
    { who: "you", text: "in. coffee first", at: 9.0 },
    { who: "ember", text: "Deal. I'll ask tonight how it went.", at: 9.5 },
  ],
};
const CAM = [
  { t: 0, x: 540, y: 1190, w: 800, r: -.015 }, { t: LOCK - .2, x: 540, y: 1180, w: 815, r: 0 },
  { t: LOCK, cut: true, x: 540, y: 1150, w: 760, r: -.02 }, { t: OPEN - .3, x: 540, y: 1140, w: 790, r: -.01 },
  { t: OPEN + .35, x: 540, y: 1290, w: 830, r: 0 }, { t: END, x: 540, y: 1275, w: 850, r: 0 },
];
const CAPS = [
  [0.1, 2.0, "you pick when it checks up on you"],
  [2.1, 5.4, "7:30, weekdays only"],
  [NOTE - .2, 10.5, "monday, 7:30. right on time."],
];

export default {
  dur: 13.2,
  caption: "You pick when it checks up on you: any time, any days. Mine is 7:30, weekdays only. Monday, 7:30, right on time.",
  tags: "#morningroutine #accountability #habits #productivity #selfimprovement",
  sounds: [["tap", T_SEG - .1], ["boop", T_SEG, 4], ["tap", H0 - .25],
    ...Array.from({ length: 11 }, (_, k) => ["tick", H0 + (H1 - H0) * Math.acos(1 - 2 * (k + .5) / 11) / Math.PI, 8 - k * .4]),
    ...Array.from({ length: 6 }, (_, k) => ["tick", M0 + (M1 - M0) * Math.acos(1 - 2 * (k + .5) / 6) / Math.PI, 3 + k * .5]),
    ["tap", SAT - .1], ["boop", SAT, -4], ["tap", SUN - .1], ["boop", SUN, -5], ["whoosh", LOCK],
    ["buzz", NOTE - .05], ["ding", NOTE], ["tap", OPEN - .15], ["whoosh", OPEN], ...K.chatSounds(chat), ["chime", END + .1]],
  init() { e = makeEmber(640); e.state.level = { level: 6, stage: "Ember" }; },
  draw(t) {
    const cam = K.camera(t, CAM, [[NOTE, NOTE + .3, 6]]);
    if (t < END + .5) {
      if (t < LOCK) { if (t < END) e.at(t); settings(t); }
      else if (t < OPEN) { if (t < END) e.at(t); const r = K.lockScreen(t, lock); if (r[0]) K.ring(t, OPEN - .15, K.SW / 2, r[0].y + 80); }
      else {
        K.chatScreen(t, chat, e, t < END);
        const k = clamp((t - OPEN) / .3);
        if (k < 1) { K.s.save(); K.s.globalAlpha = 1 - k; K.lockScreen(t, lock); K.s.restore(); }
      }
      K.room(cam); K.phone(cam);
      K.captions(t, CAPS);
      K.titleCard(t, LOCK, "Monday", .22);
    }
    if (t >= END) endCard(t, END, e, "Your companion who checks up on you");
    K.grain();
  },
};
