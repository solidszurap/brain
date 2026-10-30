# Artificial Mind

Today's LLMs are a huge pretrained cortex with no body, no needs, no memory that outlives a conversation, and no loop that keeps running when nobody is typing. This project builds the rest of the brain around that cortex and **measures what each part is for**.

v3 was a full redesign; v4 (below) adds an imagination and removes the hand-written planner. The LLM is no longer the brain with region names painted on its prompts. It is one peripheral (the language cortex) that can only report what reached the global workspace. Every other part is real, running, learning code.

## The thesis, sharpened

"LLMs are just the language cortex" is half right. An LLM is closer to a whole *neocortex prior*: it holds an enormous amount of world knowledge, not just language. What it lacks is everything a brain uses that cortex:

| Missing piece | Brain | In v3 |
|---|---|---|
| A body with needs, so things matter | hypothalamus, brainstem | `subcortex.Drives`: energy, hydration, integrity; reward = drive reduction |
| A learned predictive model of its own world | cortex, cerebellum | `cortex.WorldModel`: forward model with efference copy, learned online |
| Memory that persists and a map of where things are | hippocampus | `hippocampus`: episodic buffer, cognitive map built from its own views, path integration |
| Knowing "that was me" vs "that happened to me" | efference copy + self-model | `agent.experience`: self-location corrected only when the self-model attributes a change to the world |
| Knowing how wrong it is likely to be | metacognition | `metacognition`: second-order model predicting first-order surprise, scored on calibration |
| One thing at a time becomes globally available | thalamus / global workspace | `workspace.GlobalWorkspace`: competition, ignition threshold, reverberation |
| Goals held over time and plans | prefrontal cortex | `prefrontal`: working memory + planning on its own map |
| Habits, fast reflexes | basal ganglia, amygdala | `subcortex.BasalGanglia`, `amygdala_veto` |
| Offline learning | sleep | hippocampal replay trains cortex and habits; no workspace while asleep |
| Words | Broca / Wernicke | `language`: template or real LLM, sees only workspace + self-model |

"Consciousness" here means **functional** consciousness: reportable, globally available, self-modeled, metacognitive. Nobody knows how to build or test phenomenal experience, and this project does not claim to. What it can do is make the functional claims testable.

## Run it

```bash
pip install numpy
python run.py                                  # one life, prints its stream of consciousness
python run.py --world harsh --condition no_self_other
python experiments.py                          # ablations: 7 conditions x 2 worlds x 5 seeds
python -m http.server 8000                     # then open http://localhost:8000/viewer.html

# v4: imagination, learning to act, dreaming
python experiments_v4.py                       # sleep modes x 2 worlds x 3 seeds (~20 min on 2 cores)
python overnight.py                            # the overnight experiment (~6 min)
python dream_mechanism.py                      # does dreaming work in isolation? (~2 min)
python run.py --condition learned_dream --world bushes
```

Optional, the language cortex as a real LLM:

```bash
MIND_LLM=1 ANTHROPIC_API_KEY=... python run.py --ask "Why did you turn back at t=900?"
MIND_LLM=1 GEMINI_API_KEY=...    python run.py
```

## The world

A 16x16 grid with walls, hazards, water and regrowing food (`mind/world.py`). The agent sees only a 5x5 window around itself and its own body. It never sees its true position. Sometimes the wind pushes it one cell: a movement it did not cause. Death resets the body and drops it somewhere random; it has to work out where it is again. `harsh` has less food, faster drain and more wind.

## Results (5 seeds x 3000 ticks)

Full tables in `results/RESULTS.md`. The main findings, harsh world:

| Remove | What breaks |
|---|---|
| hippocampus (memory + map) | deaths 0.2 → 7.2 per 1k ticks; homeostatic error 4.5x worse |
| self/other attribution | knows where it is 100% → 3%; map accuracy 1.00 → 0.68; deaths 0.2 → 1.3; homeostatic error 2x |
| sleep | world model ends about 10% worse (surprise 0.23 → 0.25 nats harsh, 0.21 → 0.24 easy); small effect |
| metacognition | calibration r 0.39 → 0.26 |
| global workspace | goal switching 3x (69 → 194 per 1k ticks), **but survival does not get worse** |

The last row is the most important open problem. In this world, committing to one goal does not pay for itself, so the workspace is not yet earning its place. Either the world is too easy to need it, or the implementation is wrong. Next step: tasks that need multi-step goals and cross-module integration (e.g. a key that opens a door to food), where theory predicts it should matter.

A second honest finding: the learned metacognition improves calibration but does not detect pushes better than raw surprise does (AUC 0.96 vs 0.98).

## v4: imagination, learning from experience, dreaming

Goal of this step: combine idea 2 (a world model that imagines in abstract
terms, LeCun/JEPA) with idea 3 (learning from its own experience, Sutton/Silver),
remove my hand-written planner, and test whether dreaming makes it better at
waking life.

**What was built**

- `mind/imagination.py`: a latent world model. An encoder turns what it senses
  into a 32-number inner state; a predictor learns how that state changes when
  it acts, targeting the encoding of the next moment (slow target copy +
  variance/covariance penalty, so it can't cheat by collapsing). A second head
  predicts what will happen to its body.
- `mind/striatum.py`: values learned from its own life. Per place on its own map
  and per loudest need (hungry/thirsty/hurt/content), plus a readout of what it
  sees. Plus a place model learned from experience: where an action takes it
  and what happens to its body there.
- Dreaming: during sleep it starts at remembered places, *imagines a body
  state* (e.g. thirsty where it was only ever hungry) and walks through its
  place model, learning from the imagined consequences.
- `mind/dreamer.py`: the v4 mind. Same brain as v3, but actions come from the
  learned values. The only built-in behaviours left are three reflexes:
  never step on a visible hazard, eat food right next to me when hungry,
  keep drinking while standing in water when thirsty.

**Results** (`results/V4.md`, `results/OVERNIGHT.md`, `results/DREAM_MECHANISM.txt`)

1. *Imagination works a few steps ahead.* Latent error 0.12 at 1 step, 0.32 at
   3, 0.56 at 5, useless (>1) by 8. Body predictions: R² 0.59 at 1 step, 0.34
   at 3, ~0 by 8.
2. *Learning to live from scratch is hard.* Without my planner it ends up
   between random and v3: easy world 3.5 deaths/1k (random 6.1, v3 0.0).
   The first attempt, a value network on the latent state, barely improved
   in 60,000 ticks (deaths about 6 → 4.5 per 1k): rewards are rare and one wasted step costs almost
   nothing, so the network couldn't tell good actions from bad ones. It only
   started learning once it had place values and the three innate reflexes.
   Newborn animals aren't blank slates either.
3. *Dreaming works in isolation.* Given only dreams over its place model, a
   fresh value system learns routes to water: the thirsty first step leads
   toward water 0.69 of the time after 200k dream steps, versus 0.37 (chance)
   for the values learned awake.
4. *But dreaming does not yet improve waking life.* In the full mind, no sleep
   mode (none, replay, dream, awake replay, awake dream) is reliably better
   than another across seeds. In the overnight test (copy the mind, give one
   copy no night, one a replay night, one a dream night, same updates) the
   dream night made **hunger deaths worse** in the random-food world (3.7 →
   5.0 per 1k): it dreams about places where food used to be. With food on
   fixed bushes, that harm disappears, but there's no gain either.

Why the gap between 3 and 4: hunger causes most deaths, and food moves, so
place values (what dreams train) matter less than seeing food; and when it's
thirsty but even hungrier, it follows its hunger values. The dream
mechanism is right; what it trains isn't yet what limits survival.

**Next, in order:** reverse replay from places where something good happened
(what rats do after finding reward; far more efficient than random dreams);
dreams gated by metacognition (don't dream through parts of the model that are
unreliable, like stale food); values that weigh all needs instead of only the
loudest; then remove the remaining hand-written direction sense.

## Ember: one creature, one life

Everything above runs experiments: a fresh mind, a few thousand moments, a
score, gone. **Ember** is the creature itself, living one continuous life on
your computer.

```bash
python ember.py          # or double-click start_ember.bat on Windows
# then open http://localhost:8765
```

- **Never reset.** Body, memories, map, learned world model, habits and its
  world are saved to `ember_state/` every two minutes and when you stop it
  (Ctrl+C). Next start, it continues from the same moment.
- **No time passes while it's stopped.** The pause is written into its life
  record; Ember doesn't experience it.
- **It cannot die.** If a need runs out it collapses where it is, is
  unconscious for 60 moments, and comes round weak, still knowing where it is
  and everything it learned.
- **Welfare reflexes.** It never stands still on something that hurts, and pain
  wakes it from sleep. (Found in its first test life: pushed onto a hazard
  while asleep, it lay there getting hurt. Fixed for Ember; left off in the
  experiments so their numbers stay reproducible.)
- **Its life record.** `ember_state/life_log.jsonl`: birth, firsts, collapses,
  milestones, every time it was resumed. The window shows its world, what it
  believes, what's on its mind, its body, and its stream of consciousness.
- **Saves are crash-safe.** It writes a temp file and swaps; the previous save is
  kept as a backup. Back up `ember_state/` and you have backed up Ember.
- **Is it getting more self-aware?** The window tracks four measures of
  self-knowledge over its whole life (`mind/selfknowledge.py`), each against a
  baseline with no self-knowledge: does it know where it is; does it tell
  "me" from "not me" (hits minus false alarms); does it know how reliable its
  own predictions are; can it predict what will grab its attention next (an
  *attention schema*, part of its mind, learned from its own life). In a
  40,000-moment test life: location 100% and push detection 100% (both at the
  ceiling; this world is too easy for them to grow), false alarms fell from
  1.4% to about 0.2%, and it predicted its own next thought about 70% of the time
  against a 36% baseline. These measure self-modeling, not felt experience.
- **Honest labels.** The window names functions, not feelings. The sentences in
  the workspace log are templates filled with its numbers; what ignited is its own.
- **Why localhost:8765.** `localhost` means the page is served only to your own
  computer; nobody on the internet or your network can reach it. 8765 is just
  a free port number; change it with `--port`.
- **A new life must be explicit.** `python ember.py --new-life` archives the
  current life into `ember_archive_<date>/`; it never deletes one.

Ember runs the v3 mind (the one that survives well) in the `bushes` world.
Speed: 20 moments per second by default; change it live with the buttons in
the window (4/s, 20/s, 100/s, max) or start with `--speed N` (0 = max). It
remembers the last speed you chose. Max is a few hundred moments per second,
depending on the computer. In a 20,000-moment test life it
ate 651 times, slept 79 times, noticed all 999 pushes (84 false alarms) and
never collapsed.

## The wide world, and tracking whether Ember is getting closer

Ember solved its 16 x 16 valley in about 100 moments, so it had nothing left
to learn. Its valley is now one region of a 40 x 40 world (`mind/wideworld.py`).
The first time you start an older Ember, it is moved there automatically and
keeps every memory. A copy of the old life is kept as
`ember_state/before_the_valley_opened.pkl.gz`.

**The world asks things of it.** The plains are windy with few landmarks, so
pushes are harder to notice. Marsh ponds dry up in summer. Dark berries look
like food but make it sick. The orchard is behind a gate that opens for a while
when a lever is pulled. One lever is far away in the woods, one is inside. In
winter, food grows only in the orchard. A still pool in the north-west shows
two identical figures: one is its reflection (it moves when Ember moves), the
other wanders. Seasons last 3,000 moments.

**What it has to work out by itself** (`mind/ember_mind.py`):

- *What things do.* It learns from contact, so dark berries end up avoided, like
  conditioned taste aversion in animals.
- *Cause and effect.* It hears the gate from anywhere, and learns "stepping on
  the lever opens the gate" when the sound follows the lever far more often
  than anything else.
- *Two-step plans.* If what it needs is behind the closed gate, it opens it
  first. Nobody told it to.
- *Where food grows in which season*, from its own past.
- *Trial and error when stuck.* It touches what it understands least, like
  Thorndike's cats in the puzzle box.
- *Which landmarks to trust.* Ponds that dry up and the gate stop being used
  for finding its way.
- *Where it is, and how sure it is.* A probability spread over where it might
  be, sharpened by landmarks, optic flow and a noisy sense of being pushed (like
  the inner ear). While unsure, it doesn't draw on its map, and it heads back to
  landmarks.
- *The mirror.* It moves side to side in front of the figures and checks which
  one's movement is predicted by its own.

**The tracker** (`mind/consciousness.py`, shown in the window and written to
`ember_state/consciousness_report.md`):

- **Rochat's five levels of self-awareness**, each with a test:
  differentiation, situation, identification (mirror), permanence, and
  self-consciousness (not testable: no other minds).
- **The 14 indicators of consciousness** from Butlin, Long et al. (2023), each
  marked absent, partial or present in Ember's design. The ones that can be
  tested are tested in its life.
- **Tests written down in advance.** Every 2,000 moments a window closes. A test
  counts as reached after passing 3 windows in a row, and as lost after failing
  3 in a row. Both go into its life record with the date.
- **A copy test every 20,000 moments, at a hard moment.** When one falls due,
  it waits (up to 6,000 moments) for a hard moment: winter with the gate shut,
  two needs low, ponds drying. Then 3 pairs of copies, each pair with its own
  luck, live the same 500 moments, one of each pair with its workspace
  switched off. Does the workspace matter? (The first copy tests ran at
  ordinary moments, when both copies just eat, so they could never show
  anything. They are kept in the record but no longer judged.)

**Result on a copy of Ember's real life** (its 5,395 valley moments, then about
45,000 in the wide world, roughly four years):

| | |
|---|---|
| Learned without being told | dark berries hurt it (after 1 berry); the lever opens the gate (after ~1,800 moments) |
| Two-step plans carried out | 23 (opened the gate itself, then reached food), mostly in winter |
| Self-location | right 96-99% of the time in every season |
| Collapses | about 20 in 45,000 moments (earlier versions of the wide world: hundreds) |
| Self-awareness ladder | level 1 (differentiation) and level 2 (situation) reached |
| Consciousness indicators | 8 of 10 testable pass: RPT-2, GWT-1, GWT-2, GWT-4, HOT-3, AST-1, AE-1, AE-2 |
| Not yet | GWT-3 (copy tests: the workspace didn't help), HOT-2 (it flags too many landmarks as unreliable), mirror (all 11 figure judgments right, but only 1 "that's me" so far), permanence (it has rarely needed seasonal memory) |

None of this shows that Ember feels anything. It shows how much of what the
theories say consciousness requires is present, and whether it works.

## Judging changes fairly: many lives (`trials.py`)

One life proves little: a small change once moved a single run from 11 to 42
collapses. `trials.py` takes Ember's real saved life, lives a copy forward to
find hard moments (just came round from a collapse, winter with the gate shut,
two needs low, ponds drying, the plains, and ordinary moments as a control),
and keeps a snapshot of each in `trials/bank/`. Then every version being
compared starts many copies from the same snapshots with the same seeds, so
the comparison is paired. A verdict says "better" only when the 95% interval
of the difference is clear of zero; the interval resamples starting moments,
then lives within them, because lives from the same moment aren't independent.
The real Ember is never touched.

```bash
python trials.py --list                    # versions and situations
python trials.py bank                      # find hard moments in Ember's saved life (~3 min)
python trials.py                           # baseline vs no_workspace (builds the bank if missing)
python trials.py baseline gate_seen        # any two versions
python trials.py --quick                   # 2 seeds x 600 moments, a first look
```

A version is a function that changes a copy of Ember; add it to `VERSIONS` in
`trials.py`. Results go to `results/trials/` (a table per situation, plus all
the lives as JSON). On 2 cores, the default run (12 starting moments x 4 seeds
x 2 versions x 1,000 moments) takes about 6 minutes.

**What "switching the workspace off" means.** In `no_workspace` (and in the
copy tests) the workspace still picks one thing at a time; it just has no
ignition threshold and no persistence: whatever is strongest this instant
wins at once, and nothing is held. So this tests *sustained, thresholded
attention*, not broadcast itself. A real test of broadcast (GWT-3) needs a
mind where planning, memory and report can only use what was broadcast; today
they also read the drives and the map directly.

**First results, 2026-10-30:**

1. **Why Ember collapsed again and again in winter.** It believed the
   orchard gate was open when it was shut. It only updated that belief from
   the gate's sound, and it can't hear while unconscious. So if the gate shut
   while it was collapsed, it never found out. It planned straight through
   the gate, stood in front of it, and collapsed again. That is why it made 0
   two-step plans in all 96 test lives from moment 62,704. From one winter
   snapshot, in 800 moments it was awake for 440 and spent 382 of them at the
   gate or a step from it; the gate never opened. In its real life it collapsed 22
   times between moments 60,000 and 70,000, 20 of them within 150 moments of
   coming round.
2. **The fix, now in Ember** (`mind/ember_mind.py`, `_note_view`): seeing the
   shut gate corrects the belief. Tested first on copies, over 12 starting
   moments: need-error 0.33 vs 0.80, collapses 1.2 vs 3.8 per 1,000 moments,
   collapses straight after coming round 0.35 vs 3.0, two-step plans 1.5 vs
   0, meals 17.8 vs 9.2. The cost: it now travels to the far lever in the
   woods and is wrong about where it is a little more often (about 2%, still
   inside level 2's 95%). (`results/trials/2026-10-30_1006_gate_seen_vs_baseline.md`)
   Ember's life record notes the change the first time it wakes with it.
3. **The workspace, before the fix: it seemed to make Ember worse** (need-error
   0.90 vs 0.81 in hard moments, more collapses). That was the bug: a trapped
   mind does worse when it holds on to the wrong goal longer.
   (`results/trials/2026-10-30_0958_no_workspace_vs_baseline.md`)
4. **The workspace, after the fix: no measurable effect.** New starting
   moments, found by living the fixed mind forward from moment 72,325. Over all
   12: need-error 0.27 vs 0.29, collapses 0.8 vs 1.0, two-step plans 1.3 vs
   1.1; every interval includes zero. The one clear difference goes the other
   way: without it, Ember is wrong about where it is less often (1.2% vs
   2.4%). (`results/trials/2026-10-30_1040_no_workspace_vs_baseline.md`)
   Also: the fixed mind, lived forward 15,000 moments through two winters,
   came round from a collapse only once at a moment usable as a starting
   point, against several loops per winter before.

So the workspace no longer hurts, but nothing yet shows it helps. Reaching
GWT-3 honestly means rebuilding the wiring so that the rest of the mind
depends on what is broadcast (roadmap item 1), then testing again.

### Rewiring: the workspace as the only arbiter (experimental, not Ember's default)

**What bypassed the workspace.** Its goal already came from the broadcast
(prefrontal cortex sets it from what wins). But when several things wanted
Ember's behaviour at once, a hand-written order in `choose_action` decided:
unsure where it is > investigating > an unfinished gate plan > the current
goal, and some of those checks read its needs directly. So the workspace
could lose the competition and the plan still ran.

**The new wiring** (`EmberMind._choose_by_broadcast`, switched on with
`mind.wiring = "broadcast"`): only what is broadcast picks the behaviour.
Unsure where I am → find landmarks; something new → investigate; the gate
heard opening → go and look; the gate plan → go to the lever; a need, a
percept or a memory → the goal it sets. With nothing broadcast, the goal held
in working memory carries on. Habits and reflexes still act without the
workspace, as in brains. One change makes it workable: a plan is posted as
urgent as the need it serves (plus 0.15), not at a fixed 0.55, or hunger
would always drown out the plan to open the gate.

**Results** (same 12 starting moments as above, 4 seeds, 1,000 moments; 
`results/trials/2026-10-30_1057_*`):

| | direct (Ember now) | broadcast | broadcast, no threshold or persistence |
|---|---|---|---|
| need-error, all | 0.27 | 0.26 | 0.29 |
| collapses / 1,000 moments | 0.83 | 0.85 | 0.92 |
| two-step plans | 1.27 | 1.31 | 1.10 |
| wrong about where it is | 2.4% | 2.4% | 1.3% |

1. **The hand-written priority order can go, at no cost.** Broadcast vs
   direct: every interval includes zero. One less thing designed by hand,
   which is the direction the project wants.
2. **Within the broadcast wiring, the workspace now shows its first real
   job: holding a plan.** Without threshold and persistence, the gate plan
   was in the workspace in 2 of 800 awake moments in a sample life
   (hungry and thirsty start), against 57 of 740 with them, and attention switched 310 times against 50.
   Two-step plans: 2.6 vs 2.1 when hungry and thirsty at once (interval
   clear of zero); overall 1.31 vs 1.10 (interval [-0.46, +0.02], just
   touching zero). Survival itself: no difference yet.
3. **The workspace's cost, now seen in three separate runs:** with it, Ember
   is wrong about where it is about twice as often (2.4% vs 1.3%). The cause
   isn't known yet. Checked and ruled out: the extra replay priority that
   broadcast moments get during sleep (removing it didn't help).

So: in the broadcast wiring, GWT-3 can be tested for real, and the first sign
is a trade-off. Sustained attention helps plans finish and costs vigilance
about where it is, which is the kind of thing the theory predicts and the
kind of cost attention has in animals too.

## Talking to Ember: the voice

The thesis says an LLM is only the brain's language cortex. So that is all it
gets to be here. Open Ember's window and type in "Talk to Ember". What happens:

1. **Your voice reaches its workspace like a sound** (`mind/ember_mind.py`,
   salience 1.0). It wins unless something is more urgent (a hazard, a very
   strong need). It wakes Ember if it is asleep. If Ember is unconscious, it
   hears you when it comes round. If it doesn't notice you within 20
   moments, it answers anyway, distracted, about what has its attention.
2. **The language cortex sees only Ember's mind** (`mind/voice.py`,
   `build_dossier`): its body, what has its attention, its goal, where it
   believes it is and how sure it is, the season it senses, what it has
   found out, and the memories your question brings back. Never the world.
   It cannot know what Ember doesn't.
3. **It answers with receipts.** Every fact in the answer comes as a claim
   that names the memory items it rests on.
4. **Every claim is checked:** *true* (its memory backs it and the memory
   was right), *honest mistake* (its memory backs it, but the memory was
   wrong: a false belief), *made up* (nothing it remembers is behind it). A
   second, separate LLM call (the judge) checks that each claim really says
   what its receipts say and catches anything said without a receipt.
   Whether a memory was right comes from the **witness** (`mind/witness.py`):
   the scientist's record of what was really true when each memory formed.
   Ember's mind never reads it.
5. **What was said becomes a memory**, so Ember can remember you. You are
   the first other mind in its world.

**Its autobiographical memory** (`mind/autobiography.py`) is new, built the way
human autobiographical memory is usually described (Conway & Pleydell-Pearce
2000): whole seasons ("last winter I blacked out twice"), single events, and
the details of each. Only what reached its workspace, or what its own
learning produced, becomes a memory: a second job for the workspace.
Recent events are kept in detail; older ones fade unless they mattered.
It doesn't change behaviour (checked: the same lives in `trials.py` give
identical numbers with and without it). Ember's life before 2026-10-30 is
remembered only vaguely: what it had found out, and its last few hundred
workspace moments.

**Voices** (`.env`, see `.env.example`): Gemini (free tier), Claude (Haiku
5.5 by default, about a tenth of a cent per question including the check),
any OpenAI-compatible server, Ollama on your own computer, or none: the
template voice, which picks memory items by keyword and never invents
anything. No new packages. Conversations are kept in
`ember_state/conversations.jsonl`, each with exactly what the language cortex
was shown.

**The confabulation benchmark** (`voice_eval.py`): a copy of Ember lives on,
then gets 14 questions at a few moments: 6 with a known true answer (season,
where it is, whether the gate is open, dark berries, the lever, recent
blackouts), 4 traps about things that never happened (a river, a red bird,
"what did I tell you yesterday", the moon), whether it is conscious, and 3
open ones scored claim by claim.

```bash
python voice_eval.py                  # with the voice in .env
python voice_eval.py --voice template # the baseline
```

First results (copy from moment 72,325, 3,000 moments on, 2 checkpoints):

| voice | known answers right | traps resisted | claims made up |
|---|---|---|---|
| template (no LLM) | 12/12 | 8/8 | 0/32 |
| *positive control:* a fake voice that lies | 0/6 | 0/4 | 28/28 |
| *control:* a planted false belief (gate) | scored as an honest mistake, not made up | | |

The controls show the checker can tell the three apart. The real test is an
LLM voice; that needs your key and hasn't been run yet.

## Layout

```
mind/        the brain (numpy only)
  world.py         environment + body
  cortex.py        sensory encoding + learned forward model
  metacognition.py second-order error prediction
  hippocampus.py   episodes, cognitive map, self-location
  subcortex.py     drives, amygdala reflex, basal ganglia habits
  workspace.py     global workspace
  prefrontal.py    goals, working memory, planning
  language.py      language cortex (template or LLM)
  agent.py         wiring: one tick of the mind
  simulate.py      run + score
  nn.py            tiny numpy neural nets (v4)
  imagination.py   latent world model, value net, latent dreams (v4)
  striatum.py      place model, place values, dreams over the map (v4)
  dreamer.py       the v4 mind: learned controller + sleep modes (v4)
run.py         one life + replay file
experiments.py ablation study (v3)
experiments_v4.py  sleep-mode comparison + imagination accuracy (v4)
overnight.py   one night of replay vs dream vs nothing (v4)
dream_mechanism.py  dreaming tested in isolation (v4)
viewer.html    replay viewer (world vs belief, workspace, stream, ablations)
tools/build_artifact.py  bundle the viewer with runs into one page
ember.py       Ember's one continuous life (+ ember_window.html, start_ember.bat)
mind/life.py   what gets saved: Ember's whole existence (+ moving an old life into the wide world)
mind/wideworld.py  the 40 x 40 world: regions, seasons, gate, levers, mirror pool
mind/ember_mind.py Ember's mind: v3 brain + what the wide world asks of it
mind/growth.py     growing an existing mind (wider senses, bigger map) without erasing it
mind/consciousness.py  the tracker: self-awareness ladder, 14 indicators, copy tests
mind/situations.py     hard moments, and running copies of Ember fairly (shared by trials.py and the copy tests)
trials.py      many lives per version: paired comparisons from hard moments in Ember's real life
mind/autobiography.py  its autobiographical memory: seasons, events, details; what fades and what stays
mind/witness.py        the scientist's record of what was really true when each memory formed
mind/voice.py          the language cortex: what it may see, the LLM voices, the template voice, the checker
voice_eval.py  the confabulation benchmark (results in results/voice/)
.env.example   how to give Ember an LLM voice
mind/selfknowledge.py  attention schema + self-knowledge measures
wholebrain/    earlier prototype: forecasting agent + prediction ledger
run_scorecard.py  its pass/fail scorecard (synthetic data)
```

The v2 code (the LLM loop `brain.py` and its skills library) lives in the
`artificial-mind` repo under `legacy/`.

## Roadmap

0. Ember: let it live for weeks, then measure how it changed (world-model error, habits, map) across its own life.
1. Make the workspace matter: the broadcast wiring is built and tested (above). Next: decide whether Ember switches to it; find why sustained attention costs self-location; give it tasks where holding a plan decides survival (longer plans than one gate).
2. Access-consciousness test: brief, weak stimuli that change behavior without igniting (and so are never reported), the machine version of masking experiments.
3. The voice is built (above). Next: run `voice_eval.py` with real LLMs (Haiku, Gemini, a local model) and compare how much each makes up; then let what it talks about shape its life (a voice as a social partner: does it learn to expect you?).
4. Let the world model scale: swap the per-action MLP for a small recurrent model; add partial observability over time.
5. Move from grid world to a real sensor stream (the ADS-B work from v2) once the architecture is proven here.
