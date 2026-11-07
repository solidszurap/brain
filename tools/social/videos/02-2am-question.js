// Day 2: "it's 2am and I asked an app what to do with my life". Ember asks three questions you've never asked
// yourself, you answer, and it turns the answers into a 7-day experiment, which you start.
import * as K from "../kit.js";
const { makeEmber, endCard } = window;
const END = 14.8, CUT = 11.1, TRY = 13.4;
let e;

const chat = {
  title: "Our first chat",
  clock: () => "2:07",
  face: K.timeline([[0, "calm", .55], [2.6, "surprised", .7], [2.9, "thinking", .65], [3.8, "eager", .85], [4.6, "curious", .8],
    [6.5, "happy", .85], [7.0, "curious", .8], [8.8, "worried", .7], [9.2, "curious", .8], [10.8, "happy", .9],
    [CUT, "thinking", .7], [12.0, "eager", .95], [TRY, "happy", 1]]),
  level: () => ({ level: 2, stage: "Spark" }),
  typing: [
    { from: .45, to: 2.3, text: "I don't know what I want to do with my life", send: 2.55 },
    { from: 5.15, to: 6.2, text: "sketching. hours just go by", send: 6.45 },
    { from: 7.55, to: 8.55, text: "meetings. all day meetings", send: 8.8 },
    { from: 9.75, to: 10.55, text: "drawing comics", send: 10.8 },
  ],
  keyboard: [[0, 10.95]],
  fresh: CUT,
  msgs: [
    { who: "you", text: "I don't know what I want to do with my life", at: 2.55 },
    { who: "dots", at: 2.85, end: 3.8 },
    { who: "ember", text: "Let's find out together. Three quick questions.", at: 3.8 },
    { who: "ember", text: "When do you lose track of time?", at: 4.6 },
    { who: "you", text: "sketching. hours just go by", at: 6.45 },
    { who: "ember", text: "What drains you, even when it goes well?", at: 7.0 },
    { who: "you", text: "meetings. all day meetings", at: 8.8 },
    { who: "ember", text: "What did you love doing at 12?", at: 9.2 },
    { who: "you", text: "drawing comics", at: 10.8 },
    { who: "dots", at: CUT + .1, end: 12.0 },
    { who: "card", at: 12.0, title: "A 7-day experiment", lines: ["Sketch for 15 minutes every evening.", "Each night, tell me: did it give you energy, or drain you?"], button: "Try it", tap: TRY },
  ],
  xp: [{ at: TRY + .15, text: "+20 XP", until: END - .1 }],
};
const CAM = [
  { t: 0, x: 540, y: 1330, w: 800, r: -.02 }, { t: .9, x: 540, y: 1290, w: 830, r: 0 },
  { t: 10.9, x: 540, y: 1270, w: 850, r: 0 },
  { t: CUT, cut: true, x: 540, y: 1150, w: 790, r: 0 }, { t: END, x: 540, y: 1130, w: 820, r: 0 },
];
const CAPS = [
  [0.1, 2.75, "it's 2am and I asked an app what to do with my life"],
  [3.8, 6.6, "it didn't give me a quiz. it asked about me"],
  [7.0, 10.95, "questions I'd never asked myself"],
  [12.0, 14.6, "then it gave me a 7 day experiment"],
];

export default {
  dur: 17.3,
  caption: "2am, asked an app what to do with my life. It asked me 3 questions I'd never asked myself, then gave me a 7 day experiment instead of an answer.",
  tags: "#findyourpurpose #2am #lifeadvice #selfdiscovery #purpose",
  sounds: [...K.chatSounds(chat), ["whoosh", CUT - .05], ["unlock", TRY], ["sparkle", TRY + .1], ["xp", TRY + .15], ["chime", END + .1]],
  init() { e = makeEmber(640); },
  draw(t) {
    const cam = K.camera(t, CAM);
    if (t < END + .5) {
      K.chatScreen(t, chat, e, t < END);
      K.room(cam, 222, .22); K.phone(cam);
      K.captions(t, CAPS);
    }
    if (t >= END) endCard(t, END, e, "Find your purpose. Then live it.");
    K.grain();
  },
};
