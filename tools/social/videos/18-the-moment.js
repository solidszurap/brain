// Hook test 4 (2026-11-09), a curiosity gap with a sting: "the exact moment your goal dies". Opens on filmed footage
// (clips/shoes.mp4, made with Higgsfield: running shoes by the door, a hand reaches, hesitates and pulls back),
// "and nobody notices", except Ember's message lands right then, makes the step smaller, and they go.
import * as K from "../kit.js";
const { c, makeEmber, clamp, out3, lines, endCard } = window;
const BANNER = 3.4, OPEN = 4.55, CUT = 10.5, CHIP = 11.8, LEVEL = 11.9, END = 13.9;
const F = K.F, ASK = "Day 4. Still on for your morning run?";
let e;
const clipAt = t => .6 + t;

const chat = {
  title: "Run every morning",
  clock: t => t >= CUT ? "7:14" : "6:42",
  face: K.timeline([[0, "curious", .7], [6.2, "surprised", .7], [6.4, "thinking", .65], [7.2, "calm", .7], [9.2, "eager", .95],
    [CUT, "curious", .8], [CHIP, "happy", 1]]),
  level: t => ({ level: t >= LEVEL ? 6 : 5, stage: "Ember" }), levelAt: LEVEL,
  typing: [{ from: 4.9, to: 6.0, text: "no. it's cold and I'm tired", send: 6.2 }, { from: 8.6, to: 9.0, text: "...ok fine", send: 9.2 }],
  keyboard: [[4.6, 9.4]],
  fresh: CUT,
  msgs: [
    { who: "ember", text: ASK, at: 0 },
    { who: "you", text: "no. it's cold and I'm tired", at: 6.2 },
    { who: "dots", at: 6.4, end: 7.2 },
    { who: "ember", text: "Fair. Then just shoes on, to the end of the street. 3 minutes.", at: 7.2 },
    { who: "you", text: "...ok fine", at: 9.2 },
    { who: "ember", text: "I'll be right here.", at: 9.6 },
    { who: "ember", text: "You went! How was it?", at: CUT + .4 },
    { who: "chips", at: CUT + .7, tap: CHIP, pick: 0 },
    { who: "ember", text: "5 days in a row. Today was the one that counted.", at: CHIP + .5 },
  ],
  xp: [{ at: CHIP + .15, text: "+10 XP", until: END - .1 }],
};
const CAM = [
  { t: 0, x: 540, y: 1290, w: 1300, r: 0 }, { t: OPEN, x: 540, y: 1290, w: 1300, r: 0 },
  { t: OPEN + .5, x: 540, y: 1290, w: 820, r: 0 }, { t: CUT - .3, x: 540, y: 1270, w: 845, r: 0 },
  { t: CUT, cut: true, x: 540, y: 1134, w: 780, r: 0 }, { t: END, x: 540, y: 1124, w: 800, r: 0 },
];
const CAPS = [
  [0.1, 2.3, "the exact moment your goal dies"],
  [2.4, 3.35, "and nobody notices"],
  [BANNER + .45, OPEN + .1, "except this.", 620],
  [4.9, 6.9, "me, with my excuse ready"],
  [7.2, 9.5, "it didn't guilt me. it made it smaller."],
  [CUT + .4, END - .1, "5 days in a row now"],
];
// Ember's notification dropping in over the footage, as on your own phone; returns where to tap it
function banner(t) {
  const k = out3((t - BANNER) / .4), gone = clamp((t - OPEN) / .2); if (k <= 0 || gone >= 1) return null;
  const x = 60, w = 960, ls = lines(ASK, w - 250, `500 42px ${F}`), h = 150 + ls.length * 54, y = -h - 40 + k * (h + 360);
  c.save(); c.globalAlpha = 1 - gone; c.shadowColor = "rgba(0,0,0,.55)"; c.shadowBlur = 60; c.shadowOffsetY = 18;
  c.beginPath(); c.roundRect(x, y, w, h, 50); c.fillStyle = "#33261d"; c.fill(); c.shadowColor = "transparent";
  c.strokeStyle = "rgba(255,240,228,.12)"; c.lineWidth = 2; c.stroke();
  if (window.IMGS?.icon) { c.save(); c.beginPath(); c.roundRect(x + 40, y + 40, 96, 96, 23); c.clip(); c.drawImage(window.IMGS.icon, x + 40, y + 40, 96, 96); c.restore(); }
  c.textBaseline = "middle"; c.textAlign = "left"; c.font = `800 42px ${F}`; c.fillStyle = "#fff4e8"; c.fillText("Ember sent you a message", x + 166, y + 68);
  c.textAlign = "right"; c.font = `600 36px ${F}`; c.fillStyle = "rgba(255,240,228,.6)"; c.fillText("now", x + w - 44, y + 68);
  c.textAlign = "left"; c.font = `500 42px ${F}`; c.fillStyle = "rgba(255,244,232,.92)"; ls.forEach((l, i) => c.fillText(l, x + 166, y + 126 + i * 54));
  c.restore(); return [x + w / 2, y + h / 2];
}

export default {
  dur: END + 2.5,
  clips: { shoes: "shoes.mp4" },
  caption: "This is the exact moment your goal dies. Not in January. On a random morning, when nobody notices. Mine got a message right then: it didn't guilt me, it made the step smaller. 5 days in a row now.",
  tags: "#running #discipline #habits #accountability #selfimprovement",
  sounds: [["buzz", BANNER - .05], ["ding", BANNER], ["tap", OPEN - .15], ["whoosh", OPEN - .05], ...K.chatSounds(chat),
    ["whoosh", CUT - .3], ["thump", CHIP], ["levelup", LEVEL], ["xp", CHIP + .15], ["chime", END + .1]],
  init() { e = makeEmber(640); },
  async prep(t) { if (t < OPEN + .4) await window.clipSeek("shoes", clipAt(t)); },
  draw(t) {
    const cam = K.camera(t, CAM);
    if (t < END + .5) {
      if (t >= OPEN - .05) { K.chatScreen(t, chat, e, t < END); K.room(cam); K.phone(cam); }
      const k = clamp((t - OPEN) / .3);
      if (k < 1) {
        const shake = t > BANNER && t < BANNER + .35 ? Math.sin(t * 95) * 5 : 0;
        window.clipDraw("shoes", { zoom: 1.02 + t * .02 + k * .5, fx: .6, fy: .7, dx: shake, alpha: 1 - k });
        const at = banner(t);
        if (at) { const r = (t - (OPEN - .15)) / .45; if (r > 0 && r < 1) { c.save(); c.globalAlpha = (1 - r) * .9; c.strokeStyle = "#fff"; c.lineWidth = 8; c.beginPath(); c.arc(at[0], at[1], 30 + r * 70, 0, Math.PI * 2); c.stroke(); c.restore(); } }
      }
      K.captions(t, CAPS);
      K.titleCard(t, CUT, "30 minutes later");
      K.flash(t, LEVEL, .35, .5);
    }
    if (t >= END) endCard(t, END, e, "Your companion who checks up on you");
    K.grain();
  },
};
