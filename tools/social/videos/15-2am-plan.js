// Hook test 1 (2026-11-09), recognition: "POV: it's 2am and you're changing your whole life. again." Opens on filmed
// footage (clips/bed.mp4, made with Higgsfield: someone in bed lit by their phone looks up, caught out, and lifts the
// phone into the lens), then the phone is ours: the 2am plan, Ember makes them pick one small thing, and the next day
// at 18:00 it checks, and it happened.
import * as K from "../kit.js";
const { makeEmber, clamp, endCard } = window;
const HOOK = 3.7, CUT = 10.6, NOTE = 11.0, OPEN = 12.1, CHIP = 13.0, END = 15.2;
let e;
// the clip: the scrolling at the start runs faster, so the look into the camera comes at 1.6 s
const clipAt = t => t < 1.5 ? .3 + t * 2.3 / 1.5 : 2.6 + (t - 1.5);

const lock = { time: "18:00", date: "Wednesday 11 November", notes: [{ at: NOTE, text: "Did the 10 minutes happen?" }] };
const chat = {
  title: "Our first chat",
  clock: t => t >= CUT ? "18:01" : "2:07",
  face: K.timeline([[0, "curious", .6], [5.6, "surprised", .75], [5.8, "thinking", .65], [6.5, "happy", .85], [8.2, "eager", .9],
    [CUT, "curious", .8], [CHIP, "happy", 1]]),
  level: () => ({ level: 1, stage: "Spark" }),
  typing: [{ from: 4.0, to: 5.4, text: "new me: gym at 6am, read 30 books, learn spanish, start a business", send: 5.6 },
    { from: 7.65, to: 8.0, text: "the gym one", send: 8.2 }],
  keyboard: [[3.7, 8.45]],
  fresh: CUT,
  msgs: [
    { who: "you", text: "new me: gym at 6am, read 30 books, learn spanish, start a business", at: 5.6 },
    { who: "dots", at: 5.85, end: 6.5 },
    { who: "ember", text: "I love 2am you. Let's keep one of those alive. Which one matters most?", at: 6.5 },
    { who: "you", text: "the gym one", at: 8.2 },
    { who: "ember", text: "Then tomorrow: 10 minutes of moving. That's all. I'll check on you at 18:00.", at: 8.65 },
    { who: "ember", text: "Did the 10 minutes happen?", at: OPEN },
    { who: "chips", at: OPEN + .3, tap: CHIP, pick: 0 },
    { who: "ember", text: "Day 1. Your first 2am plan that made it to daylight.", at: CHIP + .5 },
  ],
  xp: [{ at: CHIP + .1, text: "+10 XP", until: END - .1 }],
};
const CAM = [
  { t: 0, x: 540, y: 1290, w: 1500, r: .06 }, { t: HOOK, x: 540, y: 1290, w: 1500, r: .06 },
  { t: HOOK + .5, x: 540, y: 1290, w: 820, r: 0 }, { t: CUT - .3, x: 540, y: 1270, w: 845, r: 0 },
  { t: CUT, cut: true, x: 540, y: 1000, w: 610, r: -.04 }, { t: OPEN - .15, x: 540, y: 985, w: 650, r: -.02 },
  { t: OPEN + .35, x: 540, y: 1134, w: 780, r: 0 }, { t: END, x: 540, y: 1124, w: 800, r: 0 },
];
const CAPS = [
  [0.1, 1.55, "POV: it's 2am"],
  [1.65, 3.55, "and you're changing your whole life. again."],
  [3.95, 6.3, "so I told the app my new plan"],
  [6.55, 10.3, "it didn't hype me up. it made me pick one."],
  [NOTE + .1, OPEN + .6, "and the next day it actually checked"],
  [CHIP + .5, END - .1, "first 2am plan that survived the morning"],
];
function screen(t, step) {
  if (t >= CUT && t < OPEN) { if (step) e.at(t); const r = K.lockScreen(t, lock); if (r[0]) K.ring(t, OPEN - .15, K.SW / 2, r[0].y + 80); return; }
  K.chatScreen(t, chat, e, step);
  const k = clamp((t - OPEN) / .3);
  if (t >= OPEN && k < 1) { K.s.save(); K.s.globalAlpha = 1 - k; K.lockScreen(t, lock); K.s.restore(); }
}

export default {
  dur: END + 2.5,
  clips: { bed: "bed.mp4" },
  caption: "POV: it's 2am and you're changing your whole life. Again. This time I told Ember. It made me pick ONE thing, 10 minutes, and the next day it actually checked. Which plan do you keep making at 2am?",
  tags: "#2amthoughts #newme #selfimprovement #accountability #relatable",
  sounds: [["tick", 1.62, -5], ["whoosh", HOOK - .3], ["thump", HOOK - .02], ...K.chatSounds(chat).filter(x => x[1] < CUT || x[1] > OPEN - .2),
    ["whoosh", CUT - .3], ...K.lockSounds(lock.notes), ["whoosh", OPEN], ["thump", CHIP], ["xp", CHIP + .1], ["chime", END + .1]],
  init() { e = makeEmber(640); },
  async prep(t) { if (t < HOOK + .1) await window.clipSeek("bed", clipAt(t)); },
  draw(t) {
    const cam = K.camera(t, CAM, [[NOTE, NOTE + .35, 6]]);
    if (t < END + .5) {
      if (t >= HOOK - .05) { screen(t, t < END); K.room(cam, t >= CUT ? 26 : 222, t >= CUT ? .3 : .22); K.phone(cam); }
      if (t < HOOK) {
        const rush = clamp((t - (HOOK - .3)) / .3);        // the phone coming at the lens: a last push in, then white
        window.clipDraw("bed", { zoom: 1 + t * .022 + rush * rush * .5, fx: .5, fy: .36 });
      }
      K.flash(t, HOOK - .12, .45, 1);
      K.captions(t, CAPS);
      K.titleCard(t, CUT, "the next day");
    }
    if (t >= END) endCard(t, END, e, "Your companion who checks up on you");
    K.grain();
  },
};
