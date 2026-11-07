// The pieces the story videos are built from (2026-11-07): a phone whose screen is drawn live (a lock screen with
// notifications, Ember's chat with typing and the keyboard, or a real screenshot of the app), a camera that moves the
// phone, captions that pop in word by word, title cards, film grain, and the sound effects that go with them.
// One video renders at a time, so the phone's screen is one shared canvas (`scr`, drawn with `s`).
const { C, clamp, ease, out3, back, appear, lines, W, H } = window;
const c = window.c;
export const SW = 780, SH = 1688, F = "Nunito, ui-rounded, system-ui, sans-serif";
export const scr = document.createElement("canvas"); scr.width = SW; scr.height = SH;
export const s = scr.getContext("2d");

// ---- drawing on the screen
export function wrap(text, maxW, font) {
  s.font = font; const out = []; let l = "";
  for (const w of text.split(" ")) { const tl = l ? l + " " + w : w; if (s.measureText(tl).width > maxW && l) { out.push(l); l = w; } else l = tl; }
  if (l) out.push(l); return out;
}
export function rr(x, y, w, h, r) { s.beginPath(); s.roundRect(x, y, w, h, r); }
export function txt(t, x, y, size, weight = 600, color = C.text, align = "left") {
  s.font = `${weight} ${size}px ${F}`; s.fillStyle = color; s.textAlign = align; s.textBaseline = "middle"; s.fillText(t, x, y);
}
// a finger's tap: a ring that grows and fades
export function ring(t, at, x, y) {
  const k = (t - at) / .45; if (k < 0 || k > 1) return;
  s.save(); s.globalAlpha = (1 - k) * .9; s.strokeStyle = "#fff"; s.lineWidth = 6;
  s.beginPath(); s.arc(x, y, 22 + k * 50, 0, Math.PI * 2); s.stroke();
  s.globalAlpha = (1 - k) * .35; s.fillStyle = "#fff"; s.beginPath(); s.arc(x, y, 30, 0, Math.PI * 2); s.fill(); s.restore();
}
export function statusBar(time, light = .9) {
  txt(time, 64, 34, 28, 700, `rgba(255,244,232,${light})`);
  s.fillStyle = `rgba(255,244,232,${light})`; rr(SW - 112, 22, 54, 24, 7); s.fill(); s.fillRect(SW - 56, 29, 5, 10);
  for (let i = 0; i < 4; i++) s.fillRect(SW - 200 + i * 14, 40 - i * 6, 9, 8 + i * 6);
}
function appIcon(x, y, size, kind) {
  s.save(); rr(x, y, size, size, size * .24); s.clip();
  if (kind === "other") { s.fillStyle = "#c9443a"; s.fillRect(x, y, size, size); txt("!", x + size / 2, y + size / 2 + 2, size * .62, 900, "#fff", "center"); }
  else if (window.IMGS?.icon) s.drawImage(window.IMGS.icon, x, y, size, size);
  s.restore();
}

// ---- the lock screen: notes [{at, text, title, when, icon: "other", red, out}] slide in, the newest on top (and out
// to the left at `out`)
export function lockScreen(t, { time = "18:00", date = "Tuesday 11 November", notes = [] } = {}) {
  const g = s.createRadialGradient(SW / 2, -100, 60, SW / 2, 500, 1500);
  g.addColorStop(0, "#5a3218"); g.addColorStop(.55, "#24170f"); g.addColorStop(1, "#120c08");
  s.fillStyle = g; s.fillRect(0, 0, SW, SH);
  const tm = typeof time === "function" ? time(t) : time;
  statusBar(tm);
  txt(typeof date === "function" ? date(t) : date, SW / 2, 190, 30, 700, "rgba(255,240,225,.75)", "center");
  txt(tm, SW / 2, 300, 170, 700, "rgba(255,244,232,.96)", "center");
  const rects = [], base = s.globalAlpha; let y = 500;
  for (const n of notes.filter(n => t >= n.at).sort((a, b) => b.at - a.at)) {
    const a = out3((t - n.at) / .4), ls = wrap(n.text, 520, `500 29px ${F}`), h = 104 + ls.length * 38;
    const gone = n.out != null ? out3((t - n.out) / .3) : 0;      // swiped away to the left at n.out
    if (gone >= 1) continue;
    if (y > SH) break;
    s.save(); s.globalAlpha = base * a * (1 - gone); s.translate(-gone * SW, (1 - a) * -50);
    rr(34, y, SW - 68, h, 34); s.fillStyle = n.red ? "rgba(255,110,95,.22)" : "rgba(255,240,228,.16)"; s.fill();
    appIcon(62, y + 28, 64, n.icon);
    txt(n.title || "Ember sent you a message", 146, y + 46, 29, 800, "#fff4e8");
    txt((typeof n.when === "function" ? n.when(t) : n.when) || "now", SW - 64, y + 46, 25, 600, "rgba(255,240,228,.6)", "right");
    ls.forEach((l, i) => txt(l, 146, y + 86 + i * 38, 29, 500, "rgba(255,244,232,.92)"));
    s.restore();
    rects.push({ n, x: 34, y, w: SW - 68, h });
    y += (h + 16) * a * (1 - gone);
  }
  return rects;
}

// ---- Ember's chat. A message is {who, at, ...}: "ember" and "you" lines (text), "dots" (Ember typing, until end),
// "chips" (Did it / Partly / Not today; pick is tapped at tap), "check" (your daily check: how, step) and
// "card" (Ember's suggestion: title, lines, button, tapped at tap)
const CHIPS = ["Did it", "Partly", "Not today"];
function msgSize(m) {
  if (m.who === "dots") return { w: 130, h: 72 };
  if (m.who === "chips") return { w: SW, h: 84 };
  if (m.who === "check") { s.font = `600 29px ${F}`; return { w: Math.min(560, s.measureText(m.step).width + 250), h: 84 }; }
  if (m.who === "card") { const ls = (m.lines || []).flatMap(l => wrap(l, 540, `600 28px ${F}`)); return { ls, w: 620, h: 70 + ls.length * 38 + (m.button ? 104 : 24) }; }
  const font = `600 31px ${F}`, ls = wrap(m.text, 470, font); s.font = font;
  return { ls, w: Math.max(...ls.map(l => s.measureText(l).width)) + 56, h: ls.length * 42 + 34 };
}
function drawMsg(m, sz, y, t, alpha) {
  s.save(); s.globalAlpha = alpha;
  if (m.who === "dots") {
    rr(30, y, sz.w, sz.h, [10, 30, 30, 30]); s.fillStyle = C.surface; s.fill();
    for (let i = 0; i < 3; i++) { s.fillStyle = `rgba(241,231,220,${.3 + .7 * Math.max(0, Math.sin(t * 7 - i * .9))})`; s.beginPath(); s.arc(64 + i * 30, y + 36, 8, 0, Math.PI * 2); s.fill(); }
  } else if (m.who === "chips") {
    let x = 30; const pick = m.pick ?? 0, done = m.tap != null && t > m.tap + .08;
    CHIPS.forEach((n, i) => {
      s.font = `800 28px ${F}`; const w = s.measureText(n).width + 50, on = i === pick && done;
      const k = i === pick && m.tap != null ? 1 + .12 * Math.max(0, Math.sin(clamp((t - m.tap) / .3) * Math.PI)) : 1;
      s.save(); s.globalAlpha = alpha * (done && i !== pick ? .35 : 1); s.translate(x + w / 2, y + 40); s.scale(k, k);
      rr(-w / 2, -30, w, 60, 30); s.fillStyle = on ? (pick === 2 ? "#5a3a26" : C.btn) : C.raised; s.fill();
      txt(n, 0, 2, 28, 800, on && pick !== 2 ? C.ink : C.text, "center"); s.restore();
      if (i === pick) m._tap = [x + w / 2, y + 40];
      x += w + 16;
    });
  } else if (m.who === "check") {
    const x = SW - 30 - sz.w; rr(x, y, sz.w, sz.h, [30, 30, 10, 30]); s.fillStyle = "#3a2618"; s.fill();
    s.strokeStyle = "rgba(255,190,140,.25)"; s.lineWidth = 2; s.stroke();
    s.font = `800 26px ${F}`; const cw = s.measureText(m.how).width + 66;
    rr(x + 20, y + 20, cw, 44, 22); s.fillStyle = m.how === "Not today" ? "#5a3a26" : C.btn; s.fill();
    txt((m.how === "Not today" ? "" : "✓ ") + m.how, x + 20 + cw / 2, y + 43, 26, 800, m.how === "Not today" ? C.text : C.ink, "center");
    txt(m.step, x + 36 + cw, y + 43, 29, 600, C.text);
  } else if (m.who === "card") {
    rr(30, y, sz.w, sz.h, [10, 30, 30, 30]); s.fillStyle = C.raised; s.fill(); s.strokeStyle = "rgba(255,168,98,.35)"; s.lineWidth = 2.5; s.stroke();
    txt(m.title, 62, y + 46, 32, 900, C.btn);
    sz.ls.forEach((l, i) => txt(l, 62, y + 94 + i * 38, 28, 600, C.dim));
    if (m.button) {
      const by = y + sz.h - 62, pressed = m.tap != null && t > m.tap, k = m.tap != null ? 1 - .08 * Math.max(0, Math.sin(clamp((t - m.tap + .1) / .25) * Math.PI)) : 1;
      s.save(); s.translate(62 + 120, by); s.scale(k, k); rr(-120, -34, 240, 68, 34); s.fillStyle = C.btn; s.fill();
      txt(pressed ? "Started ✓" : m.button, 0, 2, 29, 900, C.ink, "center"); s.restore();
      m._tap = [62 + 120, by];
    }
  } else {
    const you = m.who === "you", x = you ? SW - 30 - sz.w : 30;
    rr(x, y, sz.w, sz.h, you ? [30, 30, 10, 30] : [10, 30, 30, 30]);
    s.fillStyle = you ? "#3a2618" : C.surface; s.fill(); s.strokeStyle = you ? "rgba(255,190,140,.25)" : "rgba(255,245,235,.12)"; s.lineWidth = 2; s.stroke();
    sz.ls.forEach((l, i) => txt(l, x + 28, y + 38 + i * 42, 31, 600));
  }
  s.restore();
}
const KEYS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"];
function keyboard(top, typing) {
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
  const ry = top + 24 + 3 * 104;
  rr(10 + 2 * kw, ry, 5 * kw, 86, 12); s.fillStyle = pressed === " " ? "#6b5a4d" : "#4a3f37"; s.fill();
  rr(14, ry, 2 * kw - 20, 86, 12); s.fillStyle = "#3a312a"; s.fill(); txt("123", 14 + kw - 10, ry + 44, 30, 600, C.text, "center");
  rr(10 + 7 * kw + 8, ry, 3 * kw - 18, 86, 12); s.fillStyle = "#3a312a"; s.fill(); txt("return", 10 + 8.5 * kw, ry + 44, 30, 600, C.text, "center");
}
function kbAmount(t, windows) {
  let k = 0;
  for (const [up, down] of windows) {
    if (t >= up && t < down) k = Math.max(k, out3((t - up) / .3));
    else if (t >= down) k = Math.max(k, 1 - out3((t - down) / .3));
  }
  return k;
}
// cfg: {title, clock(t), face(t) → [expression, glow], level(t) → {level, stage}, look(t), msgs, typing [{from, to, text,
// send}], keyboard [[up, down]], fresh (from then on only newer lines, under Ember), xp [{at, text, until}], extra(t)}
export function chatScreen(t, cfg, e, step) {
  const fresh = cfg.fresh != null && t >= cfg.fresh;
  s.fillStyle = C.bg; s.fillRect(0, 0, SW, SH);
  const g = s.createRadialGradient(SW / 2, 380, 30, SW / 2, 380, 620);
  g.addColorStop(0, "rgba(255,150,70,.22)"); g.addColorStop(1, "rgba(255,120,50,0)"); s.fillStyle = g; s.fillRect(0, 0, SW, SH);
  statusBar(cfg.clock ? cfg.clock(t) : "18:01");
  s.strokeStyle = C.text; s.lineWidth = 4; s.lineCap = "round";
  for (let i = 0; i < 3; i++) { s.beginPath(); s.moveTo(40, 104 + i * 13); s.lineTo(72, 104 + i * 13); s.stroke(); }
  txt(cfg.title || "Our first chat", SW / 2, 118, 30, 800, C.text, "center");
  s.beginPath(); s.moveTo(SW - 56, 102); s.lineTo(SW - 56, 134); s.moveTo(SW - 72, 118); s.lineTo(SW - 40, 118); s.stroke();
  // Ember
  const [ex, gl] = cfg.face ? cfg.face(t) : ["calm", .7]; e.face(ex, gl);
  const lv = cfg.level ? cfg.level(t) : { level: 5, stage: "Ember" }; e.state.level = lv;
  if (cfg.look) e.state.look = cfg.look(t);
  if (step) e.at(t);
  s.drawImage(e.canvas, SW / 2 - 240, 150, 480, 480);
  const label = `${cfg.name || "Ember"} · Lv ${lv.level}`; s.font = `800 26px ${F}`; const lw = s.measureText(label).width + 56;
  rr(SW / 2 - lw / 2, 598, lw, 46, 23); s.fillStyle = C.raised; s.fill();
  txt(label, SW / 2, 622, 26, 800, cfg.levelAt && t > cfg.levelAt && t < cfg.levelAt + 1.6 ? C.btn : C.text, "center");
  // the input and the keyboard
  const kb = kbAmount(t, cfg.keyboard || []), kbTop = SH - 540 * kb, inTop = kbTop - 128;
  const typing = (cfg.typing || []).find(w => t >= w.from - .3 && t < w.send);
  // the conversation: newest at the bottom, each line growing in and pushing the others up
  s.save(); s.beginPath(); s.rect(0, 666, SW, inTop - 666); s.clip();
  const shown = cfg.msgs.filter(m => t >= m.at && !(m.end && t >= m.end + .15) && (!fresh || m.at >= cfg.fresh));
  // after a cut the new lines start under Ember, until they no longer fit; then they scroll like any chat
  const fits = fresh && shown.reduce((h, m) => h + (msgSize(m).h + 20) * out3((t - m.at) / .3), 676) <= inTop - 10;
  if (fits) {
    let y = 676;
    for (const m of shown) { const sz = msgSize(m), grow = out3((t - m.at) / .3); drawMsg(m, sz, y, t, grow); y += (sz.h + 20) * grow; }
  } else {
    let y = inTop - 16;
    for (let i = shown.length - 1; i >= 0 && y > 600; i--) {
      const m = shown[i], sz = msgSize(m), grow = m.at <= 0 ? 1 : out3((t - m.at) / .3), gone = m.end ? 1 - clamp((t - m.end) / .15) : 1;
      y -= (sz.h + 20) * grow * gone;
      drawMsg(m, sz, y + 20, t, grow * gone);
    }
  }
  s.restore();
  s.fillStyle = C.bg; s.fillRect(0, inTop, SW, kbTop - inTop);
  rr(26, inTop + 24, SW - 140, 82, 41); s.fillStyle = C.surface; s.fill(); s.strokeStyle = "rgba(255,245,235,.12)"; s.lineWidth = 2; s.stroke();
  if (typing && t >= typing.from) {
    const p = clamp((t - typing.from) / (typing.to - typing.from)), shownTxt = typing.text.slice(0, Math.round(typing.text.length * p));
    s.font = `600 31px ${F}`; let shownLine = shownTxt; while (s.measureText(shownLine).width > SW - 220) shownLine = shownLine.slice(1);
    txt(shownLine, 58, inTop + 66, 31, 600);
    if ((t * 2.2) % 1 < .6) { s.fillStyle = C.btn; s.fillRect(60 + s.measureText(shownLine).width + 4, inTop + 46, 3, 40); }
    typing.p = p;
  } else txt(cfg.placeholder || "Message Ember…", 58, inTop + 66, 31, 600, C.faint);
  s.fillStyle = C.btn; s.beginPath(); s.arc(SW - 66, inTop + 65, 41, 0, Math.PI * 2); s.fill();
  s.strokeStyle = C.ink; s.lineWidth = 6; s.beginPath(); s.moveTo(SW - 66, inTop + 84); s.lineTo(SW - 66, inTop + 46); s.moveTo(SW - 82, inTop + 61); s.lineTo(SW - 66, inTop + 46); s.lineTo(SW - 50, inTop + 61); s.stroke();
  if (kb > 0) keyboard(kbTop, typing);
  for (const w of cfg.typing || []) ring(t, w.send - .15, SW - 66, inTop + 65);
  for (const m of shown) if (m.tap != null && m._tap) ring(t, m.tap - .1, m._tap[0], m._tap[1]);
  for (const x of cfg.xp || []) {
    const a = clamp(Math.min((t - x.at) / .15, ((x.until ?? x.at + 1.4) - t) / .25)); if (a <= 0) continue;
    s.save(); s.globalAlpha = a; s.translate(SW / 2 + 220, 470 - out3((t - x.at) / 1.2) * 70); const k = back((t - x.at) / .35); s.scale(k, k);
    s.font = `900 36px ${F}`; const w = s.measureText(x.text).width + 60;
    rr(-w / 2, -38, w, 76, 38); s.fillStyle = C.btn; s.fill(); txt(x.text, 0, 2, 36, 900, C.ink, "center"); s.restore();
  }
  cfg.extra?.(t, { inTop, kbTop });
}

// ---- a real screenshot of the app on the screen (web/img/shot-*.webp, 390×844 at 2×), moved and zoomed
export function shotScreen(name, { y = 0, zoom = 1, fx = SW / 2, fy = SH / 2 } = {}) {
  s.fillStyle = C.bg; s.fillRect(0, 0, SW, SH);
  s.save(); s.translate(fx, fy); s.scale(zoom, zoom); s.translate(-fx, -fy - y); s.drawImage(window.IMGS[name], 0, 0, SW, SH); s.restore();
}
// dims everything on the screen but one box, and rings the box in orange
export function spotlight(x, y, w, h, a) {
  if (a <= 0) return;
  s.save(); s.globalAlpha = a * .6; s.fillStyle = "#000"; s.beginPath(); s.rect(0, 0, SW, SH); s.roundRect(x, y, w, h, 24); s.fill("evenodd");
  s.globalAlpha = a; s.strokeStyle = C.btn; s.lineWidth = 5; rr(x, y, w, h, 24); s.stroke(); s.restore();
}

// ---- the camera: keys [{t, x, y, w, r, cut}] (a key with cut jumps there at its time); shakes [[from, to, amount]]
export function camera(t, keys, shakes = []) {
  let i = 0; while (i < keys.length - 1 && t >= keys[i + 1].t) i++;
  const a = keys[i], b = keys[i + 1];
  let cam;
  if (!b || b.cut) cam = { ...a };
  else { const k = ease((t - a.t) / (b.t - a.t)), m = p => (a[p] ?? 0) + ((b[p] ?? 0) - (a[p] ?? 0)) * k; cam = { x: m("x"), y: m("y"), w: m("w"), r: m("r") }; }
  cam.r = (cam.r || 0) + Math.sin(t * .9) * .003;
  for (const [from, to, amt = 7] of shakes) if (t > from && t < to) { cam.x += Math.sin(t * 95) * amt; cam.r += Math.sin(t * 77) * amt * .0009; }
  return cam;
}
export function room(cam, hue = 26, strength = .3) {
  c.fillStyle = "#0d0907"; c.fillRect(0, 0, W, H);
  const g = c.createRadialGradient(cam.x, cam.y - 200, 50, cam.x, cam.y, 1300);
  g.addColorStop(0, `hsla(${hue}, 100%, 62%, ${strength})`); g.addColorStop(.5, `hsla(${hue - 6}, 70%, 36%, ${strength / 3})`); g.addColorStop(1, "rgba(0,0,0,0)");
  c.fillStyle = g; c.fillRect(0, 0, W, H);
}
export function phone(cam, alpha = 1) {
  const w = cam.w, h = w * SH / SW, b = w * .03;
  c.save(); c.globalAlpha = alpha; c.translate(cam.x, cam.y); c.rotate(cam.r || 0);
  c.shadowColor = "rgba(0,0,0,.6)"; c.shadowBlur = 90; c.shadowOffsetY = 40;
  c.beginPath(); c.roundRect(-w / 2 - b, -h / 2 - b, w + 2 * b, h + 2 * b, w * .14); c.fillStyle = "#090706"; c.fill();
  c.shadowColor = "transparent"; c.strokeStyle = "rgba(255,235,215,.16)"; c.lineWidth = 3; c.stroke();
  c.beginPath(); c.roundRect(-w / 2, -h / 2, w, h, w * .115); c.save(); c.clip();
  c.drawImage(scr, -w / 2, -h / 2, w, h); c.restore();
  c.beginPath(); c.roundRect(-w * .14, -h / 2 + w * .025, w * .28, w * .075, w * .04); c.fillStyle = "#000"; c.fill();
  c.restore();
}

// ---- words over the video
// captions [[from, to, text, y]]: TikTok style, white boxes that grow as each word pops in
export function captions(t, list) {
  for (const [a, b, text, y0 = 200] of list) {
    if (t < a || t > b) continue;
    const font = `900 62px ${F}`, ls = lines(text, 860, font), out = clamp((b - t) / .18);
    let k = 0;
    c.save(); c.globalAlpha = out; c.font = font; c.textBaseline = "middle"; c.textAlign = "left";
    ls.forEach((l, li) => {
      const y = y0 + li * 96, lw = c.measureText(l).width, x0 = W / 2 - lw / 2, sp = c.measureText(" ").width;
      let x = x0, right = null; const words = [];
      for (const w of l.split(" ")) { const ww = c.measureText(w).width, p = Math.min(1.03, back((t - a - k * .07) / .22)); words.push([w, x, ww, p]); if (p > 0) right = x + ww; x += ww + sp; k++; }
      if (right === null) return;
      c.beginPath(); c.roundRect(x0 - 26, y - 44, right - x0 + 52, 88, 20); c.fillStyle = "#fff8f0"; c.fill();
      for (const [w, wx, ww, p] of words) if (p > 0) { c.save(); c.translate(wx + ww / 2, y); c.scale(p, p); c.fillStyle = "#1a0f08"; c.fillText(w, -ww / 2, 2); c.restore(); }
    });
    c.restore();
  }
}
// a black card with a line on it ("45 minutes later"), centred on `at`
export function titleCard(t, at, text, half = .3) {
  const k = Math.min(clamp((t - (at - half)) / .12), clamp((at + half - t) / .12)); if (k <= 0) return;
  c.fillStyle = `rgba(8,6,5,${k})`; c.fillRect(0, 0, W, H);
  c.save(); c.globalAlpha = k; c.font = `900 84px ${F}`; c.fillStyle = "#fff4e8"; c.textAlign = "center"; c.textBaseline = "middle";
  lines(text, 900, c.font).forEach((l, i, all) => c.fillText(l, W / 2, H / 2 - 80 + (i - (all.length - 1) / 2) * 100)); c.restore();
}
// a white flash (a level-up, a reveal)
export function flash(t, at, len = .35, max = .7) {
  const k = (t - at) / len; if (k < 0 || k > 1) return;
  c.save(); c.globalAlpha = (1 - k) * max; c.fillStyle = "#fff3e0"; c.fillRect(0, 0, W, H); c.restore();
}
let noise;
export function grain() {
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

// ---- the sounds that go with a chat and a lock screen
export function chatSounds(cfg) {
  const out = [];
  for (const w of cfg.typing || []) {
    [...w.text].forEach((ch, i) => out.push(["key", w.from + (i + .5) / w.text.length * (w.to - w.from)]));
    out.push(["tap", w.send - .15], ["send", w.send]);
  }
  for (const m of cfg.msgs) {
    if ((m.who === "ember" || m.who === "card") && m.at > 0) out.push(["pop", m.at]);
    if (m.tap != null) out.push(["tap", m.tap - .1]);
  }
  return out;
}
export const lockSounds = notes => notes.flatMap(n => [["buzz", n.at - .05], [n.red ? "bonk" : "ding", n.at]]);
// the face's expression over time: [[from, expression, glow], ...]
export const timeline = list => t => { let r = list[0]; for (const x of list) if (t >= x[0]) r = x; return [r[1], r[2]]; };
