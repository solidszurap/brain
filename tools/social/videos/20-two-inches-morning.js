// "2 inches tall", episode 3 (2026-11-10): the morning. Ember on the kitchen counter (clips/kitchen.mp4), then in the
// phone: the daily question, one tap, and the longest run so far.
import { episode } from "../series.js";
import * as K from "../kit.js";
const CHIP = 5.3, LEVEL = 6.9, END = 9.6;
const chat = {
  title: "Spanish, 10 minutes a day",
  clock: () => "7:12",
  face: K.timeline([[0, "curious", .85], [CHIP, "happy", .95], [LEVEL, "happy", 1]]),
  level: t => ({ level: t >= LEVEL ? 7 : 6, stage: "Ember" }), levelAt: LEVEL,
  msgs: [
    { who: "ember", text: "Morning. Day 12 of Spanish. Did yesterday happen?", at: 0 },
    { who: "chips", at: .2, tap: CHIP, pick: 0 },
    { who: "ember", text: "12 days in a row. Your longest one yet.", at: CHIP + .6 },
  ],
  xp: [{ at: CHIP + .15, text: "+10 XP", until: END - .1 }],
};
export default episode({
  clip: "kitchen.mp4", spot: [520, 1480], phone: [800, 1210], size: 500, end: END, chat, flashAt: LEVEL,
  caps: [[4.0, 5.8, "it asks. every single day."], [CHIP + .6, END - .1, "12 days. my record was 3."]],
  sounds: [["thump", CHIP], ["xp", CHIP + .15], ["levelup", LEVEL]],
  line: "Your companion who grows with you",
  caption: "My accountability partner is 2 inches tall and it's awake before my coffee. It asks every single day. 12 days in a row now. My old record was 3.",
  tags: "#accountabilitypartner #morningroutine #languagelearning #habits #streak",
});
