// The series "my accountability partner is 2 inches tall" (2026-11-10): every episode opens the same way, on a real
// surface filmed for it (clips/, made with Higgsfield: a locked-off shot with a dark phone and an empty patch of table),
// where Ember, drawn by the app's own face code, pops up, looks around and hops into the phone; then the phone is ours
// and the day's exchange plays. One format, many situations: an episode is only its clip, where Ember stands (spot), where
// the phone is (phone, the centre of its screen), its hook, its chat and its captions. 16-two-inches was the pilot.
import * as K from "./kit.js";
const { c, makeEmber, clamp, ease, back, endCard } = window;
export const POP = .25, HOP = 2.7, LAND = 3.1, IN = 3.75;
const lerp = (a, b, k) => a + (b - a) * k;

export function episode({ clip, spot, phone, size = 470, hook = "my accountability partner is 2 inches tall", chat, caps = [], end, flashAt, line = "Your companion who checks up on you",
  caption, tags, sounds = [], hue = 26 }) {
  let e;
  const CAM = [{ t: 0, x: 540, y: 1134, w: 780, r: 0 }, { t: end, x: 540, y: 1120, w: 805, r: 0 }];
  const CAPS = [[.5, 3.0, hook], ...caps];
  // Ember on the table: a warm pool of its light on the wood, a contact shadow, and the face from the app
  function onTable(t) {
    if (t < POP || t >= LAND) return;
    let [x, y] = spot, grow = back((t - POP) / .4), sz = size, a = 1, air = 0;
    const hop = (at, len, high) => { const k = (t - at) / len; return k > 0 && k < 1 ? Math.sin(k * Math.PI) * high : 0; };
    air = hop(1.15, .42, 70) + hop(1.6, .36, 40);
    if (t >= HOP) {
      const k = clamp((t - HOP) / (LAND - HOP));
      x = lerp(spot[0], phone[0], ease(k)); y = lerp(spot[1], phone[1] + 70, k); air = Math.sin(k * Math.PI) * 300;
      sz *= 1 - .6 * k; a = 1 - clamp((k - .82) / .18);
    }
    const near = 1 - clamp(air / 320), s = sz / 470;
    c.save(); c.globalAlpha = a * Math.min(1, grow);
    c.save(); c.globalCompositeOperation = "lighter"; c.translate(x, y); c.scale(1, .34);
    const g = c.createRadialGradient(0, 0, 10, 0, 0, 430 * s);
    g.addColorStop(0, `rgba(255,150,60,${.5 * near})`); g.addColorStop(.5, `rgba(255,120,40,${.16 * near})`); g.addColorStop(1, "rgba(255,110,40,0)");
    c.fillStyle = g; c.beginPath(); c.arc(0, 0, 430 * s, 0, Math.PI * 2); c.fill(); c.restore();
    c.save(); c.translate(x, y); c.scale(1, .2); c.fillStyle = `rgba(20,8,0,${.5 * near})`; c.filter = "blur(10px)";
    c.beginPath(); c.arc(0, 0, 95 * s * (.6 + .4 * near), 0, Math.PI * 2); c.fill(); c.restore();
    e.face(t < 1.0 ? "surprised" : t < 2.2 ? "happy" : "eager", .95);
    e.state.face.gaze = t > 1.6 && t < 2.5 ? (phone[0] > spot[0] ? "right" : "left") : "you";
    e.at(t);
    const squash = 1 + (grow > 1 ? (grow - 1) * 1.5 : 0) - (air === 0 && t > 1.5 && t < 1.66 ? .06 : 0);
    c.translate(x, y - air); c.scale(grow * (2 - squash), grow * squash);
    c.drawImage(e.canvas, -sz / 2, -sz * .715, sz, sz);
    c.restore();
  }
  // the dark phone in the footage lights up warm where Ember landed
  function lit(t) {
    const k = clamp((t - LAND) / .2); if (k <= 0) return;
    c.save(); c.globalCompositeOperation = "lighter"; c.globalAlpha = k;
    const g = c.createRadialGradient(phone[0], phone[1], 20, phone[0], phone[1], 460);
    g.addColorStop(0, "rgba(255,170,90,.75)"); g.addColorStop(.3, "rgba(255,140,60,.3)"); g.addColorStop(1, "rgba(255,120,50,0)");
    c.fillStyle = g; c.fillRect(0, 0, 1080, 1920); c.restore();
  }
  return {
    dur: end + 2.5,
    clips: { [clip]: clip },
    caption, tags,
    sounds: [["pop", POP], ["sparkle", POP + .05], ["boop", 1.15, 0], ["boop", 1.6, 4], ["rise", HOP - .05], ["unlock", LAND], ["whoosh", LAND + .15],
      ...K.chatSounds(chat), ...sounds, ["chime", end + .1]],
    init() { e = makeEmber(640); },
    async prep(t) { if (t < IN + .05) await window.clipSeek(clip, t); },
    draw(t) {
      const cam = K.camera(t, CAM);
      if (t < end + .5) {
        if (t >= LAND) { K.chatScreen(t, chat, e, t < end); K.room(cam, hue); K.phone(cam); }
        const k = clamp((t - (LAND + .1)) / (IN - LAND - .1));
        if (k < 1) {              // the footage, and once Ember is in the phone we push into it and it becomes ours
          const z = 1 + k * k * 1.6, fx = phone[0] / 1080, fy = phone[1] / 1920;
          c.save(); c.globalAlpha = 1 - k * k;
          c.translate(1080 * fx, 1920 * fy); c.scale(z, z); c.translate(-1080 * fx, -1920 * fy);
          window.clipDraw(clip, {}); onTable(t); lit(t);
          c.restore();
        }
        K.flash(t, LAND, .3, .4);
        if (flashAt) K.flash(t, flashAt, .35, .5);
        K.captions(t, CAPS);
      }
      if (t >= end) endCard(t, end, e, line);
      K.grain();
    },
  };
}
