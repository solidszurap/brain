// Day 8: "dressing up my accountability buddy". The look sheet: each tap changes Ember's colour or what it wears,
// with a pop and a reaction, ending on a reveal of the final look. (Pip is level 25, so every look is open.)
import * as K from "../kit.js";
const { W, C, makeEmber, clamp, out3, back, appear, bg, say, ember, pill, tap, endCard } = window;
const c = window.c;
const END = 10.9, REVEAL = 8.4;
let e;

const COLOURS = [["amber", "hsl(30,100%,60%)"], ["gold", "hsl(45,100%,58%)"], ["rose", "hsl(345,85%,66%)"], ["ocean", "hsl(200,85%,58%)"],
  ["forest", "hsl(125,55%,48%)"], ["violet", "hsl(275,75%,64%)"], ["moon", "hsl(220,30%,82%)"], ["aurora", null]];
const WEAR = [["scarf", "Scarf"], ["glasses", "Glasses"], ["headphones", "Headphones"], ["beanie", "Beanie"], ["crown", "Crown"]];
// [when, part, value]
const TAPS = [[1.0, "color", "rose"], [1.7, "wear", "scarf"], [2.4, "color", "ocean"], [3.1, "wear", "headphones"], [3.8, "color", "forest"],
  [4.5, "wear", "beanie"], [5.2, "color", "violet"], [5.9, "wear", "glasses"], [6.6, "color", "gold"], [7.3, "wear", "crown"], [8.0, "color", "aurora"]];
const SW_X = i => 150 + i * 111, SW_Y = 1300, CH_Y = 1450;
let chipX = [];
function lookAt(t) {
  const look = { color: "amber" };
  for (const [at, part, value] of TAPS) if (t >= at) look[part] = value;
  if (t >= REVEAL) Object.assign(look, { glow: "halo", sparks: "stars", eyes: "sparkly", cheeks: "hearts" });
  return look;
}
function sheet(t, look) {
  c.save();
  c.beginPath(); c.roundRect(0, 1170, W, 800, [48, 48, 0, 0]); c.fillStyle = C.surface; c.fill(); c.strokeStyle = "rgba(255,245,235,.12)"; c.lineWidth = 2; c.stroke();
  c.beginPath(); c.roundRect(W / 2 - 40, 1188, 80, 10, 5); c.fillStyle = "rgba(255,245,235,.25)"; c.fill();
  c.font = `700 30px ${K.F}`; c.fillStyle = C.dim; c.textAlign = "left"; c.textBaseline = "middle"; c.fillText("Colour", 60, 1236);
  COLOURS.forEach(([id, col], i) => {
    const x = SW_X(i), on = look.color === id, tapAt = TAPS.find(([at, p, v]) => p === "color" && v === id)?.[0];
    const k = tapAt != null ? 1 + .18 * Math.max(0, Math.sin(clamp((t - tapAt) / .3) * Math.PI)) : 1;
    c.save(); c.translate(x, SW_Y); c.scale(k, k);
    if (col) c.fillStyle = col; else { const g = c.createLinearGradient(-38, -38, 38, 38); g.addColorStop(0, "#ff7ab8"); g.addColorStop(.5, "#8a7bff"); g.addColorStop(1, "#4fd6c8"); c.fillStyle = g; }
    c.beginPath(); c.arc(0, 0, 38, 0, Math.PI * 2); c.fill();
    if (on) { c.strokeStyle = "#fff8f0"; c.lineWidth = 6; c.beginPath(); c.arc(0, 0, 48, 0, Math.PI * 2); c.stroke(); }
    c.restore();
  });
  c.font = `700 30px ${K.F}`; c.fillStyle = C.dim; c.fillText("Wear", 60, 1386);
  let x = 60; chipX = [];
  WEAR.forEach(([id, label]) => {
    c.font = `800 34px ${K.F}`; const w = c.measureText(label).width + 52, on = look.wear === id, tapAt = TAPS.find(([at, p, v]) => p === "wear" && v === id)?.[0];
    const k = tapAt != null ? 1 + .12 * Math.max(0, Math.sin(clamp((t - tapAt) / .3) * Math.PI)) : 1;
    c.save(); c.translate(x + w / 2, CH_Y); c.scale(k, k);
    c.beginPath(); c.roundRect(-w / 2, -34, w, 68, 34); c.fillStyle = on ? C.btn : C.raised; c.fill();
    c.fillStyle = on ? C.ink : C.text; c.textAlign = "center"; c.fillText(label, 0, 2); c.restore();
    chipX.push([id, x + w / 2]); x += w + 14;
  });
  c.restore();
}
const CAPS = [
  [0.1, 2.9, "dressing up my accountability buddy"],
  [3.1, 7.9, "new looks unlock as it grows"],
  [REVEAL + .1, 10.7, "final look. thoughts?"],
];

export default {
  dur: 13.4,
  caption: "Dressing up my accountability buddy. Every look is earned by levelling up, never bought. Final look: thoughts?",
  tags: "#cozygames #cute #dressup #habittracker #selfcare",
  sounds: [...TAPS.flatMap(([at], i) => [["tap", at - .05], ["boop", at, i]]), ["rise", REVEAL - .55], ["boom", REVEAL], ["unlock", REVEAL + .05], ["sparkle", REVEAL + .1], ["chime", END + .1]],
  init() { e = makeEmber(780); e.state.level = { level: 25, stage: "Blaze" }; },
  draw(t) {
    if (t < END + .5) {
      const look = lookAt(t), last = [...TAPS].reverse().find(([at]) => t >= at), since = last ? t - last[0] : 9;
      bg(720, t >= REVEAL ? 1 : .7);
      e.state.look = look;
      e.face(t >= REVEAL ? (t < REVEAL + .4 ? "surprised" : "eager") : since < .28 ? "surprised" : "happy", t >= REVEAL ? 1 : .85);
      if (TAPS.some(([at]) => t >= at && t < at + 1 / 30)) e.burst(10);
      if (t >= REVEAL && t < REVEAL + 1 / 30) e.burst(40);
      // the reveal: the sheet slides away and Ember comes forward
      const r = out3((t - REVEAL) / .5);
      if (t < END) ember(e, t, W / 2, 740 + r * 140, 780 + r * 160);
      pill("Pip · Lv 25", W / 2, 1095 + r * 260, { size: 38, fill: C.raised, color: C.text });
      c.save(); c.translate(0, r * 800); sheet(t, look); c.restore();
      for (const [at, part, value] of TAPS) {
        if (part === "color") tap(t, at - .08, SW_X(COLOURS.findIndex(([id]) => id === value)), SW_Y);
        else { const cx = chipX.find(([id]) => id === value); if (cx) tap(t, at - .08, cx[1], CH_Y); }
      }
      K.flash(t, REVEAL, .35, .6);
      K.captions(t, CAPS);
    }
    if (t >= END) endCard(t, END, e, "New looks open as you level up");
    K.grain();
  },
};
