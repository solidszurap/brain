# Artificial Mind

Today's LLMs are a huge pretrained cortex with no body, no needs, no memory that outlives a conversation, and no loop that keeps running when nobody is typing. This project builds the rest of the brain around that cortex and **measures what each part is for**.

v3 is a full redesign. The LLM is no longer the brain with region names painted on its prompts. It is one peripheral (the language cortex) that can only report what reached the global workspace. Every other part is real, running, learning code.

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
run.py         one life + replay file
experiments.py ablation study
viewer.html    replay viewer (world vs belief, workspace, stream, ablations)
tools/build_artifact.py  bundle the viewer with runs into one page
legacy/        v2: brain.py LLM loop and its skills library
```

## Roadmap

1. Make the workspace matter: tasks requiring sustained multi-step goals; measure again.
2. Access-consciousness test: brief, weak stimuli that change behavior without igniting (and so are never reported), the machine version of masking experiments.
3. Replace the template language cortex with an LLM that answers questions about its own past from episodic memory, and score its reports against the ground-truth log (does it confabulate?).
4. Let the world model scale: swap the per-action MLP for a small recurrent model; add partial observability over time.
5. Move from grid world to a real sensor stream (the ADS-B work from v2) once the architecture is proven here.
