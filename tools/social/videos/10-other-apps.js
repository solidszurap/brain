// Day 10: "other apps when you miss a day" vs "Ember when you miss a day". A harsh red notification (a made-up,
// unnamed habit app) with a sad trombone, swiped away; then Ember's kind one, and a chat with no guilt in it.
// Honest: a missed day does end a streak in Ember too, but levels and badge levels never go down.
import * as K from "../kit.js";
const { makeEmber, clamp, endCard } = window;
const END = 11.7, SWIPE = 3.3, OPEN = 6.3;
let e;

const lock = {
  time: "21:30", date: "Thursday 6 November",
  notes: [
    { at: .45, title: "Habit Tracker", icon: "other", red: true, text: "You lost your 47-day streak. Start over from zero?", out: SWIPE },
    { at: 3.8, text: "Rough day? That's okay. Tomorrow, just 5 minutes. I'm here." },
  ],
};
const chat = {
  title: "Run 10 minutes a day",
  clock: () => "21:31",
  face: K.timeline([[0, "worried", .55], [OPEN, "calm", .65], [8.1, "worried", .6], [8.4, "thinking", .6], [9.1, "calm", .75], [10.5, "happy", .85]]),
  level: () => ({ level: 8, stage: "Ember" }),
  typing: [{ from: 6.95, to: 7.9, text: "sorry, today was a lot", send: 8.1 }, { from: 9.9, to: 10.3, text: "deal.", send: 10.5 }],
  keyboard: [[6.6, END + 1]],
  msgs: [
    { who: "check", how: "Not today", step: "run 10 minutes", at: 0 },
    { who: "ember", text: "Rough day? That's okay. Tomorrow, just 5 minutes. I'm here.", at: 0 },
    { who: "you", text: "sorry, today was a lot", at: 8.1 },
    { who: "dots", at: 8.4, end: 9.1 },
    { who: "ember", text: "No sorry needed. Some days are like that. See you tomorrow?", at: 9.1 },
    { who: "you", text: "deal.", at: 10.5 },
  ],
};
const CAM = [
  { t: 0, x: 540, y: 1150, w: 760, r: -.02 }, { t: OPEN - .3, x: 540, y: 1140, w: 790, r: -.01 },
  { t: OPEN + .35, x: 540, y: 1290, w: 830, r: 0 }, { t: END, x: 540, y: 1275, w: 850, r: 0 },
];
const CAPS = [
  [0.1, 3.2, "other apps when you miss a day:"],
  [3.6, 6.2, "Ember when you miss a day:"],
  [6.6, 9.0, "no guilt trip. just a smaller step tomorrow"],
  [9.2, 11.5, "your levels never go down"],
];

export default {
  dur: 14.2,
  caption: "Other apps when you miss a day vs Ember when you miss a day. No guilt trip, just a smaller step tomorrow. Your levels never go down.",
  tags: "#selfcompassion #habits #mentalhealth #streak #accountability",
  sounds: [["buzz", .4], ["bonk", .45], ["sad", .85], ["whoosh", SWIPE], ["buzz", 3.75], ["ding", 3.8], ["tap", OPEN - .15], ["whoosh", OPEN], ...K.chatSounds(chat), ["chime", END + .1]],
  init() { e = makeEmber(640); e.state.level = { level: 8, stage: "Ember" }; },
  draw(t) {
    const cam = K.camera(t, CAM, [[.45, .75, 9]]);
    if (t < END + .5) {
      if (t < OPEN) { if (t < END) e.at(t); const r = K.lockScreen(t, lock); const em = r.find(x => !x.n.red); if (em) K.ring(t, OPEN - .15, K.SW / 2, em.y + 80); }
      else {
        K.chatScreen(t, chat, e, t < END);
        const k = clamp((t - OPEN) / .3);
        if (k < 1) { K.s.save(); K.s.globalAlpha = 1 - k; K.lockScreen(t, lock); K.s.restore(); }
      }
      K.room(cam, t < SWIPE ? 8 : 26, t < SWIPE ? .26 : .3); K.phone(cam);
      K.captions(t, CAPS);
    }
    if (t >= END) endCard(t, END, e, "No guilt. Just the next small step.");
    K.grain();
  },
};
