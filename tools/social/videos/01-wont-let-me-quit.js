// Day 1: "the app that won't let me quit". Day 3 of running: Ember buzzes, you make an excuse, it makes the step
// smaller instead of guilt-tripping, you go, and 45 minutes later it's a 4-day streak and a level up.
import * as K from "../kit.js";
const { makeEmber, clamp, endCard } = window;
const END = 13.6, CUT = 10.75, CHIP = 12.0, LEVEL = 12.1;
let e;

const lock = { time: "18:00", notes: [{ at: .5, text: "Day 3. Still on for 10 minutes of running?" }] };
const chat = {
  title: "Run 10 minutes a day",
  clock: t => t >= CUT ? "18:47" : "18:01",
  face: K.timeline([[0, "curious", .7], [5.2, "surprised", .7], [5.5, "thinking", .65], [6.8, "calm", .7], [9.3, "eager", .95], [10.5, "curious", .8], [CHIP, "happy", 1]]),
  level: t => ({ level: t >= LEVEL ? 6 : 5, stage: "Ember" }), levelAt: LEVEL,
  typing: [{ from: 3.45, to: 5.0, text: "not today, I'm tired", send: 5.2 }, { from: 8.55, to: 9.05, text: "...fine", send: 9.3 }],
  keyboard: [[3.1, 9.45]],
  fresh: CUT,
  msgs: [
    { who: "ember", text: "Day 3. Still on for 10 minutes of running?", at: 0 },
    { who: "you", text: "not today, I'm tired", at: 5.2 },
    { who: "dots", at: 5.5, end: 6.8 },
    { who: "ember", text: "Fair. What about 5 minutes? Just to the corner and back.", at: 6.8 },
    { who: "you", text: "...fine", at: 9.3 },
    { who: "ember", text: "Shoes on. I'll be right here.", at: 9.9 },
    { who: "ember", text: "You're back! How did the 5 minutes go?", at: 11.15 },
    { who: "chips", at: 11.45, tap: CHIP, pick: 0 },
    { who: "ember", text: "4 days in a row. You almost skipped today, and you didn't.", at: 12.55 },
  ],
  xp: [{ at: 12.2, text: "+10 XP", until: 13.5 }],
};
const CAM = [
  { t: 0, x: 540, y: 1000, w: 600, r: -.05 }, { t: 2.4, x: 540, y: 980, w: 650, r: -.03 },
  { t: 3.05, x: 540, y: 1290, w: 820, r: 0 }, { t: 10.4, x: 540, y: 1270, w: 845, r: 0 },
  { t: CUT, cut: true, x: 540, y: 1134, w: 780, r: 0 }, { t: CUT + 3, x: 540, y: 1124, w: 800, r: 0 },
];
const CAPS = [
  [0.15, 2.45, "day 3 of trying to become a runner"],
  [3.0, 5.6, "me, already making excuses"],
  [5.9, 8.5, "it didn't guilt trip me. it made it smaller"],
  [8.7, 10.4, "ok fine. 5 minutes."],
  [11.2, 13.5, "now I'm on a 4 day streak"],
];
function screen(t, step) {
  if (t < 2.45) { if (step) e.at(t); const r = K.lockScreen(t, lock); if (r[0]) K.ring(t, 2.25, K.SW / 2, r[0].y + 80); return; }
  K.chatScreen(t, chat, e, step);
  const k = clamp((t - 2.45) / .35);
  if (k < 1) { K.s.save(); K.s.globalAlpha = 1 - k; K.s.translate(K.SW / 2, 600); K.s.scale(1 + k * .15, 1 + k * .15); K.s.translate(-K.SW / 2, -600); K.lockScreen(t, lock); K.s.restore(); }
}

export default {
  dur: 16,
  caption: "Day 3 of trying to become a runner. I tried to skip. It didn't guilt trip me, it made the step smaller. Now I'm on a 4 day streak.",
  tags: "#running #accountability #habits #selfimprovement #motivation",
  sounds: [...K.lockSounds(lock.notes), ["buzz", 1.35], ["tap", 2.25], ["whoosh", 2.45], ...K.chatSounds(chat),
    ["whoosh", CUT - .3], ["levelup", LEVEL], ["xp", 12.2], ["chime", END + .1]],
  init() { e = makeEmber(640); },
  draw(t) {
    const cam = K.camera(t, CAM, [[.45, .8], [1.35, 1.7]]);
    if (t < END + .5) {
      screen(t, t < END);
      K.room(cam); K.phone(cam);
      K.captions(t, CAPS);
      K.titleCard(t, CUT, "45 minutes later");
    }
    if (t >= END) endCard(t, END, e, "Your companion who checks up on you");
    K.grain();
  },
};
