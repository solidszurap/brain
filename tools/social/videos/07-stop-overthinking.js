// Day 7: "trying to find my purpose by thinking about it". Anxious thoughts pile up around a worried Ember, it pops
// them, and three small experiments take their place, each with an energy meter: the one that gave energy is a clue.
import * as K from "../kit.js";
const { W, C, makeEmber, clamp, out3, back, ease, appear, bg, say, ember, pill, endCard } = window;
const c = window.c;
const END = 11.3, POP = 4.3, MOVE = 6.7, CLUE = 9.6;
let e;

// [text, x, y, appears]
const THOUGHTS = [
  ["what's my passion?", 300, 640, .5], ["am I too late?", 815, 670, 1.1], ["what if I pick wrong?", 305, 1330, 1.6],
  ["everyone else knows", 560, 1455, 2.1], ["I'm not good at anything", 540, 470, 2.5], ["I should know by now", 790, 1295, 2.9],
];
// [title, energy 0..1, what it did, appears]
const EXPS = [["Sketch 15 minutes a day", .9, "gave me energy", 7.0], ["Write 200 words before work", .28, "drained me", 7.5], ["Volunteer twice this week", .78, "gave me energy", 8.0]];
const CAPS = [
  [0.1, 3.9, "trying to find my purpose by thinking about it"],
  [4.4, 6.9, "you won't find it by thinking. you find it by trying"],
  [7.0, 11.1, "small experiments, a week each. notice what gives you energy"],
];
function thought(text, x, y, t, at, i) {
  const a = out3((t - at) / .35), popK = (t - POP - i * .18) / .25;
  if (a <= 0 || popK >= 1) return;
  const drift = Math.sin(t * 1.3 + i * 1.7) * 10, sc = popK > 0 ? 1 + popK * .35 : back((t - at) / .4);
  c.save(); c.globalAlpha = popK > 0 ? 1 - popK : a; c.translate(x, y + drift); c.scale(sc, sc);
  c.font = `800 42px ${K.F}`; const w = c.measureText(text).width + 64;
  c.beginPath(); c.roundRect(-w / 2, -44, w, 88, 44); c.fillStyle = C.surface; c.fill(); c.strokeStyle = "rgba(255,245,235,.16)"; c.lineWidth = 3; c.stroke();
  // the little circles that make it a thought bubble, trailing from its edge towards Ember
  const len = Math.hypot(W / 2 - x, 980 - y), ux = (W / 2 - x) / len, uy = (980 - y) / len;
  const edge = Math.min(Math.abs(ux) > .01 ? (w / 2) / Math.abs(ux) : 1e9, Math.abs(uy) > .01 ? 44 / Math.abs(uy) : 1e9);
  for (const [d, r] of [[18, 13], [46, 8]]) {
    c.beginPath(); c.arc(ux * (edge + d), uy * (edge + d), r, 0, Math.PI * 2); c.fillStyle = C.surface; c.fill(); c.strokeStyle = "rgba(255,245,235,.16)"; c.lineWidth = 3; c.stroke();
  }
  c.fillStyle = C.text; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText(text, 0, 2);
  c.restore();
  // a few sparks where it popped
  if (popK > 0) for (let k = 0; k < 8; k++) {
    const ang = k / 8 * Math.PI * 2 + i, d = 40 + popK * 120;
    c.save(); c.globalAlpha = 1 - popK; c.fillStyle = C.btn; c.beginPath(); c.arc(x + Math.cos(ang) * d, y + Math.sin(ang) * d, 7 * (1 - popK), 0, Math.PI * 2); c.fill(); c.restore();
  }
}
function experiment([title, energy, did, at], i, t) {
  const a = out3((t - at) / .4); if (a <= 0) return;
  const y = 820 + i * 240, win = i === 0 && t > CLUE, dim = i > 0 && t > CLUE ? .55 : 1;
  const sc = win ? 1 + .04 * back((t - CLUE) / .4) : 1;
  c.save(); c.globalAlpha = a * dim; c.translate(W / 2 + (1 - a) * 120, y + 100); c.scale(sc, sc);
  c.beginPath(); c.roundRect(-430, -100, 860, 200, 36); c.fillStyle = C.surface; c.fill();
  c.strokeStyle = win ? C.btn : "rgba(255,245,235,.14)"; c.lineWidth = win ? 6 : 3; c.stroke();
  c.textAlign = "left"; c.textBaseline = "middle";
  c.font = `900 44px ${K.F}`; c.fillStyle = C.text; c.fillText(title, -390, -46);
  c.font = `700 32px ${K.F}`; c.fillStyle = C.dim; c.fillText("7 days", -390, 4);
  // the energy meter
  const fill = energy * out3((t - at - .3) / .7), good = energy > .5;
  c.beginPath(); c.roundRect(-390, 40, 560, 26, 13); c.fillStyle = C.raised; c.fill();
  if (fill > 0) { c.beginPath(); c.roundRect(-390, 40, 560 * fill, 26, 13); c.fillStyle = good ? C.btn : "#6d7fa6"; c.fill(); }
  c.font = `800 30px ${K.F}`; c.fillStyle = good ? C.btn : "#9aa8c8"; c.globalAlpha = a * dim * appear(t, at + .9, .3); c.fillText(did, 196, 54);
  c.restore();
  if (win) pill("a clue", W / 2 + 330, y - 4, { size: 40, scale: back((t - CLUE - .1) / .35) });
}

export default {
  dur: 13.8,
  caption: "Trying to find my purpose by thinking about it didn't work. Small experiments did: a week each, and notice what gives you energy.",
  tags: "#findyourpurpose #overthinking #selfdiscovery #purpose #mindset",
  sounds: [...THOUGHTS.map(([, , , at], i) => ["boop", at, -6 + i]), ["rise", POP - .5],
    ...THOUGHTS.map((_, i) => ["boop", POP + i * .18, 7 + i * 2]), ["whoosh", MOVE],
    ...EXPS.flatMap(([, , , at], i) => [["thump", at], ["tick", at + .6, i * 4]]), ["unlock", CLUE], ["sparkle", CLUE + .1], ["chime", END + .1]],
  init() { e = makeEmber(640); e.state.level = { level: 4, stage: "Spark" }; },
  draw(t) {
    if (t < END + .5) {
      const calm = t > POP;
      bg(980 - ease((t - MOVE) / .8) * 420, calm ? .7 : .35);
      e.face(t < POP - .3 ? "worried" : t < POP + .3 ? "surprised" : t < CLUE ? "eager" : "happy", calm ? .85 : .45);
      const m = ease((t - MOVE) / .8), ey = 980 - m * 420, size = 640 - m * 260;
      if (t < END) ember(e, t, W / 2, ey, size);
      THOUGHTS.forEach(([text, x, y, at], i) => thought(text, x, y, t, at, i));
      EXPS.forEach((x, i) => experiment(x, i, t));
      K.captions(t, CAPS);
    }
    if (t >= END) endCard(t, END, e, "Find your purpose. Then live it.");
    K.grain();
  },
};
