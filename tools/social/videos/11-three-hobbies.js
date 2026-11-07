// Day 11: "I tested 3 hobbies for a week each to find my thing". Three week-long experiments fill in day by day
// (energy or drain, the question Ember asks each evening), the winner lights up, and Ember suggests making it a goal.
import * as K from "../kit.js";
const { W, C, makeEmber, clamp, out3, back, appear, bg, say, ember, pill, tap, endCard } = window;
const c = window.c;
const END = 10.9, CLUE = 7.2, ASK = 7.6, GO = 9.6;
let e;

// [title, days (1 energy, 0 drain), when the first day fills]
const WEEKS = [["Sketching", [1, 1, 1, 0, 1, 1, 1], .55], ["Writing before work", [0, 0, 1, 0, 0, 0, 1], 2.75], ["Climbing", [1, 0, 1, 1, 0, 1, 0], 4.95]];
const STEP = .26;
const CAPS = [
  [0.1, 2.8, "I tested 3 hobbies for a week each to find my thing"],
  [3.0, 7.0, "every evening Ember asked: energy or drain?"],
  [CLUE + .1, 10.7, "the one that gives you energy is a clue"],
];
function card([title, days, at], i, t) {
  const y = 470 + i * 270, a = i ? appear(t, at - .4, .35) : 1; if (a <= 0) return;
  const win = i === 0 && t > CLUE, dim = i > 0 && t > CLUE ? .5 : 1, sc = win ? 1 + .035 * back((t - CLUE) / .4) : 1;
  c.save(); c.globalAlpha = a * dim; c.translate(W / 2, y + 115); c.scale(sc, sc);
  c.beginPath(); c.roundRect(-450, -115, 900, 230, 36); c.fillStyle = C.surface; c.fill();
  c.strokeStyle = win ? C.btn : "rgba(255,245,235,.14)"; c.lineWidth = win ? 6 : 3; c.stroke();
  c.textAlign = "left"; c.textBaseline = "middle";
  c.font = `900 46px ${K.F}`; c.fillStyle = C.text; c.fillText(title, -400, -54);
  c.font = `700 30px ${K.F}`; c.fillStyle = C.dim; c.textAlign = "right"; c.fillText(`week ${i + 1}`, 400, -54);
  let good = 0;
  days.forEach((d, k) => {
    const x = -370 + k * 82, f = out3((t - at - k * STEP) / .18);
    c.beginPath(); c.arc(x, 40, 30, 0, Math.PI * 2); c.fillStyle = C.raised; c.fill();
    if (f > 0) { c.beginPath(); c.arc(x, 40, 30 * back((t - at - k * STEP) / .3), 0, Math.PI * 2); c.fillStyle = d ? C.btn : "#6d7fa6"; c.fill(); if (d) good++; }
  });
  const done = t > at + 6 * STEP + .2;
  c.globalAlpha = a * dim * (done ? appear(t, at + 6 * STEP + .2, .3) : 0);
  c.font = `800 32px ${K.F}`; c.fillStyle = good >= 4 ? C.btn : "#9aa8c8"; c.textAlign = "right"; c.fillText(`${good} of 7: energy`, 400, 40);
  c.restore();
  if (win) pill("a clue", W / 2 + 360, y - 16, { size: 40, scale: back((t - CLUE - .1) / .35) });
}
function ask(t) {
  const a = appear(t, ASK, .35); if (a <= 0) return;
  c.save(); c.globalAlpha = a; c.translate(0, (1 - a) * 40);
  c.beginPath(); c.roundRect(370, 1290, 640, 230, [12, 40, 40, 40]); c.fillStyle = C.surface; c.fill(); c.strokeStyle = "rgba(255,245,235,.14)"; c.lineWidth = 3; c.stroke();
  c.font = `700 36px ${K.F}`; c.fillStyle = C.text; c.textAlign = "left"; c.textBaseline = "middle";
  c.fillText("Sketching gave you energy", 408, 1340); c.fillText("6 of 7 days. Make it a goal?", 408, 1386);
  const pressed = t > GO, k = 1 - .08 * Math.max(0, Math.sin(clamp((t - GO + .1) / .25) * Math.PI));
  c.save(); c.translate(560, 1460); c.scale(k, k); c.beginPath(); c.roundRect(-150, -34, 300, 68, 34); c.fillStyle = C.btn; c.fill();
  c.font = `900 32px ${K.F}`; c.fillStyle = C.ink; c.textAlign = "center"; c.fillText(pressed ? "Goal started ✓" : "Make it a goal", 0, 2); c.restore();
  c.restore();
}

export default {
  dur: 13.4,
  caption: "I tested 3 hobbies for a week each to find my thing. Every evening Ember asked: energy or drain? The one that gives you energy is a clue.",
  tags: "#findyourpurpose #hobbies #selfdiscovery #experiment #purpose",
  sounds: [...WEEKS.flatMap(([, days, at], i) => [["whoosh", at - .4], ...days.map((d, k) => d ? ["tick", at + k * STEP, k + i] : ["boop", at + k * STEP, -8])]),
    ["unlock", CLUE], ["sparkle", CLUE + .1], ["pop", ASK], ["tap", GO - .1], ["levelup", GO], ["chime", END + .1]],
  init() { e = makeEmber(420); e.state.level = { level: 6, stage: "Ember" }; },
  draw(t) {
    if (t < END + .5) {
      bg(800, t > CLUE ? .8 : .55);
      WEEKS.forEach((w, i) => card(w, i, t));
      e.face(t < ASK ? "curious" : t < GO ? "eager" : "happy", t > CLUE ? .95 : .7);
      if (t >= GO && t < GO + 1 / 30) e.burst(24);
      if (t < END) ember(e, t, 215, 1390 - (1 - appear(t, ASK - .3, .4)) * 60, 360, appear(t, ASK - .3, .4));
      ask(t);
      tap(t, GO - .1, 560, 1460);
      K.captions(t, CAPS);
    }
    if (t >= END) endCard(t, END, e, "Find your purpose. Then live it.");
    K.grain();
  },
};
