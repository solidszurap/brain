# broadcast_no_workspace vs broadcast

2026-10-30T10:57:50+01:00. Ember's saved life at moment 72,325; starting moments found by living a copy forward (bank built 2026-10-30T10:33:47+01:00). Each starting moment x 4 seeds x 1,000 moments, both versions with the same seeds (paired).

- **broadcast**: experimental wiring: only what the workspace broadcasts decides which behaviour runs
- **broadcast_no_workspace**: broadcast wiring, workspace without threshold or persistence

Numbers: mean ± spread (sd) across lives. Diff = broadcast_no_workspace − broadcast, with a 95% bootstrap interval that resamples starting moments, then lives within them (lives from the same moment aren't independent). With only 1-2 starting moments in a situation the interval is honest but wide. A verdict says "better" only when the interval is clear of zero; otherwise "can't tell".

Lower is better: need-error (how far its needs are from satisfied, averaged), collapses, loop collapses (collapsed again within 150 moments of coming round), lost (wrong about where it is), unconscious (share of moments). Higher is better: two-step plans (opened the gate, then ate).

## now: the saved life itself, as it is (4 pairs from 1 starting moments)

| | broadcast | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.075 ± 0.003 | 0.175 ± 0.188 | +0.100 | [-0.019, +0.313] | can't tell |
| collapses | 0.00 ± 0.00 | 0.50 ± 0.87 | +0.500 | [+0.000, +1.500] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.25 ± 0.43 | +0.250 | [+0.000, +0.750] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 23.00 ± 2.12 | 21.50 ± 1.50 | -1.500 | [-4.000, +1.000] |  |
| drinks | 67.25 ± 2.86 | 66.25 ± 8.87 | -1.000 | [-11.250, +7.000] |  |
| lost | 0.011 ± 0.002 | 0.017 ± 0.007 | +0.006 | [-0.001, +0.012] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.030 ± 0.052 | +0.030 | [+0.000, +0.090] | can't tell |

## came_round: just came round from a collapse (the start of a collapse loop) (4 pairs from 1 starting moments)

| | broadcast | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.489 ± 0.296 | 0.441 ± 0.271 | -0.048 | [-0.459, +0.405] | can't tell |
| collapses | 2.00 ± 1.87 | 1.50 ± 2.06 | -0.500 | [-3.750, +2.750] | can't tell |
| loop_collapses | 1.00 ± 1.73 | 1.00 ± 1.73 | +0.000 | [-3.000, +3.000] | can't tell |
| two_step | 3.00 ± 0.71 | 2.50 ± 0.50 | -0.500 | [-1.500, +0.500] | can't tell |
| meals | 13.75 ± 4.71 | 13.00 ± 4.30 | -0.750 | [-6.000, +5.000] |  |
| drinks | 55.25 ± 16.11 | 62.00 ± 15.05 | +6.750 | [-19.000, +31.750] |  |
| lost | 0.028 ± 0.029 | 0.013 ± 0.013 | -0.016 | [-0.054, +0.015] | can't tell |
| unconscious | 0.115 ± 0.104 | 0.077 ± 0.101 | -0.038 | [-0.210, +0.125] | can't tell |

## winter_gate: winter, hungry, the orchard gate shut (8 pairs from 2 starting moments)

| | broadcast | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.410 ± 0.210 | 0.427 ± 0.222 | +0.017 | [-0.231, +0.237] | can't tell |
| collapses | 1.25 ± 1.30 | 1.00 ± 1.58 | -0.250 | [-1.750, +1.250] | can't tell |
| loop_collapses | 0.38 ± 0.99 | 0.50 ± 1.32 | +0.125 | [-1.125, +1.500] | can't tell |
| two_step | 2.12 ± 0.60 | 2.25 ± 0.66 | +0.125 | [-0.375, +0.500] | can't tell |
| meals | 15.62 ± 3.16 | 15.62 ± 3.87 | +0.000 | [-3.250, +3.625] |  |
| drinks | 62.88 ± 11.06 | 64.00 ± 12.59 | +1.125 | [-11.000, +15.000] |  |
| lost | 0.019 ± 0.011 | 0.004 ± 0.004 | -0.014 | [-0.022, -0.005] | broadcast_no_workspace better |
| unconscious | 0.075 ± 0.077 | 0.055 ± 0.081 | -0.020 | [-0.107, +0.064] | can't tell |

## two_needs: hungry and thirsty at the same time (8 pairs from 2 starting moments)

| | broadcast | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.430 ± 0.220 | 0.264 ± 0.026 | -0.165 | [-0.404, +0.033] | can't tell |
| collapses | 1.88 ± 1.05 | 0.62 ± 0.48 | -1.250 | [-2.625, -0.125] | broadcast_no_workspace better |
| loop_collapses | 0.62 ± 1.11 | 0.00 ± 0.00 | -0.625 | [-1.875, +0.000] | can't tell |
| two_step | 2.62 ± 0.48 | 2.12 ± 0.60 | -0.500 | [-0.875, -0.125] | broadcast better |
| meals | 14.62 ± 4.03 | 17.38 ± 1.32 | +2.750 | [-0.375, +6.000] |  |
| drinks | 59.38 ± 13.03 | 70.00 ± 3.24 | +10.625 | [+0.000, +25.125] |  |
| lost | 0.014 ± 0.017 | 0.010 ± 0.012 | -0.004 | [-0.026, +0.014] | can't tell |
| unconscious | 0.110 ± 0.058 | 0.037 ± 0.029 | -0.072 | [-0.151, -0.007] | broadcast_no_workspace better |

## dry_thirsty: summer or autumn (ponds drying), thirsty (8 pairs from 2 starting moments)

| | broadcast | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.075 ± 0.008 | 0.106 ± 0.124 | +0.031 | [-0.027, +0.178] | can't tell |
| collapses | 0.00 ± 0.00 | 0.25 ± 0.66 | +0.250 | [+0.000, +1.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.12 ± 0.33 | +0.125 | [+0.000, +0.500] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 22.50 ± 2.12 | 20.62 ± 2.45 | -1.875 | [-3.875, +0.875] |  |
| drinks | 75.38 ± 2.12 | 73.25 ± 6.61 | -2.125 | [-7.375, +0.875] |  |
| lost | 0.033 ± 0.021 | 0.020 ± 0.021 | -0.013 | [-0.022, -0.001] | broadcast_no_workspace better |
| unconscious | 0.000 ± 0.000 | 0.015 ± 0.040 | +0.015 | [+0.000, +0.060] | can't tell |

## plains: out on the windy plains (pushes hard to notice) (8 pairs from 2 starting moments)

| | broadcast | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.206 ± 0.138 | 0.379 ± 0.342 | +0.173 | [-0.027, +0.433] | can't tell |
| collapses | 0.50 ± 0.50 | 1.62 ± 1.80 | +1.125 | [+0.000, +2.750] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.88 ± 1.17 | +0.875 | [+0.000, +2.250] | can't tell |
| two_step | 1.00 ± 1.00 | 0.50 ± 0.50 | -0.500 | [-1.000, +0.000] | can't tell |
| meals | 19.88 ± 3.59 | 15.38 ± 6.10 | -4.500 | [-8.500, +0.000] |  |
| drinks | 63.12 ± 5.53 | 55.75 ± 15.13 | -7.375 | [-19.625, +2.125] |  |
| lost | 0.030 ± 0.015 | 0.008 ± 0.007 | -0.021 | [-0.036, -0.006] | broadcast_no_workspace better |
| unconscious | 0.030 ± 0.030 | 0.090 ± 0.095 | +0.060 | [+0.000, +0.143] | can't tell |

## ordinary: nothing pressing: all needs above 60% (8 pairs from 2 starting moments)

| | broadcast | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.168 ± 0.098 | 0.232 ± 0.187 | +0.064 | [-0.015, +0.185] | can't tell |
| collapses | 0.50 ± 0.50 | 1.00 ± 1.00 | +0.500 | [+0.000, +1.125] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.25 ± 0.66 | +0.250 | [+0.000, +1.000] | can't tell |
| two_step | 0.62 ± 0.70 | 0.50 ± 0.50 | -0.125 | [-0.500, +0.000] | can't tell |
| meals | 20.62 ± 3.35 | 18.38 ± 3.77 | -2.250 | [-4.500, +0.375] |  |
| drinks | 64.75 ± 2.90 | 62.62 ± 8.08 | -2.125 | [-7.625, +2.500] |  |
| lost | 0.030 ± 0.025 | 0.017 ± 0.013 | -0.013 | [-0.036, +0.005] | can't tell |
| unconscious | 0.017 ± 0.025 | 0.048 ± 0.051 | +0.030 | [+0.000, +0.079] | can't tell |

## ALL HARD (28 pairs from 7 starting moments)

| | broadcast | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.331 ± 0.256 | 0.291 ± 0.218 | -0.040 | [-0.180, +0.081] | can't tell |
| collapses | 1.18 ± 1.39 | 0.75 ± 1.30 | -0.429 | [-1.321, +0.429] | can't tell |
| loop_collapses | 0.43 ± 1.08 | 0.32 ± 1.04 | -0.107 | [-0.786, +0.572] | can't tell |
| two_step | 1.79 ± 1.26 | 1.61 ± 1.14 | -0.179 | [-0.500, +0.107] | can't tell |
| meals | 17.04 ± 4.92 | 17.18 ± 3.96 | +0.143 | [-2.000, +2.464] |  |
| drinks | 64.36 ± 13.27 | 68.07 ± 10.58 | +3.714 | [-3.001, +11.643] |  |
| lost | 0.023 ± 0.020 | 0.012 ± 0.015 | -0.011 | [-0.020, -0.002] | broadcast_no_workspace better |
| unconscious | 0.069 ± 0.080 | 0.042 ± 0.067 | -0.028 | [-0.078, +0.017] | can't tell |

## ALL (48 pairs from 12 starting moments)

| | broadcast | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.262 ± 0.225 | 0.286 ± 0.243 | +0.024 | [-0.084, +0.126] | can't tell |
| collapses | 0.85 ± 1.17 | 0.92 ± 1.37 | +0.062 | [-0.646, +0.750] | can't tell |
| loop_collapses | 0.25 ± 0.85 | 0.40 ± 0.99 | +0.146 | [-0.375, +0.646] | can't tell |
| two_step | 1.31 ± 1.24 | 1.10 ± 1.10 | -0.208 | [-0.458, +0.021] | can't tell |
| meals | 18.60 ± 4.75 | 17.44 ± 4.49 | -1.167 | [-3.001, +0.688] |  |
| drinks | 64.46 ± 10.53 | 64.96 ± 11.90 | +0.500 | [-4.792, +6.438] |  |
| lost | 0.024 ± 0.020 | 0.013 ± 0.014 | -0.012 | [-0.020, -0.004] | broadcast_no_workspace better |
| unconscious | 0.048 ± 0.068 | 0.050 ± 0.072 | +0.002 | [-0.037, +0.039] | can't tell |
