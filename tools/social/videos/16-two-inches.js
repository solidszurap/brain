// Hook test 2 (2026-11-09), curiosity and the mascot: "my accountability partner is 2 inches tall". Opens on filmed
// footage (clips/desk.mp4, made with Higgsfield: a locked-off desk at dusk, a phone propped on books, its screen off),
// and Ember itself, drawn by the app's own face code, pops up on the real desk, looks around and hops into the phone.
// We follow it in: its daily message, your answer, a level up, and the looks it earns.
import * as K from "../kit.js";
const { c, makeEmber, clamp, ease, out3, back, endCard } = window;
const POP = .25, HOP = 2.7, LAND = 3.1, PUSH = 3.2, IN = 3.95, LEVEL = 6.5, SHOT = 8.2, END = 10.2;
let e;

// the propped phone's screen in the footage, in the video's pixels: its top-left corner and its two edges (it leans 7°)
const SCR = { x: 774, y: 899, ux: 171.6, uy: 22.1, vx: -50.2, vy: 371.4 };
const PC = [SCR.x + SCR.ux / 2 + SCR.vx / 2, SCR.y + SCR.uy / 2 + SCR.vy / 2], PW = Math.hypot(SCR.ux, SCR.uy), TILT = Math.atan2(SCR.uy, SCR.ux);
const SPOT = [455, 1500];                       // where Ember stands on the desk (its feet)
const lerp = (a, b, k) => a + (b - a) * k;

const chat = {
  title: "Learn guitar",
  clock: () => "18:00",
  face: K.timeline([[0, "happy", .9], [3.6, "curious", .8], [5.5, "surprised", .8], [5.9, "happy", .95], [LEVEL, "happy", 1]]),
  level: t => ({ level: t >= LEVEL ? 6 : 5, stage: "Ember" }), levelAt: LEVEL,
  typing: [{ from: 4.35, to: 5.25, text: "did it. my fingers hurt", send: 5.45 }],
  keyboard: [[4.05, 5.7]],
  msgs: [
    { who: "ember", text: "Day 6 of guitar. 10 minutes today?", at: 0 },
    { who: "you", text: "did it. my fingers hurt", at: 5.45 },
    { who: "ember", text: "6 days in a row. Sore fingers mean it's working.", at: 5.95 },
  ],
  xp: [{ at: 5.6, text: "+10 XP", until: 7.6 }],
};
const CAM = [
  { t: 0, x: 540, y: 1134, w: 780, r: 0 }, { t: SHOT - .2, x: 540, y: 1120, w: 800, r: 0 },
  { t: SHOT, cut: true, x: 540, y: 1100, w: 700, r: -.03 }, { t: END, x: 540, y: 1080, w: 740, r: -.01 },
];
const CAPS = [
  [0.5, 3.0, "my accountability partner is 2 inches tall"],
  [4.05, 5.75, "it texts me first. every day."],
  [5.95, 8.0, "it counted day 6 before I did"],
  [SHOT + .1, END - .1, "and it grows when I do"],
];

// Ember on the desk: a warm pool of its light on the wood, a contact shadow, and the face from the app
function onDesk(t) {
  if (t < POP || t >= LAND) return;
  let [x, y] = SPOT, grow = back((t - POP) / .4), size = 470, a = 1, air = 0;
  const hop = (at, len, high) => { const k = (t - at) / len; return k > 0 && k < 1 ? Math.sin(k * Math.PI) * high : 0; };
  air = hop(1.15, .42, 70) + hop(1.6, .36, 40);
  if (t >= HOP) {
    const k = clamp((t - HOP) / (LAND - HOP));
    x = lerp(SPOT[0], PC[0], ease(k)); y = lerp(SPOT[1], PC[1] + 70, k); air = Math.sin(k * Math.PI) * 300;
    size *= 1 - .6 * k; a = 1 - clamp((k - .82) / .18);
  }
  const near = 1 - clamp(air / 320), s = size / 470;
  c.save(); c.globalAlpha = a * grow;
  c.save(); c.globalCompositeOperation = "lighter"; c.translate(x, y); c.scale(1, .34);
  const g = c.createRadialGradient(0, 0, 10, 0, 0, 430 * s);
  g.addColorStop(0, `rgba(255,150,60,${.5 * near})`); g.addColorStop(.5, `rgba(255,120,40,${.16 * near})`); g.addColorStop(1, "rgba(255,110,40,0)");
  c.fillStyle = g; c.beginPath(); c.arc(0, 0, 430 * s, 0, Math.PI * 2); c.fill(); c.restore();
  c.save(); c.translate(x, y); c.scale(1, .2); c.fillStyle = `rgba(20,8,0,${.5 * near})`; c.filter = "blur(10px)";
  c.beginPath(); c.arc(0, 0, 95 * s * (.6 + .4 * near), 0, Math.PI * 2); c.fill(); c.restore();
  e.face(t < 1.0 ? "surprised" : t < 2.2 ? "happy" : "eager", .95);
  e.state.face.gaze = t > 1.6 && t < 2.5 ? "right" : "you";
  e.at(t);
  const squash = 1 + (grow > 1 ? (grow - 1) * 1.5 : 0) - (air === 0 && t > 1.5 && t < 1.66 ? .06 : 0);
  c.translate(x, y - air); c.scale(grow * (2 - squash), grow * squash);
  c.drawImage(e.canvas, -size / 2, -size * .715, size, size);
  c.restore();
}
// the app on the propped phone's screen, in the footage's own perspective
function onPhone(a) {
  if (a <= 0) return;
  c.save(); c.globalAlpha = a; c.transform(SCR.ux / K.SW, SCR.uy / K.SW, SCR.vx / K.SH, SCR.vy / K.SH, SCR.x, SCR.y);
  c.beginPath(); c.roundRect(0, 0, K.SW, K.SH, K.SW * .13); c.clip(); c.drawImage(K.scr, 0, 0); c.restore();
  c.save(); c.globalCompositeOperation = "lighter"; c.globalAlpha = a * .5;
  const g = c.createRadialGradient(PC[0], PC[1], 60, PC[0], PC[1], 520); g.addColorStop(0, "rgba(255,150,70,.5)"); g.addColorStop(1, "rgba(255,120,50,0)");
  c.fillStyle = g; c.fillRect(0, 0, 1080, 1920); c.restore();
}

export default {
  dur: END + 2.5,
  clips: { desk: "desk.mp4" },
  caption: "My accountability partner is 2 inches tall and lives in my phone. It texts me first, every day, and it grows when I do. Meet Ember.",
  tags: "#accountabilitypartner #cozydesk #habits #selfimprovement #productivity",
  sounds: [["pop", POP], ["sparkle", POP + .05], ["boop", 1.15, 0], ["boop", 1.6, 4], ["rise", HOP - .05], ["unlock", LAND], ["whoosh", PUSH + .05],
    ...K.chatSounds(chat), ["xp", 5.6], ["levelup", LEVEL], ["whoosh", SHOT - .15], ["sparkle", SHOT + .1], ["chime", END + .1]],
  init() { e = makeEmber(640); },
  async prep(t) { if (t < IN + .05) await window.clipSeek("desk", t); },
  draw(t) {
    const cam = K.camera(t, CAM), k = ease((t - PUSH) / (IN - PUSH)), target = { x: 540, y: 1134, w: 780 };
    if (t < END + .5) {
      if (t >= LAND) {
        if (t >= SHOT) { e.face("happy", 1); e.at(t); K.shotScreen("looks"); } else K.chatScreen(t, chat, e, t < END);
      }
      if (t < IN) {             // the footage, and from PUSH on the camera flies into the phone on the desk
        c.save();
        c.translate(lerp(PC[0], target.x, k), lerp(PC[1], target.y, k)); c.rotate(-TILT * k);
        const z = Math.exp(Math.log(target.w / PW) * k); c.scale(z, z); c.translate(-PC[0], -PC[1]);
        window.clipDraw("desk", {});
        onDesk(t);
        if (t >= LAND) onPhone(clamp((t - LAND) / .15));
        c.restore();
        K.flash(t, LAND, .3, .35);
        const a = clamp((k - .55) / .45);
        if (a > 0) { c.save(); c.globalAlpha = a; K.room(target); c.restore(); K.phone(target, a); }
      } else { K.room(cam); K.phone(cam); }
      K.flash(t, LEVEL, .35, .55);
      K.captions(t, CAPS);
    }
    if (t >= END) endCard(t, END, e, "Your companion who grows with you");
    K.grain();
  },
};
