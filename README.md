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

Ember runs the v3 mind (the one that survives well) in the `bushes` world, at 4
moments per second by default (`--speed`). In a 20,000-moment test life it
ate 651 times, slept 79 times, noticed all 999 pushes (84 false alarms) and
never collapsed.

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
mind/life.py   what gets saved: Ember's whole existence
mind/selfknowledge.py  attention schema + self-knowledge measures
wholebrain/    earlier prototype: forecasting agent + prediction ledger
run_scorecard.py  its pass/fail scorecard (synthetic data)
```

The v2 code (the LLM loop `brain.py` and its skills library) lives in the
`artificial-mind` repo under `legacy/`.

## Roadmap

0. Ember: let it live for weeks, then measure how it changed (world-model error, habits, map) across its own life.
1. Make the workspace matter: tasks requiring sustained multi-step goals; measure again.
2. Access-consciousness test: brief, weak stimuli that change behavior without igniting (and so are never reported), the machine version of masking experiments.
3. Replace the template language cortex with an LLM that answers questions about its own past from episodic memory, and score its reports against the ground-truth log (does it confabulate?).
4. Let the world model scale: swap the per-action MLP for a small recurrent model; add partial observability over time.
5. Move from grid world to a real sensor stream (the ADS-B work from v2) once the architecture is proven here.
