// "2 inches tall", episode 2 (2026-11-10): bedtime. Ember on the bedside table (clips/night.mp4), then in the phone:
// you'd rather scroll, and it doesn't argue, it makes the step one page.
import { episode } from "../series.js";
import * as K from "../kit.js";
const END = 10.4;
const chat = {
  title: "Read before bed",
  clock: () => "21:40",
  face: K.timeline([[0, "curious", .8], [5.6, "surprised", .7], [5.8, "thinking", .65], [6.6, "calm", .75], [8.6, "happy", .95]]),
  level: () => ({ level: 4, stage: "Spark" }),
  typing: [{ from: 4.2, to: 5.2, text: "honestly I'm already scrolling", send: 5.4 }, { from: 7.9, to: 8.3, text: "...one page. fine", send: 8.5 }],
  keyboard: [[3.95, 8.75]],
  msgs: [
    { who: "ember", text: "You said 10 pages before sleep. Still on?", at: 0 },
    { who: "you", text: "honestly I'm already scrolling", at: 5.4 },
    { who: "dots", at: 5.8, end: 6.6 },
    { who: "ember", text: "Okay. One page. Then scroll all you want.", at: 6.6 },
    { who: "you", text: "...one page. fine", at: 8.5 },
    { who: "ember", text: "I'll ask you tomorrow how it went.", at: 8.9 },
  ],
};
export default episode({
  clip: "night.mp4", spot: [620, 1600], phone: [880, 1090], size: 450, end: END, chat,
  caps: [[4.0, 6.3, "it remembers what I said"], [6.6, END - .1, "no guilt. just smaller."]],
  caption: "My accountability partner is 2 inches tall and lives in my phone. Tonight I wanted to scroll. It didn't argue. It said: one page.",
  tags: "#accountabilitypartner #readingtok #habits #bedtimeroutine #selfimprovement",
});
