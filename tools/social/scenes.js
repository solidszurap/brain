// The videos: one entry per video, in posting order. Each has its length (dur, seconds), the caption and hashtags to
// post with it, init() (a fresh Ember for each recording) and draw(t), which paints the moment t seconds in.
// Keep the text inside the safe area: nothing important above y 150 or below y 1520 (TikTok's and Instagram's buttons
// and captions cover those), and away from the right edge. Every claim must be true of the app (CLAUDE.md).
const { W, H, C, c, makeEmber, clamp, ease, out3, back, fade, appear, bg, say, ember, bubble, chat, pill, phone, lockScreen, tap, endCard, medal } = window;

let e;   // this video's Ember
const fresh = (look = {}, level = { level: 5, stage: "Ember" }) => () => { e = makeEmber(720); e.state.look = look; e.state.level = level; };

export default {
  // 1. it writes to you first
  "01-checks-up": {
    dur: 12, init: fresh(),
    caption: "An app that texts you first and asks how today's step went. No guilt if you didn't.",
    tags: "#accountability #goals #habits #selfimprovement #motivation",
    draw(t) {
      if (t < 4.6) {
        lockScreen(t, "18:00", "Wednesday", [{ at: .9, text: "Today's step: run 10 minutes. How did it go?" }]);
        say("The app that checks up on you", W / 2, 1180, { size: 70, alpha: appear(t, 1.8), rise: 30, maxW: 820 });
        tap(t, 3.7, 540, 790);
        return;
      }
      bg(560);
      e.face(t < 7 ? "curious" : "happy", t < 7 ? .6 : .95);
      ember(e, t, W / 2, 500, 640);
      const y = 860 + bubble("Today's step: run 10 minutes. How did it go?", "ember", 860, { alpha: appear(t, 4.8) }) + 90;
      const chips = ["Did it", "Partly", "Not today"];
      chips.forEach((ch, i) => pill(ch, 250 + i * 300, y, { alpha: appear(t, 5.4 + i * .1) * (t > 6.6 && i ? .35 : 1), size: 48,
        fill: i === 0 && t > 6.5 ? C.btn : C.raised, color: i === 0 && t > 6.5 ? C.ink : C.text, scale: i === 0 ? 1 + .12 * Math.max(0, Math.sin(clamp((t - 6.5) / .3) * Math.PI)) : 1 }));
      tap(t, 6.4, 250, y);
      const y2 = y + 100 + bubble("You did it. That's 3 days in a row.", "ember", y + 90, { alpha: appear(t, 7.4) });
      pill("+10 XP", W / 2, y2 + 80, { alpha: fade(t, 7.8, 9.4), scale: back((t - 7.8) / .4), size: 52 });
      endCard(t, 9.5, e);
    },
  },

  // 2. three questions
  "02-three-questions": {
    dur: 14, init: fresh(),
    caption: "Don't know what you want yet? Start with these 3 questions. Ember helps you test the answers with small experiments.",
    tags: "#findyourpurpose #selfdiscovery #purpose #selfimprovement #journaling",
    draw(t) {
      bg(460);
      const qs = ["What makes you lose track of time?", "What drains you, even when it goes well?", "What did you love doing at 12?"];
      say("Don't know what you want yet?", W / 2, 200, { size: 64, alpha: fade(t, .1, 2.2), maxW: 820 });
      say("Answer these 3", W / 2, 360, { size: 64, color: C.btn, alpha: fade(t, .5, 2.2), maxW: 820 });
      const k = Math.floor((t - 2.2) / 2.3);
      e.face(k >= 0 && k < 3 ? "curious" : "eager", .75);
      ember(e, t, W / 2, 760, 560);
      if (k >= 0 && k < 3) {
        const a = fade(t, 2.2 + k * 2.3, 2.2 + (k + 1) * 2.3 - .05, .3);
        say(`${k + 1} of 3`, W / 2, 1060, { size: 40, weight: 800, color: C.dim, alpha: a });
        say(qs[k], W / 2, 1130, { size: 72, alpha: a, rise: 30, maxW: 820 });
      }
      say("Then Ember turns your answers into small experiments.", W / 2, 1110, { size: 60, alpha: fade(t, 9.2, 11.6), rise: 30, maxW: 820 });
      endCard(t, 11.6, e, "Find your purpose. Then live it.");
    },
  },

  // 3. it grows
  "03-it-grows": {
    dur: 12, init: fresh({}, { level: 1, stage: "Spark" }),
    caption: "Your companion grows as you do. Spark, Ember, Flame, Blaze. Every level is earned by showing up.",
    tags: "#cozygames #selfcare #habittracker #goals #levelup",
    draw(t) {
      bg(800, .4 + Math.min(.5, t * .05));
      const steps = [[0, 1, "Spark"], [2.4, 5, "Ember"], [4.8, 10, "Flame"], [7.2, 20, "Blaze"]];
      const cur = [...steps].reverse().find(s => t >= s[0]) || steps[0];
      e.state.level = { level: cur[1], stage: cur[2] };
      e.face(t % 2.4 < .9 && t > 1 ? "surprised" : "happy", .85);
      say("Watch it grow with you", W / 2, 220, { size: 74, alpha: appear(t, .2), maxW: 820 });
      ember(e, t, W / 2, 820, 720);
      if (t < 9.6) {
        say(cur[2], W / 2, 1210, { size: 110, color: C.btn, alpha: appear(t, cur[0] + .05, .3) });
        say(`Level ${cur[1]}`, W / 2, 1350, { size: 50, weight: 800, color: C.dim, alpha: appear(t, cur[0] + .15, .3) });
      }
      endCard(t, 9.6, e, "Grows from showing up, never from paying");
    },
  },

  // 4. Monday, again
  "04-monday-again": {
    dur: 12, init: fresh(),
    caption: "POV: you said you'd start Monday. Again. Ember doesn't lecture. It finds a step small enough for today.",
    tags: "#procrastination #motivation #adhd #selfimprovement #habits",
    draw(t) {
      bg(420);
      say("POV: you said you'd start on Monday. Again.", W / 2, 190, { size: 66, alpha: appear(t, .1), maxW: 820 });
      e.face(t < 3.6 ? "calm" : t < 6.8 ? "curious" : "eager", .7);
      ember(e, t, W / 2, 560, 440);
      const y = chat(t, [["I'll start on Monday. For real this time.", "you", 1.2], ["No lecture. What's one thing small enough to do today, in 10 minutes?", "ember", 3.6],
        ["Put my running shoes by the door.", "you", 5.6]], 790);
      pill("Today's step: shoes by the door", W / 2, y + 50, { alpha: fade(t, 7, 9.6), scale: back((t - 7) / .4), size: 44 });
      endCard(t, 9.6, e);
    },
  },

  // 5. what it is
  "05-what-it-is": {
    dur: 15, init: fresh(),
    caption: "Ember in 15 seconds: talk it through, one step a day, it remembers your words, and it grows with you. Free to start.",
    tags: "#productivityapp #goals #aicompanion #selfimprovement #apps",
    draw(t) {
      bg(900);
      const parts = [["talk", "Talk it through"], ["goal", "One small step a day"], ["knows", "It remembers your words"], ["badges", "It grows with you"]];
      const k = clamp(Math.floor(t / 3), 0, 3), local = t - k * 3;
      if (t < 12.2) {
        const [img, line] = parts[k];
        say(line, W / 2, 180, { size: 72, alpha: fade(local, .05, 2.95, .25), rise: 20, maxW: 820 });
        const slide = 1 - out3(local / .45);
        phone(img, W / 2 + slide * 700, 960, 560, { rot: slide * .08 });
        if (k > 0 && local < .45) phone(parts[k - 1][0], W / 2 - out3(local / .45) * 700, 960, 560, { rot: -out3(local / .45) * .08 });
      }
      endCard(t, 12.2, e, "Free to start. No ads.");
    },
  },

  // 6. the notifications stack up
  "06-day-twelve": {
    dur: 12, init: fresh(),
    caption: "Day 12. It hasn't missed a day, even when I tried to.",
    tags: "#accountability #consistency #habits #goals #selfimprovement",
    draw(t) {
      if (t < 6.4) {
        lockScreen(t, "07:30", "Friday", [
          { at: .6, when: "now", text: "Day 12. Today's step: 20 minutes of drawing. You've got this." },
          { at: 1.6, when: "yesterday", text: "Partly is still progress. What got in the way?" },
          { at: 2.4, when: "Wed", text: "You said the interview is today. Thinking of you. Tell me how it went?" },
          { at: 3.1, when: "Tue", text: "5 days of steps. Your goal just reached level 2." },
        ]);
        return;
      }
      bg(700);
      e.face("eager", .95); ember(e, t, W / 2, 640, 600);
      say("12", W / 2, 960, { size: 220, color: C.btn, alpha: appear(t, 6.6), rise: 30 });
      say("days of showing up", W / 2, 1200, { size: 64, alpha: appear(t, 6.9), maxW: 820 });
      endCard(t, 9.6, e);
    },
  },

  // 7. not found your thing yet
  "07-not-found-yet": {
    dur: 13, init: fresh(),
    caption: "You don't find your purpose by thinking harder. You find it by trying small things and noticing what gives you energy.",
    tags: "#findyourpurpose #purpose #lifeadvice #selfdiscovery #mindset",
    draw(t) {
      bg(560);
      say("You won't find your purpose by thinking harder.", W / 2, 190, { size: 66, alpha: fade(t, .1, 4.4), maxW: 820 });
      say("You find it by trying.", W / 2, 520, { size: 80, color: C.btn, alpha: fade(t, 1.6, 4.4), maxW: 820 });
      e.face("curious", .75);
      if (t < 4.6) ember(e, t, W / 2, 1000, 520);
      if (t >= 4.4 && t < 10.6) {
        const a = fade(t, 4.4, 10.6);
        say("Ember suggests small experiments", W / 2, 180, { size: 62, alpha: a, maxW: 820 });
        phone("first", W / 2, 1030, 540, { alpha: a, scroll: 0 });
      }
      endCard(t, 10.6, e, "Find your purpose. Then live it.");
    },
  },

  // 8. dress it up
  "08-make-it-yours": {
    dur: 12, init: fresh(),
    caption: "Give your companion a name, a colour and a scarf. New looks open as you level up.",
    tags: "#cozy #cute #selfcare #habittracker #customization",
    draw(t) {
      bg(800);
      const looks = [
        [{}, "Amber"], [{ color: "rose", wear: "scarf" }, "Rose and a scarf"], [{ color: "ocean", wear: "headphones" }, "Ocean and headphones"],
        [{ color: "forest", wear: "beanie", cheeks: "freckles" }, "Forest and a beanie"], [{ color: "violet", wear: "glasses", eyes: "sparkly" }, "Violet and glasses"],
        [{ color: "aurora", wear: "crown", glow: "halo", sparks: "stars" }, "Aurora and a crown"],
      ];
      const k = clamp(Math.floor(t / 1.6), 0, looks.length - 1);
      e.state.look = looks[k][0]; e.state.level = { level: 25, stage: "Blaze" };
      e.face(t % 1.6 < .4 ? "surprised" : "happy", .9);
      if (Math.abs(t % 1.6) < 1 / 30 && t > .1 && t < 9.6) e.burst(14);
      say("Make it yours", W / 2, 200, { size: 80, alpha: appear(t, .1) });
      ember(e, t, W / 2, 800, 720);
      if (t < 9.6) say(looks[k][1], W / 2, 1230, { size: 60, color: C.btn, alpha: appear(t, k * 1.6, .25), maxW: 820 });
      endCard(t, 9.6, e, "New looks open as you level up");
    },
  },

  // 9. it remembered
  "09-it-remembered": {
    dur: 13, init: fresh(),
    caption: "It remembered what I said 3 weeks ago, in my exact words.",
    tags: "#aicompanion #journaling #selfimprovement #memory #mentalhealth",
    draw(t) {
      bg(420);
      say("It remembered what I said 3 weeks ago", W / 2, 190, { size: 66, alpha: fade(t, .1, 7.2), maxW: 820 });
      e.face(t < 3 ? "calm" : "happy", .8);
      if (t < 7.2) {
        ember(e, t, W / 2, 560, 480, fade(t, 0, 7.2));
        chat(t, [["Not sure what to do this weekend.", "you", .9, 7.2],
          ["On Oct 17 you said: “I lose track of time when I sketch.” Want to give that a Saturday morning?", "ember", 2.6, 7.2]], 860);
      }
      if (t >= 7 && t < 10.6) {
        const a = fade(t, 7, 10.6);
        say("Your words, with the date", W / 2, 180, { size: 66, alpha: a });
        phone("knows", W / 2, 1010, 540, { alpha: a });
      }
      endCard(t, 10.6, e, "It remembers your story, in your words");
    },
  },

  // 10. no guilt
  "10-no-guilt": {
    dur: 12, init: fresh(),
    caption: "Missed a day? It doesn't guilt-trip you. It makes tomorrow's step smaller.",
    tags: "#selfcompassion #habits #mentalhealth #goals #selfimprovement",
    draw(t) {
      bg(460);
      say("Missed a day?", W / 2, 200, { size: 80, alpha: appear(t, .1) });
      e.face(t < 3.4 ? "worried" : t < 5.6 ? "calm" : "happy", t < 3.4 ? .45 : .8);
      ember(e, t, W / 2, 580, 520);
      const y = 880 + bubble("Today's step: 20 minutes of drawing. How did it go?", "ember", 880, { alpha: appear(t, .6) }) + 80;
      pill("Not today", 780, y, { alpha: appear(t, 1.6), fill: t > 2.4 ? "#5a3a26" : C.raised, color: C.text, size: 48 });
      tap(t, 2.3, 780, y);
      bubble("That's okay, some days are like that. Tomorrow: just 5 minutes, pencil only?", "ember", y + 90, { alpha: appear(t, 3.4) });
      endCard(t, 9.6, e, "No guilt. Just the next small step.");
    },
  },

  // 11. three experiments
  "11-experiments": {
    dur: 14, init: fresh(),
    caption: "3 small experiments, a week each. The one that gives you energy is a clue.",
    tags: "#findyourpurpose #experiment #selfdiscovery #growthmindset #purpose",
    draw(t) {
      bg(380);
      say("3 small experiments, a week each", W / 2, 190, { size: 66, alpha: appear(t, .1), maxW: 820 });
      const xs = [["Sketch for 15 minutes a day", "Lost track of time twice", 5], ["Write 200 words before work", "Felt like a chore", 2], ["Help at a weekend class", "Came home buzzing", 5]];
      xs.forEach(([title, note, stars], i) => {
        const a = appear(t, 1 + i * 1.4, .45), y = 470 + i * 300;
        if (a <= 0) return;
        c.save(); c.globalAlpha = a; c.translate((1 - a) * 80, 0);
        c.beginPath(); c.roundRect(110, y, W - 220, 250, 40); c.fillStyle = C.surface; c.fill(); c.strokeStyle = C.edge; c.lineWidth = 2; c.stroke();
        say(title, 160, y + 40, { size: 48, weight: 800, align: "left", maxW: 760 });
        say(note, 160, y + 116, { size: 40, weight: 600, align: "left", color: C.dim, maxW: 760 });
        for (let s = 0; s < 5; s++) say("★", 160 + s * 50, y + 172, { size: 40, align: "left", color: s < stars ? C.btn : C.faint });
        c.restore();
      });
      if (t > 6) e.face("eager", .9);
      say("The ones that give you energy are clues.", W / 2, 1400, { size: 56, color: C.btn, alpha: appear(t, 6.2), maxW: 820 });
      if (t > 11.4) endCard(t, 11.4, e, "Find your purpose. Then live it.");
      else e.at(t);
    },
  },

  // 12. badges level up
  "12-badges": {
    dur: 11, init: fresh(),
    caption: "Badges that level up with you. Streaks, days together, goals reached.",
    tags: "#gamification #habittracker #streak #goals #levelup",
    draw(t) {
      bg(780);
      say("Badges that level up", W / 2, 200, { size: 80, alpha: appear(t, .1) });
      const lv = t < 2.6 ? 1 : t < 4.6 ? 2 : t < 6.6 ? 3 : 4, since = t - [0, 2.6, 4.6, 6.6][lv - 1];
      medal(W / 2, 800, 260, lv, 1, lv > 1 ? back(since / .5) * .15 + .85 : appear(t, .3) );
      say(["3 days in a row", "7 days in a row", "14 days in a row", "30 days in a row"][lv - 1], W / 2, 1150, { size: 66, alpha: appear(since, .05, .3) });
      say("On fire", W / 2, 1250, { size: 48, weight: 800, color: C.dim, alpha: appear(t, .4) });
      e.at(t);
      endCard(t, 8.6, e, "Share it when you're proud of it");
    },
  },

  // 13. the path
  "13-one-step-a-day": {
    dur: 13, init: fresh(),
    caption: "Your goal, one step a day. Every 5 days you show up, it levels up.",
    tags: "#goals #consistency #habittracker #discipline #selfimprovement",
    draw(t) {
      bg(700);
      say("Your goal, one step a day", W / 2, 190, { size: 68, alpha: appear(t, .1), maxW: 940 });
      // the path winds up the screen, the first day at the bottom; a skipped day stays dark
      const kinds = ["done", "done", "partly", "done", "done", "done", "skip", "done", "done", "done", "done", "partly"];
      const fill = { done: C.btn, partly: "#c98b5a", skip: "#4a3a2e" }, n = kinds.length;
      const pos = i => [W / 2 + Math.sin(i * .75) * 250, 1440 - i * 82];
      const shown = clamp(Math.floor((t - .8) / .62) + 1, 0, n);
      c.save(); c.strokeStyle = C.raised; c.lineWidth = 18; c.lineCap = "round"; c.beginPath();
      for (let i = 0; i < n; i++) { const [x, y] = pos(i); i ? c.lineTo(x, y) : c.moveTo(x, y); } c.stroke(); c.restore();
      for (let i = 0; i < n; i++) {
        const [x, y] = pos(i), a = i < shown ? appear(t, .8 + i * .62, .3) : 0;
        c.beginPath(); c.arc(x, y, 40, 0, Math.PI * 2); c.fillStyle = C.surface; c.fill();
        if (a > 0) { c.beginPath(); c.arc(x, y, 40 * back(a), 0, Math.PI * 2); c.fillStyle = fill[kinds[i]]; c.fill(); }
      }
      const did = kinds.slice(0, shown).filter(k => k !== "skip").length, level = 1 + Math.floor(did / 5);
      const upAt = .8 + (kinds.findIndex((k, i) => kinds.slice(0, i + 1).filter(x => x !== "skip").length === (level - 1) * 5)) * .62;
      pill(`Goal level ${level}`, W / 2, 380, { size: 56, alpha: appear(t, .6), scale: level > 1 ? 1 + .15 * Math.max(0, Math.sin(clamp((t - upAt) / .4) * Math.PI)) : 1 });
      say("Up a level every 5 days you show up", W / 2, 460, { size: 44, weight: 700, color: C.dim, alpha: appear(t, 1), maxW: 900 });
      e.at(t);
      endCard(t, 10.6, e);
    },
  },

  // 14. the deal
  "14-free-no-ads": {
    dur: 12, init: fresh(),
    caption: "Free to start: 10 messages a day, goals and check-ups included. No ads.",
    tags: "#apps #privacy #selfimprovement #goals #aicompanion",
    draw(t) {
      bg(560);
      e.face("happy", .85);
      ember(e, t, W / 2, 470, 440);
      const ls = ["Free: 10 messages a day", "Goals and check-ups too", "No ads", "Ember Plus: no daily limit"];
      ls.forEach((l, i) => {
        const a = appear(t, .8 + i * .9, .4);
        pill("✓", 150, 850 + i * 130, { alpha: a, size: 44 });
        say(l, 225, 822 + i * 130, { size: 58, weight: 800, align: "left", alpha: a, maxW: 800 });
      });
      endCard(t, 9.6, e, "Your companion who checks up on you");
    },
  },
};
