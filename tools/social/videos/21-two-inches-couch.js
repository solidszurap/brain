// "2 inches tall", episode 4 (2026-11-10): against the couch. Ember on the coffee table (clips/couch.mp4), then in the
// phone: it's a run day, you say no, and it offers a smaller yes.
import { episode } from "../series.js";
import * as K from "../kit.js";
const END = 10.6;
const chat = {
  title: "Run 3 times a week",
  clock: () => "18:00",
  face: K.timeline([[0, "eager", .85], [5.5, "worried", .65], [5.8, "thinking", .65], [6.6, "calm", .75], [8.8, "happy", .95]]),
  level: () => ({ level: 5, stage: "Ember" }),
  typing: [{ from: 4.2, to: 5.1, text: "tired. maybe tomorrow", send: 5.3 }, { from: 8.2, to: 8.5, text: "ugh. ok", send: 8.7 }],
  keyboard: [[3.95, 8.95]],
  msgs: [
    { who: "ember", text: "It's a run day. How are we feeling?", at: 0 },
    { who: "you", text: "tired. maybe tomorrow", at: 5.3 },
    { who: "dots", at: 5.8, end: 6.6 },
    { who: "ember", text: "Tomorrow works. Or: shoes on, 5 minutes, back on the couch by 18:15.", at: 6.6 },
    { who: "you", text: "ugh. ok", at: 8.7 },
    { who: "ember", text: "The couch will wait. So will I.", at: 9.1 },
  ],
};
export default episode({
  clip: "couch.mp4", spot: [480, 1130], phone: [756, 990], size: 430, end: END, chat,
  caps: [[4.0, 6.3, "it lets me say no"], [6.6, END - .1, "it always has a smaller yes"]],
  caption: "My accountability partner is 2 inches tall and it just found me on the couch. It lets me say no. It always has a smaller yes.",
  tags: "#accountabilitypartner #runningmotivation #couchto5k #habits #selfimprovement",
});
