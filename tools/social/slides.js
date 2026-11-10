// Photo slideshows (2026-11-10): the format app accounts post most on TikTok ("photo mode", and Instagram carousels).
// A slideshow is a scene like any other, so `node make.mjs s1 --stills out/slides --at <mids>` writes its slides as
// PNGs (1080×1920; `at(n)` below gives the moments) and a plain render gives the same thing as a video. Each one is a
// hook slide, a few slides with one thought each, and a last slide with Ember and the address. The picture behind is one
// frame of a clip in clips/, dimmed. Text stays out of the top 150 px and the bottom 400 px.
const { c, makeEmber, clamp, say, ember, lines, C } = window;
export const EACH = 2.6;
export const at = n => Array.from({ length: n }, (_, i) => +(i * EACH + EACH / 2).toFixed(2)).join(",");
const F = "Nunito, ui-rounded, system-ui, sans-serif";

// slides: {hook} | {n, text, sub} | {quote} | {end, sub}
export function slideshow({ clip, frame = 1, fx = .5, fy = .5, slides, caption, tags }) {
  let e;
  function back(t, i) {
    window.clipDraw(clip, { zoom: 1.12 + (t - i * EACH) * .012, fx, fy });
    c.fillStyle = "rgba(13,9,7,.6)"; c.fillRect(0, 0, 1080, 1920);
    const g = c.createLinearGradient(0, 1100, 0, 1920); g.addColorStop(0, "rgba(13,9,7,0)"); g.addColorStop(1, "rgba(13,9,7,.75)");
    c.fillStyle = g; c.fillRect(0, 0, 1080, 1920);
  }
  const glow = (y, r, a) => {
    const g = c.createRadialGradient(540, y, 20, 540, y, r); g.addColorStop(0, `rgba(255,140,50,${a})`); g.addColorStop(1, "rgba(255,120,40,0)");
    c.save(); c.globalCompositeOperation = "lighter"; c.fillStyle = g; c.fillRect(0, 0, 1080, 1920); c.restore();
  };
  const height = (text, size, maxW) => lines(text, maxW, `900 ${size}px ${F}`).length * size * 1.15;
  function slide(s, t, i) {
    if (s.hook) {
      const h = height(s.hook, 104, 920), y = 760 - h / 2;
      say(s.hook, 540, y, { size: 104, maxW: 920, color: "#fff4e8" });
      glow(y + h + 250, 420, .4); e.face("curious", .9); ember(e, t, 540, y + h + 250, 420);
    } else if (s.quote) {
      const font = `800 74px ${F}`, ls = lines(s.quote, 800, font), h = ls.length * 96 + 110, y = 820 - h / 2;
      glow(y - 150, 380, .35); e.face(s.face || "happy", .9); ember(e, t, 250, y - 150, 300);
      c.save(); c.beginPath(); c.roundRect(80, y, 920, h, [16, 56, 56, 56]); c.fillStyle = C.surface; c.fill();
      c.strokeStyle = "rgba(255,245,235,.14)"; c.lineWidth = 3; c.stroke();
      c.font = font; c.fillStyle = "#fff4e8"; c.textBaseline = "top"; c.textAlign = "left";
      ls.forEach((l, k) => c.fillText(l, 140, y + 55 + k * 96)); c.restore();
    } else if (s.end) {
      glow(640, 620, .5); e.face("happy", 1); ember(e, t, 540, 640, 560);
      const h = say(s.end, 540, 960, { size: 78, maxW: 900, color: "#fff4e8" });
      const h2 = s.sub ? say(s.sub, 540, 960 + h + 30, { size: 48, weight: 700, lh: 1.3, color: "rgba(255,244,232,.75)", maxW: 880 }) + 30 : 0;
      const py = 960 + h + h2 + 50;
      c.save(); c.font = `900 60px ${F}`; const w = c.measureText("yourember.app").width + 110;
      c.beginPath(); c.roundRect(540 - w / 2, py, w, 120, 60); c.fillStyle = C.btn; c.fill();
      c.fillStyle = C.ink; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText("yourember.app", 540, py + 63); c.restore();
    } else {
      const h = height(s.text, 92, 900), sub = s.sub ? lines(s.sub, 860, `700 60px ${F}`).length * 60 * 1.3 + 40 : 0, y = 800 - (h + sub) / 2;
      if (s.n) {
        c.save(); c.beginPath(); c.arc(540, y - 130, 62, 0, Math.PI * 2); c.fillStyle = C.btn; c.fill();
        c.font = `900 68px ${F}`; c.fillStyle = C.ink; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText(String(s.n), 540, y - 126); c.restore();
      }
      say(s.text, 540, y, { size: 92, maxW: 900, color: "#fff4e8" });
      if (s.sub) say(s.sub, 540, y + h + 40, { size: 60, weight: 700, lh: 1.3, color: "rgba(255,244,232,.8)", maxW: 860 });
    }
  }
  return {
    dur: slides.length * EACH,
    clips: { [clip]: clip },
    caption, tags, slides: slides.length,
    sounds: slides.map((_, i) => [i ? "tick" : "pop", i * EACH + .02]).concat([["chime", (slides.length - 1) * EACH + .1]]),
    init() { e = makeEmber(640); },
    async prep() { await window.clipSeek(clip, frame); },
    draw(t) {
      const i = Math.min(slides.length - 1, Math.floor(t / EACH)), k = clamp((t - i * EACH) / .18);
      back(t, i);
      c.save(); c.globalAlpha = k; slide(slides[i], t, i); c.restore();
    },
  };
}

export const s1 = slideshow({
  clip: "night.mp4", fx: .4, fy: .45,
  slides: [
    { hook: "5 questions an app asked me that I couldn't answer" },
    { n: 1, text: "When do you lose track of time?" },
    { n: 2, text: "What did you love at 12 that you stopped doing?" },
    { n: 3, text: "What made you stop?" },
    { n: 4, text: "What would you still do if nobody ever saw it?" },
    { n: 5, text: "What's the smallest version you could try this week?" },
    { end: "It turned my answers into a 7 day experiment.", sub: "Ember helps you find what you want. Then checks you're doing it." },
  ],
  caption: "Number 3 got me. Which one can't you answer?",
  tags: "#findyourpurpose #selfdiscovery #journalprompts #whatdoiwant #purpose",
});
export const s2 = slideshow({
  clip: "kitchen.mp4", fx: .5, fy: .5,
  slides: [
    { hook: "why you quit on day 3 (it's not motivation)" },
    { n: 1, text: "Your plan is too big.", sub: "Make it 10 minutes. Seriously." },
    { n: 2, text: "Nobody asks if you did it.", sub: "So skipping costs nothing." },
    { n: 3, text: "One bad day ends the whole thing.", sub: "\"Not today\" has to be allowed." },
    { n: 4, text: "You can't see it adding up.", sub: "A streak you can look at changes that." },
    { end: "Mine asks me every day at 18:00.", sub: "Ember: a companion who checks up on you. Free to start." },
  ],
  caption: "It was never motivation. Which one is yours?",
  tags: "#habits #discipline #selfimprovement #accountability #consistency",
});
export const s3 = slideshow({
  clip: "desk.mp4", fx: .4, fy: .5,
  slides: [
    { hook: "things my 2 inch accountability partner said this week" },
    { quote: "Day 6 of guitar. 10 minutes today?", face: "curious" },
    { quote: "Sore fingers mean it's working." },
    { quote: "I love 2am you. Let's keep one of those plans alive.", face: "eager" },
    { quote: "Fair. Then just shoes on, to the end of the street.", face: "calm" },
    { quote: "Today was the one that counted." },
    { end: "It lives in my phone. It texts first.", sub: "Ember: your companion who checks up on you." },
  ],
  caption: "It's 2 inches tall and it has no chill. Meet Ember.",
  tags: "#accountabilitypartner #habits #cozydesk #selfimprovement #productivity",
});
export const s4 = slideshow({
  clip: "couch.mp4", fx: .5, fy: .4,
  slides: [
    { hook: "POV: 4 hobbies, 0 idea what you actually want" },
    { n: 1, text: "Stop trying to think your way to the answer." },
    { n: 2, text: "Pick one thing. Try it for 7 days." },
    { n: 3, text: "Each night, ask:", sub: "did it give me energy, or drain me?" },
    { n: 4, text: "Keep what gives you energy. Drop the rest. Repeat." },
    { end: "I run these experiments with Ember.", sub: "It asks the questions, and remembers what you said." },
  ],
  caption: "You don't find it by thinking. You find it by trying. What's your first 7 days?",
  tags: "#findyourpurpose #whatdoiwant #selfdiscovery #twenties #purpose",
});
export const s5 = slideshow({
  clip: "bus.mp4", frame: .3, fx: .5, fy: .5,
  slides: [
    { hook: "signs you don't need motivation. you need someone to check on you" },
    { n: 1, text: "You start strong every Monday." },
    { n: 2, text: "You only do it when someone's waiting." },
    { n: 3, text: "You've downloaded 6 habit apps.", sub: "And muted every reminder." },
    { n: 4, text: "Nobody knows when you quit." },
    { end: "Mine checks on me every day.", sub: "Ember: a companion who checks up on you and grows with you." },
  ],
  caption: "Number 4 is the real one. Tag who checks on you.",
  tags: "#accountability #habits #selfimprovement #discipline #relatable",
});
