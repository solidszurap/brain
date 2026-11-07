// Day 3: "what showing up every day does to your Ember". A day counter rolls on and Ember transforms at each
// stage (Spark, Ember, Flame, Blaze) with a flash, a boom and the looks it unlocked. The days are about right for
// someone who checks in daily (level 5 ≈ 500 XP ≈ 2 weeks, 10 ≈ 2 months, 20 ≈ 8 months).
import * as K from "../kit.js";
const { W, C, makeEmber, clamp, out3, back, appear, bg, say, ember, pill, endCard } = window;
const c = window.c;
const END = 12.7;
let e;

// [the moment it transforms, day, level, stage, look, what it unlocked, caption]
const STAGES = [
  [0, 1, 1, "Spark", {}, null],
  [3.4, 12, 5, "Ember", { wear: "scarf" }, "a scarf"],
  [6.6, 55, 10, "Flame", { wear: "glasses", glow: "halo", eyes: "sparkly" }, "a halo ring"],
  [9.8, 230, 20, "Blaze", { wear: "crown", glow: "halo", sparks: "stars", eyes: "sparkly", cheeks: "hearts" }, "a little crown"],
];
const ROLL = .8;   // the counter rolls for this long before each change
const CAPS = [
  [0.1, 2.6, "what showing up every day does to your Ember"],
  [3.5, 6.0, "two weeks in"],
  [6.7, 9.2, "two months in"],
  [9.9, 12.5, "eight months in. it wears a crown now"],
];
function stageAt(t) { let i = 0; for (let k = 0; k < STAGES.length; k++) if (t >= STAGES[k][0]) i = k; return i; }
function dayAt(t) {
  const i = stageAt(t), next = STAGES[i + 1];
  if (next && t > next[0] - ROLL) return Math.round(STAGES[i][1] + (next[1] - STAGES[i][1]) * out3((t - (next[0] - ROLL)) / ROLL));
  return STAGES[i][1];
}

export default {
  dur: 15.3,
  caption: "What showing up every day does to your Ember. Two weeks, two months, eight months. Every level is earned by showing up.",
  tags: "#glowup #levelup #habits #cozygames #selfimprovement",
  sounds: [
    ...STAGES.slice(1).flatMap(([at], n) => [
      ["rise", at - ROLL],
      ...Array.from({ length: 12 }, (_, k) => ["tick", at - ROLL + k * ROLL / 12, k + n * 3]),
      ["boom", at], ["levelup", at + .05], ["sparkle", at + .1], ["unlock", at + .35],
    ]),
    ["chime", END + .1],
  ],
  init() { e = makeEmber(860); },
  draw(t) {
    const i = stageAt(t), [at, , level, stage, look, unlocked] = STAGES[i], since = t - at;
    if (t < END + .5) {
      // a shake as it transforms
      const sh = i > 0 && since < .35 ? (1 - since / .35) * 14 : 0;
      c.save(); c.translate(Math.sin(t * 90) * sh, Math.cos(t * 70) * sh);
      bg(930, .45 + i * .17);
      e.state.level = { level, stage }; e.state.look = look;
      e.face(i > 0 && since < .7 ? "surprised" : i === 3 ? "eager" : "happy", .75 + i * .08);
      ember(e, t, W / 2, 930, 860);
      // the day counter
      const day = dayAt(t), rolling = STAGES[i + 1] && t > STAGES[i + 1][0] - ROLL;
      pill(`Day ${day}`, W / 2, 440, { size: 54, fill: rolling ? C.btn : C.raised, color: rolling ? C.ink : C.text, scale: rolling ? 1.08 : 1 });
      say(stage, W / 2, 1290, { size: 112, color: C.btn, alpha: i ? appear(t, at, .25) : 1, rise: 20 });
      say(unlocked ? `Level ${level} · unlocked ${unlocked}` : `Level ${level}`, W / 2, 1420, { size: 48, weight: 800, color: C.dim, alpha: i ? appear(t, at + .35, .3) : 1, maxW: 960 });
      c.restore();
      if (i > 0) K.flash(t, at, .35, .55);
      K.captions(t, CAPS);
    }
    if (t >= END) endCard(t, END, e, "Grows from showing up, never from paying");
    K.grain();
  },
};
