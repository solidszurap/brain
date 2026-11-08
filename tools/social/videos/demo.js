// The product demo (2026-11-08, Szilard: "a demo video of the app which shows how the product works"): 16:9, about 80
// seconds, for the website, YouTube, applications and anyone who asks what Ember is. Not a post (the 14 reels are).
// The phone sits on the left, each step is explained on the right, and the screens are the real app: the chat is drawn
// live as the app looks today (tab bar, Send, the goal bar), and the pages are screenshots of the made-up demo Ember
// (web/img and tools/social/img). The story: a first chat about quitting running → Ember proposes a goal → two weeks
// later, today's check on the goal's page, a badge levels up, Ember answers, the path → a check-up at 18:00 → what it
// knows → the experiment that found their drawing → looks and badges → the price → yourember.app.
// Every claim is true of the app (CLAUDE.md); no privacy selling points, no model name.
import * as K from "../kit.js";
const { C, makeEmber, clamp, ease, out3, back, appear, say, lines, bg, ember } = window;
const c = window.c;
const PX = 640;                       // the phone's centre, left of the middle; the words sit to its right
const T = {
  phoneIn: 4.5,
  hi: 5.8, type1: [6.8, 8.7, 8.95], dots1: 9.2, ember1: 10.5, type2: [11.3, 12.7, 12.95], dots2: 13.2, ember2: 14.5,
  card: 15.3, pick: 17.9,
  later: 19.45,                       // "Two weeks later" covers the cut to the goal's page
  tap: 21.3, sheet: 21.75, nice: 24.3, reply: 24.9, scroll: [26.9, 28.3],
  checkups: 33.6, lock: 37.0, note: 37.6, open: 39.5, type3: [40.3, 41.7, 41.95], answer: 43.5,
  knows: 45.0, find: 52.0, looks: 59.5, badges: 64.2, out: 69.0,
  price: 69.6, end: 75.0, dur: 80.5,
};
let e, big;

// ---- the first chat: they say what they want, Ember asks once, then proposes a goal with a plan
const GOAL = "Run 5 km without stopping";
const chat1 = {
  app: true,
  title: t => t >= T.pick + .4 ? GOAL : "Our first chat",
  clock: () => "20:14",
  face: K.timeline([[0, "eager", .8], [T.dots1, "curious", .75], [T.ember2, "happy", .85], [T.pick, "eager", .95]]),
  level: t => ({ level: 1, stage: "Spark", progress: t < T.pick + .2 ? .28 : .28 + .4 * out3((t - T.pick - .2) / .6) }),
  fresh: 5.0,
  typing: [{ from: T.type1[0], to: T.type1[1], text: "I want to get fit, but I always quit running after a week.", send: T.type1[2] },
           { from: T.type2[0], to: T.type2[1], text: "I go too hard, it hurts, then I skip a day.", send: T.type2[2] }],
  keyboard: [[T.type1[0] - .4, T.type2[2] + .35]],
  bar: t => t >= T.pick + .5 ? { title: GOAL, phase: "phase 1/3", today: "Today: walk 5 min, then run 1 and walk 2, six times", k: out3((t - T.pick - .5) / .35) } : null,
  msgs: [
    { who: "ember", text: "Hi, I'm Ember! What's on your mind lately?", at: T.hi },
    { who: "you", text: "I want to get fit, but I always quit running after a week.", at: T.type1[2] },
    { who: "dots", at: T.dots1, end: T.ember1 },
    { who: "ember", text: "That's really common, and it's fixable. What usually makes you stop?", at: T.ember1 },
    { who: "you", text: "I go too hard, it hurts, then I skip a day.", at: T.type2[2] },
    { who: "dots", at: T.dots2, end: T.ember2 },
    { who: "ember", text: "Then we start gentle on purpose. Here's a plan you can start today:", at: T.ember2 },
    { who: "card", at: T.card, title: GOAL, button: "Make this my goal", pressed: "Your goal now ✓", tap: T.pick,
      lines: ["Done when: you run 5 km in one go", "6 weeks, in 3 phases of 2 weeks", "Today: walk 5 min, then run 1 and walk 2, six times"] },
  ],
  xp: [{ at: T.pick + .1, text: "+20 XP", x: K.SW / 2 + 170, y: 1010 }],
};

// ---- the app's screenshots, under a phone's status bar (taken in a browser, they have none of their own)
const BAR = 56, SC = (K.SH - BAR) / K.SH, OX = (K.SW - K.SW * SC) / 2;
function onPhone(clock, paint) {      // paint draws in screenshot pixels (780 × 1688)
  const s = K.s; s.fillStyle = C.bg; s.fillRect(0, 0, K.SW, K.SH);
  s.save(); s.translate(OX, BAR); s.scale(SC, SC); paint(); s.restore();
  s.fillStyle = C.bg; s.fillRect(0, 0, K.SW, BAR); K.statusBar(clock);
}

// ---- two weeks later, the goal's page: today's check (before → after), a badge levels up, Ember's answer, the path
const TOP = 124, TAB = 116;           // the page's own top bar and the tab bar, in screenshot pixels (they don't scroll)
const SCROLL = 1000;
const scrollAt = t => SCROLL * ease((t - T.scroll[0]) / (T.scroll[1] - T.scroll[0]));
function tallAt(sc) {                 // the whole goal page (one tall screenshot), scrolled, under its fixed bars
  const s = K.s, img = window.IMGS["goal-tall"], view = K.SH - TOP - TAB;
  s.drawImage(img, 0, TOP + sc, K.SW, view, 0, TOP, K.SW, view);
  s.drawImage(img, 0, 0, K.SW, TOP, 0, 0, K.SW, TOP);
  s.drawImage(img, 0, img.height - TAB, K.SW, TAB, 0, K.SH - TAB, K.SW, TAB);
}
const sheetAt = t => t < T.nice ? out3((t - T.sheet) / .35) : 1 - out3((t - T.nice - .05) / .3);
function goalPage(t) { onPhone("19:05", () => goalPaint(t)); }
function goalPaint(t) {
  const s = K.s, I = window.IMGS;
  s.fillStyle = C.bg; s.fillRect(0, 0, K.SW, K.SH);
  const k = sheetAt(t), after = clamp((t - T.sheet - .05) / .3);    // the page updates behind the sheet as it comes up
  if (after < 1) {
    s.drawImage(I["goal-before"], 0, 0, K.SW, K.SH);
    if (t >= T.tap + .05) s.drawImage(I["goal-after"], 60, 532, 210, 106, 60, 532, 210, 106);   // Did it lights up
  }
  if (after > 0) { s.save(); s.globalAlpha = after; tallAt(scrollAt(t)); s.restore(); }
  K.ring(t, T.tap - .1, 165, 585);
  // the app's "+25 XP" for the check
  const a = clamp(Math.min((t - T.tap - .1) / .15, (T.tap + 1.5 - t) / .25));
  if (a > 0) {
    s.save(); s.globalAlpha = a; s.translate(390, 700 - out3((t - T.tap - .1) / 1.2) * 40); const b = back((t - T.tap - .1) / .35); s.scale(b, b);
    K.rr(-112, -38, 224, 76, 38); s.fillStyle = C.btn; s.fill(); K.txt("+25 XP", 0, 2, 36, 900, C.ink, "center"); s.restore();
  }
  // the badge that levelled up: the app's own sheet (from the screenshot taken right after the check)
  if (k > 0) s.drawImage(I["goal-after"], 0, 844, K.SW, 844, 0, 844 + (1 - k) * 844, K.SW, 844);
  if (k > .9) K.ring(t, T.nice - .1, 490, 1592);
  // Ember's answer, already there when the sheet goes; then the path, with today's stop
  K.spotlight(34, 806, 712, 272, clamp(Math.min((t - T.reply) / .3, (T.scroll[0] - t) / .25)));
  if (t > T.scroll[1]) K.ring(t, T.scroll[1] + .35, 459, 2242 - SCROLL);
}

// ---- a check-up at the time they chose, and their answer in the goal's chat
const lock = { time: "18:00", date: "Monday 9 November", notes: [{ at: T.note, text: "Today's step: run 12 minutes without stopping. How did it go?" }] };
const chat2 = {
  app: true,
  title: GOAL,
  clock: () => "18:01",
  face: K.timeline([[0, "curious", .8], [T.type3[2], "eager", .9], [T.answer, "happy", .95]]),
  level: t => ({ level: 5, stage: "Ember", progress: t < T.type3[2] + .2 ? .16 : .16 + .04 * out3((t - T.type3[2] - .2) / .6) }),
  fresh: T.open - .25,
  placeholder: "Ask about Run 5 km without…",
  bar: { title: GOAL, phase: "phase 2/3", today: "Today: run 12 minutes without stopping" },
  typing: [{ from: T.type3[0], to: T.type3[1], text: "Did it! 12 minutes, no walking.", send: T.type3[2] }],
  keyboard: [[T.type3[0] - .4, T.type3[2] + .35]],
  msgs: [
    { who: "ember", text: "Today's step: run 12 minutes without stopping. How did it go?", at: T.open - .2 },
    { who: "you", text: "Did it! 12 minutes, no walking.", at: T.type3[2] },
    { who: "dots", at: T.type3[2] + .3, end: T.answer },
    { who: "ember", text: "Twelve minutes without stopping! Two weeks ago, one minute hurt. That's real progress.", at: T.answer },
  ],
  xp: [{ at: T.type3[2] + .15, text: "+10 XP" }],
};

// ---- what the phone shows: [from, screen, how it comes in]
const SCREENS = [
  [0, "chat1"], [T.later, "goal", "cut"], [T.checkups, "checkups", "slide"], [T.lock, "lock", "slide"], [T.open, "chat2", "fade"],
  [T.knows, "knows", "slide"], [T.find, "first", "slide"], [T.looks, "looks", "slide"], [T.badges, "badges", "slide"],
];
// spotlights on the screenshots: [from, x, y, w, h] in screenshot pixels (390×844 at 2×)
const SPOTS = {
  checkups: [[T.checkups + .6, 34, 712, 712, 474]],
  knows: [[T.knows + .7, 32, 1004, 708, 340]],
  first: [[T.find + .7, 40, 776, 616, 380]],
  looks: [[T.looks + .6, 24, 926, 732, 680]],
  badges: [[T.badges + .6, 28, 370, 724, 890]],
};
const CLOCK = { checkups: "21:30", knows: "12:40", first: "12:41", looks: "12:43", badges: "12:44" };
const SLIDE = .3;
function draw1(kind, t, until) {
  if (kind === "chat1") return K.chatScreen(t, chat1, e, true);
  if (kind === "chat2") return K.chatScreen(t, chat2, e, true);
  if (kind === "goal") return goalPage(t);
  if (kind === "lock") { const r = K.lockScreen(t, lock); if (r[0]) K.ring(t, T.open - .3, K.SW / 2, r[0].y + 80); return; }
  onPhone(CLOCK[kind] || "12:30", () => {
    K.s.drawImage(window.IMGS[kind], 0, 0, K.SW, K.SH);
    for (const [at, x, y, w, h] of SPOTS[kind] || []) K.spotlight(x, y, w, h, clamp(Math.min((t - at) / .3, (until - .15 - t) / .2)));
  });
}
function screen(t) {
  let i = 0; for (let k = 0; k < SCREENS.length; k++) if (t >= SCREENS[k][0]) i = k;
  const [from, kind, how] = SCREENS[i], until = SCREENS[i + 1]?.[0] ?? T.price;
  const k = !how || how === "cut" ? 1 : out3((t - from) / (how === "fade" ? .3 : SLIDE));
  if (k >= 1) return draw1(kind, t, until);
  const s = K.s, prev = SCREENS[i - 1][1];
  if (how === "fade") { draw1(kind, t, until); s.save(); s.globalAlpha = 1 - k; draw1(prev, t, from); s.restore(); return; }
  s.save(); s.translate((1 - k) * K.SW, 0); draw1(kind, t, until); s.restore();       // like switching tabs
  s.save(); s.translate(-k * K.SW, 0); draw1(prev, t, from); s.restore();
}

// ---- the words beside the phone: one step at a time
const STEPS = [
  [5.7, 14.3, "Talk to it like a friend", "Tell Ember what you want, or that you don't know yet. It asks a question or two."],
  [14.6, 19.15, "Get a plan you can start today", "Ember proposes a goal, in phases of one to two weeks. One tap makes it yours."],
  [19.85, 33.4, "One small step a day", "Every goal has its own page: today's step, a one-tap check, and a path that fills in day by day."],
  [33.8, 44.8, "It checks up on you", "At the time and on the days you choose, Ember writes first, right on your phone."],
  [45.2, 51.8, "It remembers your story", "What matters to you, kept in your own words, with the date you said it."],
  [52.2, 59.3, "It helps you find what you want", "Not sure yet? Ember suggests small experiments, based on what you've told it."],
  [59.7, 68.9, "It grows with you", "Progress earns XP. Ember levels up, unlocks new looks, and you collect badges to share."],
];
const TX = 1090, TW = 720;
function balanced(text, maxW, font) {       // like CSS text-wrap: balance, for one or two lines
  const greedy = lines(text, maxW, font); if (greedy.length !== 2) return greedy;
  const words = text.split(" "); c.font = font; let best = greedy, bestW = Infinity;
  for (let i = 1; i < words.length; i++) {
    const a = words.slice(0, i).join(" "), b = words.slice(i).join(" "), w = Math.max(c.measureText(a).width, c.measureText(b).width);
    if (w <= maxW && w < bestW) { best = [a, b]; bestW = w; }
  }
  return best;
}
function stepText(t) {
  STEPS.forEach(([from, to, head, body], i) => {
    const a = clamp(Math.min((t - from) / .45, (to - t) / .3)); if (a <= 0) return;
    const headF = "900 74px Nunito, ui-rounded, system-ui, sans-serif";
    const hls = balanced(head, TW, headF), hl = hls.length, bl = lines(body, TW - 20, `600 40px Nunito, ui-rounded, system-ui, sans-serif`).length;
    const h = 72 + 30 + hl * 74 * 1.12 + 26 + bl * 40 * 1.38 + 64, y0 = 540 - h / 2, dx = (1 - out3((t - from) / .6)) * 40;
    c.save(); c.globalAlpha = a; c.translate(dx, 0);
    // the step's number, in Ember's orange
    c.fillStyle = C.btn; c.beginPath(); c.arc(TX + 36, y0 + 36, 36, 0, Math.PI * 2); c.fill();
    c.font = "900 40px Nunito, ui-rounded, system-ui, sans-serif"; c.fillStyle = C.ink; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText(String(i + 1), TX + 36, y0 + 38);
    c.restore();
    const hy = y0 + 102;
    hls.forEach((l, li) => say(l, TX + dx, hy + li * 74 * 1.12, { size: 74, weight: 900, align: "left", maxW: 2000, alpha: a }));
    say(body, TX + dx, hy + hl * 74 * 1.12 + 26, { size: 40, weight: 600, align: "left", maxW: TW - 20, lh: 1.38, color: C.dim, alpha: a });
    // where you are in the tour: seven dots, this one long
    c.save(); c.globalAlpha = a * .9;
    for (let d = 0, x = TX + dx; d < STEPS.length; d++) { const w = d === i ? 44 : 14; c.beginPath(); c.roundRect(x, y0 + h - 14, w, 14, 7); c.fillStyle = d === i ? C.btn : "rgba(241,231,220,.22)"; c.fill(); x += w + 12; }
    c.restore();
  });
}

// ---- the opening, the price and the end
function intro(t, phoneOn) {
  if (t > T.phoneIn + .7) return;
  const fly = clamp((t - T.phoneIn) / .7), a = 1 - clamp((t - (T.phoneIn - .25)) / .55);
  if (!phoneOn) bg(430, .85); else if (fly < 1) { c.save(); c.globalAlpha = 1 - fly; bg(430, .85); c.restore(); }
  if (a <= 0) return;
  if (t >= .45 && t < .45 + 1 / 30) big.burst(24);
  big.face(t < 1.4 ? "eager" : "happy", .9);
  const pop = back((t - .25) / .55), size = 470 * (.55 + .45 * pop);
  if (t >= .25) ember(big, t, 960, 380, size, a * clamp((t - .25) / .2));
  say("ember", 960, 600, { size: 140, weight: 900, alpha: a * appear(t, 1.0, .5), rise: 30 });
  say("Your companion who checks up on you and grows with you.", 960, 790, { size: 46, weight: 700, color: C.dim, maxW: 1400, alpha: a * appear(t, 1.6, .5), rise: 20 });
}
function priceCard(t, x, y, w, h, at, title, big1, small, plus) {
  const a = appear(t, at, .45); if (a <= 0) return;
  const k = .92 + .08 * back((t - at) / .45);
  c.save(); c.globalAlpha = a; c.translate(x, y + h / 2); c.scale(k, k); c.translate(-x, -(y + h / 2));
  c.beginPath(); c.roundRect(x - w / 2, y, w, h, 40); c.fillStyle = C.surface; c.fill();
  c.strokeStyle = plus ? "rgba(255,168,98,.7)" : C.edge; c.lineWidth = plus ? 4 : 2; c.stroke();
  c.restore();
  say(title, x, y + 46, { size: 50, weight: 900, color: plus ? C.btn : C.text, alpha: a });
  say(big1, x, y + 128, { size: 46, weight: 800, alpha: a });
  say(small, x, y + 200, { size: 34, weight: 600, color: C.dim, maxW: w - 90, lh: 1.3, alpha: a });
}
function price(t) {
  if (t < T.price - .05 || t > T.end + .6) return;
  const a = clamp((t - T.price) / .45);
  c.save(); c.globalAlpha = a; bg(400, .75); c.restore();
  say("Start free", 960, 190, { size: 92, weight: 900, alpha: appear(t, T.price + .15, .5), rise: 30 });
  priceCard(t, 960 - 300, 370, 540, 330, T.price + .4, "Free", "10 messages a day", ["Daily checks and check-ups", "never count"].join("\n"), false);
  priceCard(t, 960 + 300, 370, 540, 330, T.price + .6, "Ember Plus", "No daily limit", ["$7.99 a month", "or $49.99 a year"].join("\n"), true);
  say("No ads. Cancel anytime.", 960, 790, { size: 40, weight: 700, color: C.dim, alpha: appear(t, T.price + 1.0, .5) });
}
function end(t) {
  if (t < T.end) return;
  const a = appear(t, T.end, .5);
  c.save(); c.globalAlpha = a; bg(420, .95); c.restore();
  if (t >= T.end + .15 && t < T.end + .15 + 1 / 30) big.burst(30);
  big.face("happy", .95);
  ember(big, t, 960, 380, 470 * (.6 + .4 * back((t - T.end - .05) / .55)), a);
  say("yourember.app", 960, 640, { size: 112, weight: 900, alpha: appear(t, T.end + .35, .5), rise: 30 });
  say("Find your purpose. Then live it, one step at a time.", 960, 800, { size: 48, weight: 700, color: C.dim, maxW: 1500, alpha: appear(t, T.end + .75, .5), rise: 20 });
}

// ---- the camera: where the phone is and how big (it moves in on what each step is about)
const fit = (t, sy, w, extra = {}) => ({ t, x: PX, y: 540 + (w * K.SH / K.SW) / 2 - sy * w / K.SW, w, r: 0, ...extra });
const GONE = 1800;
const CAM = [
  { t: 0, x: PX, y: GONE, w: 440, r: .04 }, { t: T.phoneIn, x: PX, y: GONE, w: 440, r: .04 },
  fit(5.3, 844, 440, { r: -.01 }), fit(6.4, 900, 500), fit(8.0, 1000, 560), fit(13.4, 1000, 560),
  fit(15.0, 1150, 580), fit(T.later - .3, 1150, 590),
  fit(T.later, 600, 600, { cut: true }), fit(T.tap - .3, 600, 620), fit(T.sheet, 610, 620), fit(T.sheet + .5, 1200, 600),
  fit(T.nice, 1200, 600), fit(T.reply + .1, 920, 610), fit(T.scroll[0], 920, 600), fit(T.scroll[1], 844, 520), fit(T.checkups - .3, 844, 520),
  fit(T.checkups + .6, 950, 600), fit(T.lock - .2, 950, 610), fit(T.lock + .4, 760, 560), fit(T.open, 780, 570),
  fit(T.open + .7, 1050, 590), fit(T.knows - .3, 1050, 600), fit(T.knows + .6, 1170, 630), fit(T.find - .3, 1170, 640),
  fit(T.find + .6, 960, 620), fit(T.looks - .3, 960, 630), fit(T.looks + .6, 1270, 600), fit(T.badges - .3, 1270, 610),
  fit(T.badges + .6, 800, 560), fit(T.out, 800, 570), { t: T.out + .6, x: PX, y: GONE, w: 470, r: -.03 },
];

export default {
  size: [1920, 1080],
  dur: T.dur,
  caption: "How Ember works: talk to it like a friend, get a plan you can start today, one small step a day, check-ups at your time, a memory of your story, and a companion that grows with you.",
  tags: "#ember #productdemo",
  music: { bpm: 92, chords: [[48, 60, 64, 67], [43, 59, 62, 67], [45, 57, 60, 64], [41, 57, 60, 65]], gain: .5 },
  sounds: [
    ["sparkle", .45], ["chime", 1.1], ["whoosh", T.phoneIn + .05],
    ...K.chatSounds(chat1), ["xp", T.pick + .1],
    ["whoosh", T.later - .3],
    ["tap", T.tap - .1], ["thump", T.tap], ["xp", T.tap + .12], ["levelup", T.sheet + .1], ["sparkle", T.sheet + .3],
    ["tap", T.nice - .1], ["whoosh", T.nice + .05], ["boop", T.reply, 4], ["whoosh", T.scroll[0]], ["boop", T.scroll[1] + .35, 7],
    ["whoosh", T.checkups], ["boop", T.checkups + .6, 4],
    ["whoosh", T.lock], ["buzz", T.note - .05], ["ding", T.note], ["tap", T.open - .3], ["whoosh", T.open],
    ...K.chatSounds(chat2), ["xp", T.type3[2] + .15],
    ["whoosh", T.knows], ["boop", T.knows + .7, 4],
    ["whoosh", T.find], ["boop", T.find + .7, 6],
    ["whoosh", T.looks], ["boop", T.looks + .6, 4], ["whoosh", T.badges], ["unlock", T.badges + .6],
    ["whoosh", T.out], ["pop", T.price + .4], ["pop", T.price + .6],
    ["chime", T.end + .15], ["sparkle", T.end + .3],
  ],
  init() { e = makeEmber(640); big = makeEmber(640); big.state.level = { level: 5, stage: "Ember" }; },
  draw(t) {
    const cam = K.camera(t, CAM), phoneOn = t >= T.phoneIn && t < T.out + .7;
    if (phoneOn) K.room(cam, 26, .32);
    intro(t, phoneOn);
    if (phoneOn) { screen(t); K.phone(cam); stepText(t); }
    price(t);
    end(t);
    K.titleCard(t, T.later, "Two weeks later", .32);
    K.grain(0);
  },
};
