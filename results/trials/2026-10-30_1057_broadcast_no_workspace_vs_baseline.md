# broadcast_no_workspace vs baseline

2026-10-30T10:57:44+01:00. Ember's saved life at moment 72,325; starting moments found by living a copy forward (bank built 2026-10-30T10:33:47+01:00). Each starting moment x 4 seeds x 1,000 moments, both versions with the same seeds (paired).

- **baseline**: Ember as it is now
- **broadcast_no_workspace**: broadcast wiring, workspace without threshold or persistence

Numbers: mean ± spread (sd) across lives. Diff = broadcast_no_workspace − baseline, with a 95% bootstrap interval that resamples starting moments, then lives within them (lives from the same moment aren't independent). With only 1-2 starting moments in a situation the interval is honest but wide. A verdict says "better" only when the interval is clear of zero; otherwise "can't tell".

Lower is better: need-error (how far its needs are from satisfied, averaged), collapses, loop collapses (collapsed again within 150 moments of coming round), lost (wrong about where it is), unconscious (share of moments). Higher is better: two-step plans (opened the gate, then ate).

## now: the saved life itself, as it is (4 pairs from 1 starting moments)

| | baseline | broadcast_no_workspace | diff | 95% interval | verdict |
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

| | baseline | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.404 ± 0.175 | 0.441 ± 0.271 | +0.037 | [-0.325, +0.433] | can't tell |
| collapses | 1.50 ± 1.12 | 1.50 ± 2.06 | +0.000 | [-2.250, +2.750] | can't tell |
| loop_collapses | 0.50 ± 0.87 | 1.00 ± 1.73 | +0.500 | [-1.500, +3.000] | can't tell |
| two_step | 2.75 ± 0.43 | 2.50 ± 0.50 | -0.250 | [-1.000, +0.500] | can't tell |
| meals | 13.00 ± 2.74 | 13.00 ± 4.30 | +0.000 | [-5.500, +5.000] |  |
| drinks | 61.75 ± 11.63 | 62.00 ± 15.05 | +0.250 | [-23.500, +23.250] |  |
| lost | 0.025 ± 0.022 | 0.013 ± 0.013 | -0.012 | [-0.041, +0.011] | can't tell |
| unconscious | 0.090 ± 0.067 | 0.077 ± 0.101 | -0.013 | [-0.135, +0.125] | can't tell |

## winter_gate: winter, hungry, the orchard gate shut (8 pairs from 2 starting moments)

| | baseline | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.382 ± 0.221 | 0.427 ± 0.222 | +0.044 | [-0.252, +0.264] | can't tell |
| collapses | 1.00 ± 1.32 | 1.00 ± 1.58 | +0.000 | [-1.500, +1.500] | can't tell |
| loop_collapses | 0.38 ± 0.99 | 0.50 ± 1.32 | +0.125 | [-1.125, +1.500] | can't tell |
| two_step | 2.12 ± 0.60 | 2.25 ± 0.66 | +0.125 | [-0.750, +0.750] | can't tell |
| meals | 15.38 ± 3.31 | 15.62 ± 3.87 | +0.250 | [-3.625, +3.375] |  |
| drinks | 64.62 ± 11.16 | 64.00 ± 12.59 | -0.625 | [-12.503, +13.125] |  |
| lost | 0.012 ± 0.008 | 0.004 ± 0.004 | -0.007 | [-0.017, +0.002] | can't tell |
| unconscious | 0.060 ± 0.079 | 0.055 ± 0.081 | -0.005 | [-0.094, +0.074] | can't tell |

## two_needs: hungry and thirsty at the same time (8 pairs from 2 starting moments)

| | baseline | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.471 ± 0.249 | 0.264 ± 0.026 | -0.206 | [-0.490, +0.009] | can't tell |
| collapses | 2.12 ± 1.45 | 0.62 ± 0.48 | -1.500 | [-3.250, -0.250] | broadcast_no_workspace better |
| loop_collapses | 1.00 ± 1.41 | 0.00 ± 0.00 | -1.000 | [-2.750, +0.000] | can't tell |
| two_step | 2.50 ± 0.71 | 2.12 ± 0.60 | -0.375 | [-1.375, +0.500] | can't tell |
| meals | 14.25 ± 4.87 | 17.38 ± 1.32 | +3.125 | [-0.250, +7.250] |  |
| drinks | 56.38 ± 14.25 | 70.00 ± 3.24 | +13.625 | [+2.250, +29.500] |  |
| lost | 0.017 ± 0.015 | 0.010 ± 0.012 | -0.007 | [-0.028, +0.015] | can't tell |
| unconscious | 0.120 ± 0.080 | 0.037 ± 0.029 | -0.082 | [-0.185, -0.015] | broadcast_no_workspace better |

## dry_thirsty: summer or autumn (ponds drying), thirsty (8 pairs from 2 starting moments)

| | baseline | broadcast_no_workspace | diff | 95% interval | verdict |
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

| | baseline | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.238 ± 0.174 | 0.379 ± 0.342 | +0.141 | [-0.027, +0.386] | can't tell |
| collapses | 0.62 ± 0.70 | 1.62 ± 1.80 | +1.000 | [+0.000, +2.625] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.88 ± 1.17 | +0.875 | [+0.000, +2.250] | can't tell |
| two_step | 1.00 ± 1.00 | 0.50 ± 0.50 | -0.500 | [-1.000, +0.000] | can't tell |
| meals | 18.75 ± 4.66 | 15.38 ± 6.10 | -3.375 | [-6.625, +0.000] |  |
| drinks | 63.88 ± 5.06 | 55.75 ± 15.13 | -8.125 | [-21.253, +2.125] |  |
| lost | 0.034 ± 0.027 | 0.008 ± 0.007 | -0.026 | [-0.053, -0.006] | broadcast_no_workspace better |
| unconscious | 0.037 ± 0.042 | 0.090 ± 0.095 | +0.053 | [+0.000, +0.129] | can't tell |

## ordinary: nothing pressing: all needs above 60% (8 pairs from 2 starting moments)

| | baseline | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.193 ± 0.150 | 0.232 ± 0.187 | +0.039 | [-0.026, +0.149] | can't tell |
| collapses | 0.50 ± 0.71 | 1.00 ± 1.00 | +0.500 | [+0.000, +1.125] | can't tell |
| loop_collapses | 0.12 ± 0.33 | 0.25 ± 0.66 | +0.125 | [-0.375, +0.750] | can't tell |
| two_step | 0.62 ± 0.70 | 0.50 ± 0.50 | -0.125 | [-0.500, +0.000] | can't tell |
| meals | 20.00 ± 3.91 | 18.38 ± 3.77 | -1.625 | [-3.375, +0.500] |  |
| drinks | 63.88 ± 5.42 | 62.62 ± 8.08 | -1.250 | [-6.750, +2.625] |  |
| lost | 0.028 ± 0.025 | 0.017 ± 0.013 | -0.012 | [-0.036, +0.007] | can't tell |
| unconscious | 0.030 ± 0.042 | 0.048 ± 0.051 | +0.018 | [+0.000, +0.048] | can't tell |

## ALL HARD (28 pairs from 7 starting moments)

| | baseline | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.323 ± 0.249 | 0.291 ± 0.218 | -0.032 | [-0.188, +0.104] | can't tell |
| collapses | 1.11 ± 1.40 | 0.75 ± 1.30 | -0.357 | [-1.287, +0.500] | can't tell |
| loop_collapses | 0.46 ± 1.05 | 0.32 ± 1.04 | -0.143 | [-0.929, +0.607] | can't tell |
| two_step | 1.71 ± 1.22 | 1.61 ± 1.14 | -0.107 | [-0.536, +0.250] | can't tell |
| meals | 16.75 ± 5.10 | 17.18 ± 3.96 | +0.429 | [-1.821, +2.857] |  |
| drinks | 64.93 ± 12.95 | 68.07 ± 10.58 | +3.143 | [-4.215, +11.964] |  |
| lost | 0.021 ± 0.019 | 0.012 ± 0.015 | -0.009 | [-0.018, -0.001] | broadcast_no_workspace better |
| unconscious | 0.064 ± 0.080 | 0.042 ± 0.067 | -0.023 | [-0.075, +0.023] | can't tell |

## ALL (48 pairs from 12 starting moments)

| | baseline | broadcast_no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.266 ± 0.225 | 0.286 ± 0.243 | +0.020 | [-0.092, +0.120] | can't tell |
| collapses | 0.83 ± 1.20 | 0.92 ± 1.37 | +0.083 | [-0.646, +0.750] | can't tell |
| loop_collapses | 0.29 ± 0.84 | 0.40 ± 0.99 | +0.104 | [-0.479, +0.667] | can't tell |
| two_step | 1.27 ± 1.20 | 1.10 ± 1.10 | -0.167 | [-0.438, +0.104] | can't tell |
| meals | 18.15 ± 5.05 | 17.44 ± 4.49 | -0.708 | [-2.417, +1.104] |  |
| drinks | 64.77 ± 10.41 | 64.96 ± 11.90 | +0.188 | [-5.479, +6.417] |  |
| lost | 0.024 ± 0.022 | 0.013 ± 0.014 | -0.011 | [-0.021, -0.003] | broadcast_no_workspace better |
| unconscious | 0.049 ± 0.069 | 0.050 ± 0.072 | +0.001 | [-0.035, +0.036] | can't tell |
