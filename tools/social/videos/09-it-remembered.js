// Day 9: "I mentioned this once. 3 weeks ago." You tell Ember about losing track of time on a flyer; three weeks
// later you're bored, and it brings your exact words back with a plan. It ends on the real memory page, where the
// same words and their date are kept (web/img/shot-knows.webp: "Fixing up my friend's flyer last week..." Oct 12).
import * as K from "../kit.js";
const { makeEmber, clamp, out3, endCard } = window;
const END = 14.6, CUT = 4.0, MEM = 11.9;
let e;

const chat = {
  title: "Our first chat",
  clock: t => t >= CUT ? "10:02" : "21:14",
  face: K.timeline([[0, "calm", .7], [2.7, "curious", .8], [3.1, "happy", .85], [CUT, "calm", .7], [5.7, "thinking", .7], [6.9, "eager", .9],
    [10.4, "amused", .85], [10.9, "happy", .9]]),
  level: () => ({ level: 4, stage: "Spark" }),
  typing: [
    { from: .35, to: 2.45, text: "fixing up my friend's flyer last week, I didn't notice two hours go by", send: 2.7 },
    { from: 4.45, to: 5.5, text: "bored. no idea what to do this weekend", send: 5.7 },
    { from: 9.35, to: 10.15, text: "wait how do you remember that", send: 10.4 },
  ],
  keyboard: [[0, CUT], [CUT + .05, MEM]],
  fresh: CUT,
  msgs: [
    { who: "you", text: "fixing up my friend's flyer last week, I didn't notice two hours go by", at: 2.7 },
    { who: "ember", text: "Two hours without noticing is a real clue. I'll remember that.", at: 3.1 },
    { who: "you", text: "bored. no idea what to do this weekend", at: 5.7 },
    { who: "dots", at: 6.0, end: 6.9 },
    { who: "ember", text: "On Oct 12 you said you didn't notice two hours go by, fixing a flyer. Design something of your own on Saturday?", at: 6.9 },
    { who: "you", text: "wait how do you remember that", at: 10.4 },
    { who: "ember", text: "You told me. I keep your words, with the date.", at: 10.9 },
  ],
};
const fit = (t, sy, w) => ({ t, x: 540, y: 900 + (w * K.SH / K.SW) / 2 - sy * w / K.SW, w, r: 0 });
const CAM = [
  { t: 0, x: 540, y: 1290, w: 830, r: -.01 }, { t: CUT - .3, x: 540, y: 1280, w: 845, r: 0 },
  { t: CUT, cut: true, x: 540, y: 1290, w: 830, r: 0 }, { t: MEM - .2, x: 540, y: 1270, w: 860, r: 0 },
  fit(MEM + .35, 1172, 980), fit(END, 1172, 1010),
];
const CAPS = [
  [0.1, 3.75, "I mentioned this once. 3 weeks ago."],
  [7.0, 9.3, "it remembered my exact words"],
  [MEM + .1, 14.4, "and you can read everything it remembers"],
];

export default {
  dur: 17.1,
  caption: "I mentioned this once, 3 weeks ago. It remembered my exact words, and the date. You can read everything it remembers.",
  tags: "#aicompanion #journaling #selfdiscovery #findyourpurpose #creative",
  sounds: [...K.chatSounds(chat), ["whoosh", CUT - .3], ["whoosh", MEM - .05], ["boop", MEM + .45, 5], ["sparkle", 7.0], ["chime", END + .1]],
  init() { e = makeEmber(640); },
  draw(t) {
    const cam = K.camera(t, CAM);
    if (t < END + .5) {
      if (t < MEM) K.chatScreen(t, chat, e, t < END);
      else {
        if (t < END) e.at(t);
        const k = out3((t - MEM) / .3);
        K.s.save(); K.s.translate((1 - k) * K.SW, 0); K.shotScreen("knows"); K.spotlight(32, 1004, 708, 340, clamp((t - MEM - .4) / .3)); K.s.restore();
        if (k < 1) { K.s.save(); K.s.translate(-k * K.SW, 0); K.chatScreen(t, chat, e, false); K.s.restore(); }
      }
      K.room(cam); K.phone(cam);
      K.captions(t, CAPS);
      K.titleCard(t, CUT, "3 weeks later");
    }
    if (t >= END) endCard(t, END, e, "It remembers your story, in your words");
    K.grain();
  },
};
