# no_workspace vs baseline

2026-10-30T10:40:27+01:00. Ember's saved life at moment 72,325; starting moments found by living a copy forward (bank built 2026-10-30T10:33:47+01:00). Each starting moment x 4 seeds x 1,000 moments, both versions with the same seeds (paired).

- **baseline**: Ember as it is now
- **no_workspace**: workspace without threshold or persistence: the strongest signal of each instant wins at once

Numbers: mean ± spread (sd) across lives. Diff = no_workspace − baseline, with a 95% bootstrap interval that resamples starting moments, then lives within them (lives from the same moment aren't independent). With only 1-2 starting moments in a situation the interval is honest but wide. A verdict says "better" only when the interval is clear of zero; otherwise "can't tell".

Lower is better: need-error (how far its needs are from satisfied, averaged), collapses, loop collapses (collapsed again within 150 moments of coming round), lost (wrong about where it is), unconscious (share of moments). Higher is better: two-step plans (opened the gate, then ate).

## now: the saved life itself, as it is (4 pairs from 1 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.075 ± 0.003 | 0.175 ± 0.188 | +0.100 | [-0.019, +0.313] | can't tell |
| collapses | 0.00 ± 0.00 | 0.50 ± 0.87 | +0.500 | [+0.000, +1.500] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.25 ± 0.43 | +0.250 | [+0.000, +0.750] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 23.00 ± 2.12 | 21.50 ± 1.50 | -1.500 | [-4.000, +1.000] |  |
| drinks | 67.25 ± 2.86 | 66.25 ± 8.87 | -1.000 | [-13.000, +7.000] |  |
| lost | 0.011 ± 0.002 | 0.017 ± 0.007 | +0.006 | [-0.001, +0.012] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.030 ± 0.052 | +0.030 | [+0.000, +0.090] | can't tell |

## came_round: just came round from a collapse (the start of a collapse loop) (4 pairs from 1 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.404 ± 0.175 | 0.424 ± 0.278 | +0.020 | [-0.343, +0.433] | can't tell |
| collapses | 1.50 ± 1.12 | 1.50 ± 2.06 | +0.000 | [-2.250, +2.750] | can't tell |
| loop_collapses | 0.50 ± 0.87 | 1.00 ± 1.73 | +0.500 | [-1.500, +3.000] | can't tell |
| two_step | 2.75 ± 0.43 | 2.25 ± 0.43 | -0.500 | [-1.000, +0.500] | can't tell |
| meals | 13.00 ± 2.74 | 12.75 ± 4.15 | -0.250 | [-5.500, +4.750] |  |
| drinks | 61.75 ± 11.63 | 61.00 ± 14.23 | -0.750 | [-23.500, +20.750] |  |
| lost | 0.025 ± 0.022 | 0.012 ± 0.013 | -0.013 | [-0.041, +0.011] | can't tell |
| unconscious | 0.090 ± 0.067 | 0.077 ± 0.101 | -0.013 | [-0.135, +0.125] | can't tell |

## winter_gate: winter, hungry, the orchard gate shut (8 pairs from 2 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.382 ± 0.221 | 0.431 ± 0.222 | +0.049 | [-0.258, +0.267] | can't tell |
| collapses | 1.00 ± 1.32 | 1.00 ± 1.58 | +0.000 | [-1.500, +1.500] | can't tell |
| loop_collapses | 0.38 ± 0.99 | 0.50 ± 1.32 | +0.125 | [-1.125, +1.500] | can't tell |
| two_step | 2.12 ± 0.60 | 2.12 ± 0.60 | +0.000 | [-0.750, +0.500] | can't tell |
| meals | 15.38 ± 3.31 | 15.50 ± 3.87 | +0.125 | [-3.625, +3.375] |  |
| drinks | 64.62 ± 11.16 | 64.25 ± 12.70 | -0.375 | [-12.500, +13.625] |  |
| lost | 0.012 ± 0.008 | 0.005 ± 0.004 | -0.007 | [-0.017, +0.002] | can't tell |
| unconscious | 0.060 ± 0.079 | 0.055 ± 0.081 | -0.005 | [-0.094, +0.074] | can't tell |

## two_needs: hungry and thirsty at the same time (8 pairs from 2 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.471 ± 0.249 | 0.283 ± 0.053 | -0.187 | [-0.450, +0.009] | can't tell |
| collapses | 2.12 ± 1.45 | 0.88 ± 0.33 | -1.250 | [-3.125, -0.250] | no_workspace better |
| loop_collapses | 1.00 ± 1.41 | 0.00 ± 0.00 | -1.000 | [-2.750, +0.000] | can't tell |
| two_step | 2.50 ± 0.71 | 2.12 ± 0.60 | -0.375 | [-1.375, +0.625] | can't tell |
| meals | 14.25 ± 4.87 | 17.12 ± 1.54 | +2.875 | [-0.500, +7.125] |  |
| drinks | 56.38 ± 14.25 | 68.75 ± 3.15 | +12.375 | [+2.000, +26.500] |  |
| lost | 0.017 ± 0.015 | 0.010 ± 0.010 | -0.007 | [-0.028, +0.012] | can't tell |
| unconscious | 0.120 ± 0.080 | 0.046 ± 0.025 | -0.074 | [-0.169, -0.015] | no_workspace better |

## dry_thirsty: summer or autumn (ponds drying), thirsty (8 pairs from 2 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.075 ± 0.008 | 0.106 ± 0.124 | +0.031 | [-0.027, +0.179] | can't tell |
| collapses | 0.00 ± 0.00 | 0.25 ± 0.66 | +0.250 | [+0.000, +1.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.12 ± 0.33 | +0.125 | [+0.000, +0.500] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 22.50 ± 2.12 | 20.62 ± 2.45 | -1.875 | [-3.875, +0.875] |  |
| drinks | 75.38 ± 2.12 | 73.25 ± 6.61 | -2.125 | [-7.003, +0.875] |  |
| lost | 0.033 ± 0.021 | 0.020 ± 0.021 | -0.013 | [-0.022, -0.001] | no_workspace better |
| unconscious | 0.000 ± 0.000 | 0.015 ± 0.040 | +0.015 | [+0.000, +0.060] | can't tell |

## plains: out on the windy plains (pushes hard to notice) (8 pairs from 2 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.238 ± 0.174 | 0.379 ± 0.342 | +0.141 | [-0.027, +0.386] | can't tell |
| collapses | 0.62 ± 0.70 | 1.62 ± 1.80 | +1.000 | [+0.000, +2.625] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.88 ± 1.17 | +0.875 | [+0.000, +2.250] | can't tell |
| two_step | 1.00 ± 1.00 | 0.50 ± 0.50 | -0.500 | [-1.000, +0.000] | can't tell |
| meals | 18.75 ± 4.66 | 15.38 ± 6.10 | -3.375 | [-6.625, +0.000] |  |
| drinks | 63.88 ± 5.06 | 55.75 ± 15.13 | -8.125 | [-21.253, +2.125] |  |
| lost | 0.034 ± 0.027 | 0.008 ± 0.007 | -0.026 | [-0.053, -0.006] | no_workspace better |
| unconscious | 0.037 ± 0.042 | 0.090 ± 0.095 | +0.053 | [+0.000, +0.129] | can't tell |

## ordinary: nothing pressing: all needs above 60% (8 pairs from 2 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
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

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.323 ± 0.249 | 0.295 ± 0.220 | -0.028 | [-0.176, +0.105] | can't tell |
| collapses | 1.11 ± 1.40 | 0.82 ± 1.28 | -0.286 | [-1.143, +0.500] | can't tell |
| loop_collapses | 0.46 ± 1.05 | 0.32 ± 1.04 | -0.143 | [-0.929, +0.607] | can't tell |
| two_step | 1.71 ± 1.22 | 1.54 ± 1.09 | -0.179 | [-0.607, +0.179] | can't tell |
| meals | 16.75 ± 5.10 | 17.04 ± 4.01 | +0.286 | [-1.893, +2.607] |  |
| drinks | 64.93 ± 12.95 | 67.64 ± 10.45 | +2.714 | [-4.393, +11.000] |  |
| lost | 0.021 ± 0.019 | 0.012 ± 0.015 | -0.010 | [-0.018, -0.001] | no_workspace better |
| unconscious | 0.064 ± 0.080 | 0.044 ± 0.066 | -0.020 | [-0.070, +0.024] | can't tell |

## ALL (48 pairs from 12 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.266 ± 0.225 | 0.289 ± 0.244 | +0.022 | [-0.084, +0.120] | can't tell |
| collapses | 0.83 ± 1.20 | 0.96 ± 1.35 | +0.125 | [-0.562, +0.750] | can't tell |
| loop_collapses | 0.29 ± 0.84 | 0.40 ± 0.99 | +0.104 | [-0.479, +0.667] | can't tell |
| two_step | 1.27 ± 1.20 | 1.06 ± 1.05 | -0.208 | [-0.479, +0.062] | can't tell |
| meals | 18.15 ± 5.05 | 17.35 ± 4.53 | -0.792 | [-2.417, +0.938] |  |
| drinks | 64.77 ± 10.41 | 64.71 ± 11.77 | -0.062 | [-5.646, +5.813] |  |
| lost | 0.024 ± 0.022 | 0.012 ± 0.013 | -0.011 | [-0.021, -0.003] | no_workspace better |
| unconscious | 0.049 ± 0.069 | 0.051 ± 0.071 | +0.002 | [-0.033, +0.036] | can't tell |
