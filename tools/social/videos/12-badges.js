// Day 12: "badges for showing up. they level up with you". The "On fire" badge climbs from level 1 to 4 (3, 7, 14
// and 30 days in a row, as in mind/core.py BADGES), its ring changing colour each time, then the share card.
import * as K from "../kit.js";
const { W, C, makeEmber, clamp, out3, back, appear, bg, say, ember, medal, endCard } = window;
const c = window.c;
const END = 12.0, SHARE = 9.0;
let e;

const LEVELS = [[.6, 1, 3], [2.8, 2, 7], [5.0, 3, 14], [7.2, 4, 30]];   // [when, level, days in a row]
const CAPS = [
  [0.1, 2.6, "badges for showing up. they level up with you"],
  [2.8, 6.8, "each level takes a little longer"],
  [7.3, 8.9, "level 4: 30 days in a row"],
  [SHARE + .2, 11.8, "and you can share them"],
];
const now = t => { let r = LEVELS[0]; for (const l of LEVELS) if (t >= l[0]) r = l; return r; };
function shareCard(t) {
  const k = out3((t - SHARE) / .5); if (k <= 0) return;
  const cx = W / 2, top = 440 + (1 - k) * 900, w = 620, h = 775;
  c.save(); c.translate(cx, top + h / 2); c.rotate(-.03 * k); c.scale(1.18, 1.18); c.translate(-cx, -(top + h / 2));
  c.shadowColor = "rgba(0,0,0,.6)"; c.shadowBlur = 80; c.shadowOffsetY = 30;
  const g = c.createLinearGradient(0, top, 0, top + h); g.addColorStop(0, "#3a2416"); g.addColorStop(1, "#16100c");
  c.beginPath(); c.roundRect(cx - w / 2, top, w, h, 40); c.fillStyle = g; c.fill(); c.shadowColor = "transparent";
  c.strokeStyle = "rgba(255,200,150,.25)"; c.lineWidth = 3; c.stroke();
  if (t < END) e.at(t);
  c.drawImage(e.canvas, cx - 120, top + 30, 240, 240);
  medal(cx, top + 395, 112, 4);
  c.textAlign = "center"; c.textBaseline = "middle";
  c.font = `900 46px ${K.F}`; c.fillStyle = C.text; c.fillText("On fire · Level 4", cx, top + 560);
  c.font = `700 30px ${K.F}`; c.fillStyle = C.dim; c.fillText("Did my step 30 days in a row", cx, top + 615);
  c.font = `900 32px ${K.F}`; c.fillStyle = C.btn; c.fillText("yourember.app", cx, top + 710);
  c.restore();
}

export default {
  dur: 14.5,
  caption: "Badges for showing up, and they level up with you. 3 days, 7, 14, 30. And you can share them when you're proud.",
  tags: "#gamification #streak #habittracker #levelup #consistency",
  sounds: [...LEVELS.flatMap(([at], i) => [["rise", at - .5], ["unlock", at], ["sparkle", at + .05], ["boom", at, 0]].slice(i ? 0 : 1)),
    ["whoosh", SHARE], ["thump", SHARE + .45], ["chime", END + .1]],
  init() { e = makeEmber(520); e.state.level = { level: 9, stage: "Ember" }; },
  draw(t) {
    if (t < END + .5) {
      const [at, level, days] = now(t), since = t - at;
      bg(820, .5 + level * .1);
      const sc = level === 1 ? back((t - .4) / .45) : 1 + .12 * Math.max(0, Math.sin(clamp(since / .45) * Math.PI));
      if (t > .4) medal(W / 2, 800, 250, level, 1, sc);
      say("On fire", W / 2, 1110, { size: 86, alpha: appear(t, .6, .3) });
      say(`${days} days in a row`, W / 2, 1225, { size: 54, weight: 800, color: C.btn, alpha: appear(t, at + .05, .25), rise: 16 });
      e.face(since < .35 && t > .6 ? "surprised" : "happy", .75 + level * .06);
      if (LEVELS.some(([a]) => t >= a && t < a + 1 / 30)) e.burst(16);
      if (t < SHARE) ember(e, t, 860, 1380, 320);
      if (t >= SHARE) { c.fillStyle = `rgba(10,7,5,${.92 * out3((t - SHARE) / .4)})`; c.fillRect(0, 0, W, 1920); }
      shareCard(t);
      for (const [a, l] of LEVELS) if (l > 1) K.flash(t, a, .3, .45);
      K.captions(t, CAPS);
    }
    if (t >= END) endCard(t, END, e, "Share it when you're proud of it");
    K.grain();
  },
};
