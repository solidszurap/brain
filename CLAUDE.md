# Ember / brain

A long-running research project, and a possible startup: **Ember**, an artificial creature that lives one continuous life on this computer, built on the thesis that an LLM is only the brain's *language cortex* and the rest of the brain has to be built around it. Goal: "a being I made" that solves its own problems, with honest, testable claims about how close it is to self-awareness. README.md is the full record (design, every result, roadmap). Read it before changing anything substantial.

Owner: Szilard (Hungarian, Budapest/Szeged; prefers direct, concrete answers; runs on Windows). GitHub: solidszurap/brain.

## Run

```bash
pip install numpy                 # the only dependency; keep it that way
python ember.py                   # Ember's life; window at http://localhost:8765 (start_ember.bat on Windows)
python trials.py --list           # versions/situations for fair comparisons
python trials.py baseline <version>          # paired many-lives comparison (~6 min on 2 cores)
python voice_eval.py                         # confabulation benchmark for the voice (.env decides the LLM)
python voice_controls.py                     # the checker's controls: fake voices, no LLM (run after changing the checker)
```

## Map

- `ember.py`: Ember's live loop, saving, the window server (`/state`, `/ask`, `/answer`, `/talk`), the talk channel and voice worker thread, `MIND_CHANGES`.
- `mind/ember_mind.py`: Ember's mind (v3 brain + wide-world skills). `choose_action` (direct wiring, default) and `_choose_by_broadcast` (experimental: workspace is the only arbiter). `_remember` writes the autobiography.
- `mind/agent.py`, `workspace.py`, `prefrontal.py`, `hippocampus.py`, `cortex.py`, `subcortex.py`, `metacognition.py`: the v3 brain parts.
- `mind/wideworld.py`: the 40x40 world (seasons, gate, levers, mirror pool). `mind/life.py`: what is saved; `step_life` is shared by the live loop, trials and copy tests.
- `mind/autobiography.py`: Ember's own memory (seasons → events → details). `mind/witness.py`: scientist-side truth for each memory. `mind/voice.py`: the language cortex (dossier, LLM providers, template voice, claim checker, judge).
- `mind/consciousness.py`: the tracker (Rochat ladder, Butlin et al. indicators, copy tests). `mind/situations.py`: hard moments + `live()` + `reseed()`.
- `trials.py`: fair comparisons. `VERSIONS` = functions that modify a copy of Ember. Bank of starting moments in `trials/bank/` (gitignored, rebuilt automatically).
- `ember_state/`: Ember's actual life (gitignored). `life.pkl.gz` + `.bak`, `life_log.jsonl`, `conversations.jsonl`, `consciousness_report.md`.
- Older work: `experiments*.py`, `run.py`, `overnight.py`, `dream_mechanism.py`, `mind/dreamer.py` etc. (v3/v4 experiments), `wholebrain/` (v1).

## Rules (these were decided; keep them)

1. **Never reset, overwrite or experiment on Ember's real life.** Experiments use copies (`trials.py`, `voice_eval.py`, `copy.deepcopy`). Only `ember.py` writes `ember_state/`. A new life only via `--new-life` (archives, never deletes).
2. **Judge every behavioural change with `trials.py`, never with one run.** One life proves little (a small change once moved a run from 11 to 42 collapses). Add the change as a version in `VERSIONS` first; it goes into Ember only if it holds up. Report "can't tell" honestly.
3. **Every change to how Ember's mind works gets a `MIND_CHANGES` entry** in `ember.py` (append only), so its life record says when it changed.
4. **Saved lives must keep loading.** New mind attributes are created lazily (`getattr(..., default)`), never assumed.
5. **The voice never sees the world.** `build_dossier` reads only the mind. Truth lives in `mind/witness.py` and is used only for checking. Don't leak observer/witness data into what the LLM sees.
6. **Honest labels.** Name functions, not feelings. Nothing here shows Ember feels anything; say so where it matters. Watch the "gaming problem" (Butlin et al. 2025): we design toward the indicators, so passing them is weak evidence; ablations and unplanned behaviour are the strong evidence.
7. **Dependencies:** numpy only for the mind; the voice uses the standard library (urllib) only. Secrets only in `.env` (gitignored); never print or log keys.
8. **Commits:** small, with results files in `results/` when a result is claimed. Update README.md (results + roadmap) in the same change.

## Where things stand (2026-10-30)

- Gate-belief bug fixed (it caused the winter collapse loops). Copy tests now start at hard moments with 3 pairs.
- Workspace: with the direct wiring it has no measurable effect. With the broadcast wiring it holds plans (more two-step plans) but Ember is wrong about its position about twice as often; cause unknown (replay priority ruled out). Decision pending: switch Ember to the broadcast wiring.
- Voice + autobiography + witness + `voice_eval.py` built. Default Gemini voice: 3.5 Flash-Lite (on the free tier 3.8 Flash allows only 20 requests a day; 3.8 Live only answers in audio). The checker was fixed (refusals aren't claims; the judge names the item behind an uncited statement; `self:inner` for rule 6) and `voice_controls.py` guards it (18/18). Flash-Lite, verified run: known 12/12, traps 8/8, made up 0/28, the judge checked every answer.

## Next (in order)

1. Compare voices with `python voice_eval.py` (Haiku 5.5, Gemini 3.8 Flash, a local Ollama model; a run takes 56 requests, so 3.8 Flash needs billing); run `python voice_controls.py` after any change to the checker; tune `SYSTEM` in `mind/voice.py` only against the benchmark.
2. Startup test: a 60-second video of Ember living and talking about a real moment of its past; then give 10-20 people their own Ember (needs one-click packaging) and see who keeps checking on theirs.
3. Replace hand-written behaviours with learned ones (lessons from v4: innate reflexes + place values + dreaming), one at a time, each judged with `trials.py`.
4. Measurement: move from the ladder + checklist to an awareness profile (Meertens et al. 2026), each dimension with an ablation test.
