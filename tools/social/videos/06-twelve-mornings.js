// Day 6: "12 days ago I couldn't run for 1 minute". Twelve mornings of Ember's notifications stack up on the lock
// screen, faster and faster, each step a little harder. Then: today I ran 10 minutes without stopping.
import * as K from "../kit.js";
const { W, C, makeEmber, clamp, out3, back, appear, bg, say, ember, pill, endCard } = window;
const c = window.c;
const END = 12.1, PAYOFF = 9.0;
let e;

const TEXTS = [
  "Day 1. Just 1 minute of running today. That's all.", "Day 2. 1 minute again. Yesterday counted.",
  "Day 3. Try 2 minutes? Walk between if you need to.", "Day 4. 2 minutes, twice. You've got this.",
  "Day 5. 5 days of steps. Your goal just reached level 2.", "Day 6. 3 minutes. How did your legs feel yesterday?",
  "Day 7. A whole week. 4 minutes today?", "Day 8. Rest day. Just a walk, if you like.",
  "Day 9. 5 minutes without stopping. Ready?", "Day 10. You said it felt easier. 6 minutes?",
  "Day 11. 8 minutes. You're almost there.", "Day 12. 10 minutes today. Remember day 1?",
];
const GAPS = [.85, .8, .74, .68, .62, .57, .52, .48, .45, .42, .4];
const AT = TEXTS.map((_, i) => .55 + GAPS.slice(0, i).reduce((a, b) => a + b, 0));
const day = i => new Date(2026, 9, 27 + i);          // day 1 was Tuesday 27 October; day 12 is today, Saturday 7 November
const fmt = (d, o) => d.toLocaleDateString("en-GB", o);
const current = t => { let k = 0; AT.forEach((a, i) => { if (t >= a) k = i; }); return k; };
const lock = {
  time: "7:30",
  date: t => fmt(day(current(t)), { weekday: "long", day: "numeric", month: "long" }),
  notes: TEXTS.map((text, i) => ({ at: AT[i], text, when: t => current(t) === i ? "now" : fmt(day(i), { weekday: "short" }) })),
};
const CAPS = [
  [0.1, 3.0, "12 days ago I couldn't run for 1 minute"],
  [3.2, 8.7, "it texted me every single morning"],
  [PAYOFF + .2, 11.9, "today I ran 10 minutes without stopping"],
];

export default {
  dur: 14.6,
  caption: "12 days ago I couldn't run for 1 minute. It texted me every single morning, one small step harder each time. Today I ran 10 minutes without stopping.",
  tags: "#running #couchto5k #consistency #glowup #accountability",
  sounds: [...AT.flatMap((a, i) => [["buzz", a - .04], ["tick", a, i]]), ["tap", PAYOFF - .25], ["whoosh", PAYOFF - .1],
    ["boom", PAYOFF + .9], ["levelup", PAYOFF + .95], ["sparkle", PAYOFF + 1.0], ["chime", END + .1]],
  init() { e = makeEmber(760); e.state.level = { level: 7, stage: "Ember" }; },
  draw(t) {
    if (t < PAYOFF) {
      e.at(t);
      const cam = K.camera(t, [{ t: 0, x: 540, y: 1150, w: 760, r: -.02 }, { t: PAYOFF, x: 540, y: 1165, w: 790, r: 0 }],
        AT.map(a => [a, a + .22, 5]));
      const r = K.lockScreen(t, lock); if (r[0]) K.ring(t, PAYOFF - .25, K.SW / 2, r[0].y + 80);
      K.room(cam); K.phone(cam);
    } else if (t < END + .5) {
      // the payoff: day 1's minute becomes day 12's ten
      const k = t - PAYOFF, grown = k > .9;
      bg(900, grown ? .95 : .6);
      e.face(grown ? "eager" : "curious", grown ? 1 : .75);
      if (k >= .9 && k < .9 + 1 / 30) e.burst(30);
      if (t < END) ember(e, t, W / 2, 960, 760);
      pill(grown ? "Day 12" : "Day 1", W / 2, 470, { size: 54, fill: grown ? C.btn : C.raised, color: grown ? C.ink : C.text, scale: grown ? back((k - .9) / .35) : 1 });
      say(grown ? "10 minutes" : "1 minute", W / 2, 1290, { size: 120, color: grown ? C.btn : C.text, alpha: grown ? appear(t, PAYOFF + .9, .2) : appear(t, PAYOFF, .2), rise: 20 });
      say(grown ? "without stopping" : "and I had to stop", W / 2, 1430, { size: 50, weight: 800, color: C.dim, alpha: appear(t, PAYOFF + (grown ? 1 : .1), .25) });
      K.flash(t, PAYOFF + .9, .35, .55);
    }
    K.captions(t, CAPS);
    if (t >= END) endCard(t, END, e, "Your companion who checks up on you");
    K.grain();
  },
};
