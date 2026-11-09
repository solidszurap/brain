// Hook test 3 (2026-11-09), a quiet question: "when did you last lose track of time?" Opens on filmed footage
// (clips/bus.mp4, made with Higgsfield: someone on a night bus, head on the window, who looks down at their phone),
// and the question turns out to be Ember's: two answers later it's a 7-day experiment, started. Ends by asking you.
import * as K from "../kit.js";
const { makeEmber, clamp, endCard } = window;
const HOOK = 3.6, CUT = 9.0, TRY = 11.0, END = 12.5;
let e;
const clipAt = t => .15 + t * 1.33;

const chat = {
  title: "Our first chat",
  clock: () => "23:12",
  face: K.timeline([[0, "curious", .8], [5.7, "happy", .85], [6.2, "curious", .8], [7.9, "worried", .65], [8.2, "thinking", .7],
    [CUT + .2, "eager", .95], [TRY, "happy", 1]]),
  level: () => ({ level: 2, stage: "Spark" }),
  typing: [{ from: 4.15, to: 5.5, text: "drawing. but I haven't in years", send: 5.7 }, { from: 7.15, to: 7.7, text: "life, I guess", send: 7.9 }],
  keyboard: [[3.6, 8.3]],
  fresh: CUT,
  msgs: [
    { who: "ember", text: "When do you lose track of time?", at: 0 },
    { who: "you", text: "drawing. but I haven't in years", at: 5.7 },
    { who: "ember", text: "What made you stop?", at: 6.2 },
    { who: "you", text: "life, I guess", at: 7.9 },
    { who: "dots", at: 8.2, end: CUT },
    { who: "card", at: CUT + .2, title: "A 7-day experiment", lines: ["Draw for 15 minutes every evening.", "Each night, tell me: did it give you energy, or drain you?"], button: "Try it", tap: TRY },
  ],
  xp: [{ at: TRY + .15, text: "+20 XP", until: END - .1 }],
};
const CAM = [
  { t: 0, x: 540, y: 1180, w: 1150, r: -.03 }, { t: HOOK, x: 540, y: 1180, w: 1150, r: -.03 },
  { t: HOOK + .55, x: 540, y: 1290, w: 820, r: 0 }, { t: CUT - .1, x: 540, y: 1270, w: 845, r: 0 },
  { t: CUT, cut: true, x: 540, y: 1150, w: 790, r: 0 }, { t: END, x: 540, y: 1130, w: 820, r: 0 },
];
const CAPS = [
  [0.15, 3.5, "when did you last lose track of time?"],
  [3.85, 5.9, "an app asked me this at 11pm"],
  [6.2, 8.8, "it didn't give me advice"],
  [CUT + .2, TRY + .1, "it gave me a 7 day experiment"],
  [TRY + .35, END - .05, "so. what's your answer?"],
];

export default {
  dur: END + 2.5,
  clips: { bus: "bus.mp4" },
  caption: "When did you last lose track of time? An app asked me that at 11pm. It didn't give me advice, it gave me a 7 day experiment. What's your answer? Tell me below.",
  tags: "#findyourpurpose #selfdiscovery #latenightthoughts #purpose #whatdoiwant",
  sounds: [["whoosh", HOOK - .2], ...K.chatSounds(chat), ["whoosh", CUT - .05], ["unlock", TRY], ["sparkle", TRY + .1], ["xp", TRY + .15], ["chime", END + .1]],
  init() { e = makeEmber(640); },
  async prep(t) { if (t < HOOK + .35) await window.clipSeek("bus", clipAt(t)); },
  draw(t) {
    const cam = K.camera(t, CAM);
    if (t < END + .5) {
      if (t >= HOOK - .05) { K.chatScreen(t, chat, e, t < END); K.room(cam, 222, .22); K.phone(cam); }
      // her eyes drop to her phone, and so do we: the footage pushes in towards it as ours fades in
      const k = clamp((t - (HOOK - .1)) / .4);
      if (k < 1) window.clipDraw("bus", { zoom: 1 + t * .018 + k * k * .9, fx: .52, fy: .5 + k * .3, alpha: 1 - k * k });
      K.captions(t, CAPS);
    }
    if (t >= END) endCard(t, END, e, "Find your purpose. Then live it.");
    K.grain();
  },
};
