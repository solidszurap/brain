// "The app that won't let me quit": a 16-second story told on a phone, with Ember acting it out.
// The phone's screen is drawn live on its own canvas (lock screen, then the chat, the keyboard, the daily check),
// and a camera moves the phone around the frame. Captions pop in word by word, TikTok style, and the sound effects
// (buzz, ding, typing, pops, the level-up chime) are listed in `sounds` for the studio to synthesise.
const { W, H, C, makeEmber, clamp, ease, out3, back, appear, endCard, lines } = window;
const c = window.c;
const SW = 780, SH = 1688, F = "Nunito, ui-rounded, system-ui, sans-serif";
const scr = document.createElement("canvas"); scr.width = SW; scr.height = SH;
const s = scr.getContext("2d");
let e, noise;

// ---- the story's timeline (seconds)
const END = 13.6;                       // the end card
const CUT = 10.75;                      // "45 minutes later": the camera jumps while the screen is black
const TYPE = [
  { from: 3.45, to: 5.0, text: "not today, I'm tired", send: 5.2 },
  { from: 8.55, to: 9.05, text: "...fine", send: 9.3 },
];
const KB = { up: 3.1, down: 9.45 };     // the keyboard slides up and down
const CHIP_TAP = 12.0, LEVEL_UP = 12.1;
const MSGS = [
  { who: "ember", text: "Day 3. Still on for 10 minutes of running?", at: 0 },
  { who: "you", text: "not today, I'm tired", at: 5.2 },
  { who: "dots", at: 5.5, end: 6.8 },
  { who: "ember", text: "Fair. What about 5 minutes? Just to the corner and back.", at: 6.8 },
  { who: "you", text: "...fine", at: 9.3 },
  { who: "ember", text: "Shoes on. I'll be right here.", at: 9.9 },
  { who: "ember", text: "You're back! How did the 5 minutes go?", at: 11.15 },
  { who: "chips", at: 11.45 },
  { who: "ember", text: "4 days in a row. You almost skipped today, and you didn't.", at: 12.55 },
];
const CAPTIONS = [
  [0.15, 2.45, "day 3 of trying to become a runner"],
  [3.0, 5.6, "me, already making excuses"],
  [5.9, 8.5, "it didn't guilt trip me. it made it smaller"],
  [8.7, 10.4, "ok fine. 5 minutes."],
  [11.2, 13.5, "now I'm on a 4 day streak"],
];
function faceAt(t) {
  if (t < 5.2) return ["curious", .7];
  if (t < 5.5) return ["surprised", .7];
  if (t < 6.8) return ["thinking", .65];
  if (t < 9.3) return ["calm", .7];
  if (t < 10.5) return ["eager", .95];
  if (t < CHIP_TAP) return ["curious", .8];
  return ["happy", 1];
}
// where the phone sits: centre, width, tilt
const CAM = [
  { t: 0, x: 540, y: 1000, w: 600, r: -.05 },
  { t: 2.4, x: 540, y: 980, w: 650, r: -.03 },
  { t: 3.05, x: 540, y: 1290, w: 820, r: 0 },
  { t: 10.4, x: 540, y: 1270, w: 845, r: 0 },
];
const CAM2 = { x: 540, y: 1134, w: 780, r: 0 };  // after the cut: a fresh screen, with the new lines under Ember
function camera(t) {
  if (t >= CUT) { const k = ease((t - CUT) / 3); return { ...CAM2, w: CAM2.w + 20 * k, y: CAM2.y - 10 * k }; }
  let i = 0; while (i < CAM.length - 1 && t > CAM[i + 1].t) i++;
  const a = CAM[i], b = CAM[Math.min(i + 1, CAM.length - 1)], k = b === a ? 0 : ease((t - a.t) / (b.t - a.t));
  const m = (p) => a[p] + (b[p] - a[p]) * k;
  let x = m("x"), r = m("r");
  for (const [s0, s1] of [[.45, .8], [1.35, 1.7]]) if (t > s0 && t < s1) { x += Math.sin(t * 95) * 7; r += Math.sin(t * 77) * .006; }
  return { x, y: m("y"), w: m("w"), r: r + Math.sin(t * .9) * .003 };
}

// ---- the phone's screen
function wrap(text, maxW, font) { s.font = font; const ws = text.split(" "), out = []; let l = "";
  for (const w of ws) { const tl = l ? l + " " + w : w; if (s.measureText(tl).width > maxW && l) { out.push(l); l = w; } else l = tl; }
  if (l) out.push(l); return out; }
function rr(x, y, w, h, r) { s.beginPath(); s.roundRect(x, y, w, h, r); }
function txt(t, x, y, size, weight = 600, color = C.text, align = "left") {
  s.font = `${weight} ${size}px ${F}`; s.fillStyle = color; s.textAlign = align; s.textBaseline = "middle"; s.fillText(t, x, y);
}
function ring(t, at, x, y) {
  const k = (t - at) / .45; if (k < 0 || k > 1) return;
  s.save(); s.globalAlpha = (1 - k) * .9; s.strokeStyle = "#fff"; s.lineWidth = 6;
  s.beginPath(); s.arc(x, y, 22 + k * 50, 0, Math.PI * 2); s.stroke();
  s.globalAlpha = (1 - k) * .35; s.fillStyle = "#fff"; s.beginPath(); s.arc(x, y, 30, 0, Math.PI * 2); s.fill(); s.restore();
}
function statusBar(time, light = .9) {
  txt(time, 64, 34, 28, 700, `rgba(255,244,232,${light})`);
  s.fillStyle = `rgba(255,244,232,${light})`; rr(SW - 112, 22, 54, 24, 7); s.fill(); s.fillRect(SW - 56, 29, 5, 10);
  for (let i = 0; i < 4; i++) { s.fillRect(SW - 200 + i * 14, 40 - i * 6, 9, 8 + i * 6); }
}
function lockScreen(t) {
  const g = s.createRadialGradient(SW / 2, -100, 60, SW / 2, 500, 1500);
  g.addColorStop(0, "#5a3218"); g.addColorStop(.55, "#24170f"); g.addColorStop(1, "#120c08");
  s.fillStyle = g; s.fillRect(0, 0, SW, SH);
  statusBar("18:00");
  txt("Tuesday 11 November", SW / 2, 190, 30, 700, "rgba(255,240,225,.75)", "center");
  txt("18:00", SW / 2, 300, 170, 700, "rgba(255,244,232,.96)", "center");
  const a = out3((t - .5) / .45); if (a <= 0) return;
  const y = 520 + (1 - a) * -60, lsx = wrap("Day 3. Still on for 10 minutes of running?", 520, `500 29px ${F}`);
  s.save(); s.globalAlpha = a;
  rr(34, y, SW - 68, 104 + lsx.length * 38, 34); s.fillStyle = "rgba(255,240,228,.16)"; s.fill();
  s.save(); rr(62, y + 28, 64, 64, 15); s.clip(); if (window.IMGS?.icon) s.drawImage(window.IMGS.icon, 62, y + 28, 64, 64); s.restore();
  txt("Ember sent you a message", 146, y + 46, 29, 800, "#fff4e8");
  txt("now", SW - 64, y + 46, 25, 600, "rgba(255,240,228,.6)", "right");
  lsx.forEach((l, i) => txt(l, 146, y + 86 + i * 38, 29, 500, "rgba(255,244,232,.92)"));
  s.restore();
  ring(t, 2.25, SW / 2, y + 80);
}
let chipX = 0, chipY = 0;
function bubbleSize(m) {
  if (m.who === "dots") return { w: 130, h: 72 };
  if (m.who === "chips") return { w: SW, h: 84 };
  const font = `600 31px ${F}`, ls = wrap(m.text, 470, font); s.font = font;
  return { ls, w: Math.max(...ls.map(l => s.measureText(l).width)) + 56, h: ls.length * 42 + 34 };
}
function drawMsg(m, sz, y, t, alpha) {
  s.save(); s.globalAlpha = alpha;
  if (m.who === "dots") {
    rr(30, y, sz.w, sz.h, [10, 30, 30, 30]); s.fillStyle = C.surface; s.fill();
    for (let i = 0; i < 3; i++) { s.fillStyle = `rgba(241,231,220,${.3 + .7 * Math.max(0, Math.sin(t * 7 - i * .9))})`; s.beginPath(); s.arc(64 + i * 30, y + 36, 8, 0, Math.PI * 2); s.fill(); }
  } else if (m.who === "chips") {
    const names = ["Did it", "Partly", "Not today"]; let x = 30;
    names.forEach((n, i) => {
      s.font = `800 28px ${F}`; const w = s.measureText(n).width + 50, on = i === 0 && t > CHIP_TAP + .08;
      const k = i === 0 ? 1 + .12 * Math.max(0, Math.sin(clamp((t - CHIP_TAP) / .3) * Math.PI)) : 1;
      s.save(); s.globalAlpha = alpha * (t > CHIP_TAP + .08 && i ? .35 : 1); s.translate(x + w / 2, y + 40); s.scale(k, k);
      rr(-w / 2, -30, w, 60, 30); s.fillStyle = on ? C.btn : C.raised; s.fill();
      txt(n, 0, 2, 28, 800, on ? C.ink : C.text, "center"); s.restore();
      if (i === 0) { chipX = x + w / 2; chipY = y + 40; }
      x += w + 16;
    });
  } else {
    const you = m.who === "you", x = you ? SW - 30 - sz.w : 30;
    rr(x, y, sz.w, sz.h, you ? [30, 30, 10, 30] : [10, 30, 30, 30]);
    s.fillStyle = you ? "#3a2618" : C.surface; s.fill(); s.strokeStyle = you ? "rgba(255,190,140,.25)" : "rgba(255,245,235,.12)"; s.lineWidth = 2; s.stroke();
    sz.ls.forEach((l, i) => txt(l, x + 28, y + 38 + i * 42, 31, 600));
  }
  s.restore();
}
const KEYS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"];
function keyboard(t, top, typing) {
  s.fillStyle = "#26201b"; s.fillRect(0, top, SW, SH - top);
  let pressed = null;
  if (typing && typing.p > 0 && typing.p < 1) { const n = typing.text.length * typing.p; if (n % 1 < .55) pressed = typing.text[Math.floor(n)]?.toLowerCase(); }
  const kw = (SW - 20) / 10;
  KEYS.forEach((row, r) => {
    const x0 = (SW - row.length * kw) / 2;
    [...row].forEach((ch, i) => {
      const x = x0 + i * kw + 4, y = top + 24 + r * 104, on = ch === pressed;
      rr(x, y, kw - 8, 86, 12); s.fillStyle = on ? "#6b5a4d" : "#4a3f37"; s.fill();
      txt(ch, x + (kw - 8) / 2, y + 44, 36, 500, C.text, "center");
      if (on) { rr(x - 8, y - 96, kw + 8, 92, 16); s.fillStyle = "#6b5a4d"; s.fill(); txt(ch, x + (kw - 8) / 2, y - 50, 48, 600, C.text, "center"); }
    });
  });
  rr(10 + 2 * kw, top + 24 + 3 * 104, 5 * kw, 86, 12); s.fillStyle = pressed === " " ? "#6b5a4d" : "#4a3f37"; s.fill();
  rr(14, top + 24 + 3 * 104, 2 * kw - 20, 86, 12); s.fillStyle = "#3a312a"; s.fill(); txt("123", 14 + kw - 10, top + 24 + 3 * 104 + 44, 30, 600, C.text, "center");
  rr(10 + 7 * kw + 8, top + 24 + 3 * 104, 3 * kw - 18, 86, 12); s.fillStyle = "#3a312a"; s.fill(); txt("return", 10 + 8.5 * kw, top + 24 + 3 * 104 + 44, 30, 600, C.text, "center");
}
function app(t, step) {
  const later = t >= CUT;
  s.fillStyle = C.bg; s.fillRect(0, 0, SW, SH);
  const g = s.createRadialGradient(SW / 2, 380, 30, SW / 2, 380, 620);
  g.addColorStop(0, "rgba(255,150,70,.22)"); g.addColorStop(1, "rgba(255,120,50,0)"); s.fillStyle = g; s.fillRect(0, 0, SW, SH);
  statusBar(later ? "18:47" : "18:01");
  // the top bar: chats, the chat's name, a new chat
  s.strokeStyle = C.text; s.lineWidth = 4; s.lineCap = "round";
  for (let i = 0; i < 3; i++) { s.beginPath(); s.moveTo(40, 104 + i * 13); s.lineTo(72, 104 + i * 13); s.stroke(); }
  txt("Run 10 minutes a day", SW / 2, 118, 30, 800, C.text, "center");
  s.beginPath(); s.moveTo(SW - 56, 102); s.lineTo(SW - 56, 134); s.moveTo(SW - 72, 118); s.lineTo(SW - 40, 118); s.stroke();
  // Ember
  const [ex, gl] = faceAt(t); e.face(ex, gl);
  if (t >= LEVEL_UP) e.state.level = { level: 6, stage: "Ember" };
  if (step) e.at(t);
  s.drawImage(e.canvas, SW / 2 - 240, 150, 480, 480);
  const lv = t >= LEVEL_UP ? 6 : 5;
  s.font = `800 26px ${F}`; rr(SW / 2 - 92, 598, 184, 46, 23); s.fillStyle = C.raised; s.fill();
  txt(`Ember · Lv ${lv}`, SW / 2, 622, 26, 800, lv === 6 && t < LEVEL_UP + 1.5 ? C.btn : C.text, "center");
  // the input and the keyboard
  const kb = t < KB.up ? 0 : t < KB.down ? out3((t - KB.up) / .3) : 1 - out3((t - KB.down) / .3);
  const kbTop = SH - 540 * kb, inTop = kbTop - 128;
  const typing = TYPE.find(w => t >= w.from - .3 && t < w.send);
  // the conversation, newest at the bottom; each line grows in, pushing the others up
  s.save(); s.beginPath(); s.rect(0, 666, SW, inTop - 666); s.clip();
  let y = inTop - 16;
  const shown = MSGS.filter(m => t >= m.at && !(m.end && t >= m.end + .15) && (!later || m.at > CUT));
  if (later) {                            // after the cut the chat has scrolled on: the new lines start under Ember
    y = 676;
    for (const m of shown) { const sz = bubbleSize(m), grow = out3((t - m.at) / .3); drawMsg(m, sz, y, t, grow); y += (sz.h + 20) * grow; }
  }
  for (let i = shown.length - 1; !later && i >= 0 && y > 600; i--) {
    const m = shown[i], sz = bubbleSize(m), grow = m.at === 0 ? 1 : out3((t - m.at) / .3);
    const fadeOut = m.end ? 1 - clamp((t - m.end) / .15) : 1;
    y -= (sz.h + 20) * grow * fadeOut;
    drawMsg(m, sz, y + 20, t, grow * fadeOut);
  }
  s.restore();
  s.fillStyle = C.bg; s.fillRect(0, inTop, SW, kbTop - inTop);
  rr(26, inTop + 24, SW - 140, 82, 41); s.fillStyle = C.surface; s.fill(); s.strokeStyle = "rgba(255,245,235,.12)"; s.lineWidth = 2; s.stroke();
  if (typing && t >= typing.from) {
    const p = clamp((t - typing.from) / (typing.to - typing.from)), shownTxt = typing.text.slice(0, Math.round(typing.text.length * p));
    txt(shownTxt, 58, inTop + 66, 31, 600);
    s.font = `600 31px ${F}`; if ((t * 2.2) % 1 < .6) { s.fillStyle = C.btn; s.fillRect(60 + s.measureText(shownTxt).width + 4, inTop + 46, 3, 40); }
    typing.p = p;
  } else txt("Message Ember…", 58, inTop + 66, 31, 600, C.faint);
  s.fillStyle = C.btn; s.beginPath(); s.arc(SW - 66, inTop + 65, 41, 0, Math.PI * 2); s.fill();
  s.strokeStyle = C.ink; s.lineWidth = 6; s.beginPath(); s.moveTo(SW - 66, inTop + 84); s.lineTo(SW - 66, inTop + 46); s.moveTo(SW - 82, inTop + 61); s.lineTo(SW - 66, inTop + 46); s.lineTo(SW - 50, inTop + 61); s.stroke();
  if (kb > 0) keyboard(t, kbTop, typing);
  for (const w of TYPE) ring(t, w.send - .15, SW - 66, inTop + 65);
  ring(t, CHIP_TAP - .1, chipX, chipY);
  // the XP it earned
  const xa = clamp(Math.min((t - 12.2) / .15, (13.5 - t) / .25));
  if (xa > 0) {
    s.save(); s.globalAlpha = xa; s.translate(SW / 2 + 220, 470 - out3((t - 12.2) / 1.2) * 70); const k = back((t - 12.2) / .35); s.scale(k, k);
    rr(-110, -38, 220, 76, 38); s.fillStyle = C.btn; s.fill(); txt("+10 XP", 0, 2, 36, 900, C.ink, "center"); s.restore();
  }
}
function screen(t, step) {
  if (t < 2.45) { if (step) e.at(t); lockScreen(t); return; }
  const k = clamp((t - 2.45) / .35);
  app(t, step);
  if (k < 1) { s.save(); s.globalAlpha = 1 - k; const keep = s.getTransform(); s.translate(SW / 2, 600); s.scale(1 + k * .15, 1 + k * .15); s.translate(-SW / 2, -600); lockScreen(t); s.setTransform(keep); s.restore(); }
}

// ---- the frame around it
function room(cam, t) {
  c.fillStyle = "#0d0907"; c.fillRect(0, 0, W, H);
  const g = c.createRadialGradient(cam.x, cam.y - 200, 50, cam.x, cam.y, 1300);
  g.addColorStop(0, "rgba(255,140,60,.30)"); g.addColorStop(.5, "rgba(160,70,25,.10)"); g.addColorStop(1, "rgba(0,0,0,0)");
  c.fillStyle = g; c.fillRect(0, 0, W, H);
}
function phone(cam) {
  const w = cam.w, h = w * SH / SW, b = w * .03;
  c.save(); c.translate(cam.x, cam.y); c.rotate(cam.r);
  c.shadowColor = "rgba(0,0,0,.6)"; c.shadowBlur = 90; c.shadowOffsetY = 40;
  c.beginPath(); c.roundRect(-w / 2 - b, -h / 2 - b, w + 2 * b, h + 2 * b, w * .14); c.fillStyle = "#090706"; c.fill();
  c.shadowColor = "transparent"; c.strokeStyle = "rgba(255,235,215,.16)"; c.lineWidth = 3; c.stroke();
  c.beginPath(); c.roundRect(-w / 2, -h / 2, w, h, w * .115); c.save(); c.clip();
  c.drawImage(scr, -w / 2, -h / 2, w, h); c.restore();
  // the dynamic island
  c.beginPath(); c.roundRect(-w * .14, -h / 2 + w * .025, w * .28, w * .075, w * .04); c.fillStyle = "#000"; c.fill();
  c.restore();
}
function caption(t, a, b, text) {
  if (t < a || t > b) return;
  const font = `900 62px ${F}`, ls = lines(text, 860, font), out = clamp((b - t) / .18);
  let k = 0;
  c.save(); c.globalAlpha = out; c.font = font; c.textBaseline = "middle"; c.textAlign = "left";
  ls.forEach((l, li) => {
    // the box grows with the words, as each one pops in
    const y = 200 + li * 96, lw = c.measureText(l).width, x0 = W / 2 - lw / 2, sp = c.measureText(" ").width;
    let x = x0, right = null; const words = [];
    for (const w of l.split(" ")) { const ww = c.measureText(w).width, p = back((t - a - k * .07) / .22); words.push([w, x, ww, p]); if (p > 0) right = x + ww; x += ww + sp; k++; }
    if (right === null) return;
    c.beginPath(); c.roundRect(x0 - 26, y - 44, right - x0 + 52, 88, 20); c.fillStyle = "rgba(255,248,240,1)"; c.fill();
    for (const [w, wx, ww, p] of words) if (p > 0) { c.save(); c.translate(wx + ww / 2, y); c.scale(p, p); c.fillStyle = "#1a0f08"; c.fillText(w, -ww / 2, 2); c.restore(); }
  });
  c.restore();
}
function grain(t) {
  if (!noise) {
    noise = document.createElement("canvas"); noise.width = noise.height = 256; const n = noise.getContext("2d"), d = n.createImageData(256, 256);
    for (let i = 0; i < d.data.length; i += 4) { const v = Math.random() * 255; d.data[i] = d.data[i + 1] = d.data[i + 2] = v; d.data[i + 3] = 255; }
    n.putImageData(d, 0, 0);
  }
  c.save(); c.globalAlpha = .05; c.globalCompositeOperation = "overlay";
  const ox = Math.floor(Math.random() * 256), oy = Math.floor(Math.random() * 256);
  for (let x = -ox; x < W; x += 256) for (let y = -oy; y < H; y += 256) c.drawImage(noise, x, y);
  c.restore();
  const v = c.createRadialGradient(W / 2, H / 2, H * .3, W / 2, H / 2, H * .75);
  v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,.5)"); c.fillStyle = v; c.fillRect(0, 0, W, H);
}

// ---- the sounds, for the studio's synthesiser
const sounds = [
  ["buzz", .45], ["ding", .5], ["buzz", 1.35], ["tap", 2.25], ["whoosh", 2.45],
  ...TYPE.flatMap(w => [...w.text].map((ch, i) => ["key", w.from + (i + .5) / w.text.length * (w.to - w.from)])),
  ...TYPE.flatMap(w => [["tap", w.send - .15], ["send", w.send]]),
  ...MSGS.filter(m => m.who === "ember" && m.at > 0).map(m => ["pop", m.at]),
  ["whoosh", CUT - .3], ["tap", CHIP_TAP - .1], ["levelup", LEVEL_UP], ["xp", 12.2], ["chime", END + .1],
];

export default {
  dur: 16,
  caption: "Day 3 of trying to become a runner. I tried to skip. It didn't guilt trip me, it made the step smaller. Now I'm on a 4 day streak.",
  tags: "#running #accountability #habits #selfimprovement #motivation",
  sounds,
  init() { e = makeEmber(640); e.state.level = { level: 5, stage: "Ember" }; },
  draw(t) {
    const cam = camera(t);
    if (t < END + .5) {
      screen(t, t < END);
      room(cam, t); phone(cam);
      for (const [a, b, text] of CAPTIONS) caption(t, a, b, text);
      // "45 minutes later"
      const k = Math.min(clamp((t - (CUT - .3)) / .12), clamp((CUT + .3 - t) / .12));
      if (k > 0) { c.fillStyle = `rgba(8,6,5,${k})`; c.fillRect(0, 0, W, H);
        c.save(); c.globalAlpha = k; c.font = `900 84px ${F}`; c.fillStyle = "#fff4e8"; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText("45 minutes later", W / 2, H / 2 - 80); c.restore(); }
    }
    if (t >= END) endCard(t, END, e, "Your companion who checks up on you");
    grain(t);
  },
};
