# no_workspace vs baseline

2026-10-30T09:59:43+01:00. Ember's saved life at moment 62,704; starting moments found by living a copy forward (bank built 2026-10-30T09:39:59+01:00). Each starting moment x 4 seeds x 1,000 moments, both versions with the same seeds (paired).

- **baseline**: Ember as it is now
- **no_workspace**: workspace without threshold or persistence: the strongest signal of each instant wins at once

Numbers: mean ± spread (sd) across lives. Diff = no_workspace − baseline, with a 95% bootstrap interval that resamples starting moments, then lives within them (lives from the same moment aren't independent). With only 1-2 starting moments in a situation the interval is honest but wide. A verdict says "better" only when the interval is clear of zero; otherwise "can't tell".

Lower is better: need-error (how far its needs are from satisfied, averaged), collapses, loop collapses (collapsed again within 150 moments of coming round), lost (wrong about where it is), unconscious (share of moments). Higher is better: two-step plans (opened the gate, then ate).

## now: the saved life itself, as it is (4 pairs from 1 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 1.435 ± 0.042 | 1.396 ± 0.023 | -0.039 | [-0.072, -0.005] | no_workspace better |
| collapses | 7.25 ± 0.43 | 7.00 ± 0.00 | -0.250 | [-0.750, +0.000] | can't tell |
| loop_collapses | 6.25 ± 0.43 | 6.00 ± 0.00 | -0.250 | [-0.750, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] |  |
| drinks | 4.50 ± 3.35 | 8.00 ± 1.22 | +3.500 | [+0.250, +6.250] |  |
| lost | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |
| unconscious | 0.421 ± 0.002 | 0.420 ± 0.000 | -0.001 | [-0.003, +0.000] | can't tell |

## came_round: just came round from a collapse (the start of a collapse loop) (8 pairs from 2 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 1.140 ± 0.314 | 1.017 ± 0.349 | -0.123 | [-0.300, -0.025] | no_workspace better |
| collapses | 5.50 ± 1.73 | 5.12 ± 1.90 | -0.375 | [-1.500, +0.250] | can't tell |
| loop_collapses | 4.50 ± 1.73 | 4.00 ± 2.00 | -0.500 | [-1.625, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 3.50 ± 3.87 | 5.12 ± 5.16 | +1.625 | [+0.000, +4.250] |  |
| drinks | 18.62 ± 15.43 | 25.88 ± 16.13 | +7.250 | [+2.500, +14.500] |  |
| lost | 0.001 ± 0.003 | 0.007 ± 0.013 | +0.006 | [-0.001, +0.021] | can't tell |
| unconscious | 0.330 ± 0.104 | 0.307 ± 0.114 | -0.022 | [-0.083, +0.015] | can't tell |

## winter_gate: winter, hungry, the orchard gate shut (8 pairs from 2 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 1.432 ± 0.069 | 1.352 ± 0.053 | -0.080 | [-0.105, -0.057] | no_workspace better |
| collapses | 7.75 ± 0.43 | 7.50 ± 0.50 | -0.250 | [-0.750, +0.000] | can't tell |
| loop_collapses | 6.75 ± 0.43 | 6.50 ± 0.50 | -0.250 | [-0.750, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 0.38 ± 0.70 | 0.62 ± 0.70 | +0.250 | [-0.250, +1.000] |  |
| drinks | 8.00 ± 6.20 | 14.75 ± 4.02 | +6.750 | [+3.872, +9.750] |  |
| lost | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |
| unconscious | 0.442 ± 0.013 | 0.430 ± 0.010 | -0.012 | [-0.020, -0.005] | no_workspace better |

## two_needs: hungry and thirsty at the same time (8 pairs from 2 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.905 ± 0.518 | 0.751 ± 0.609 | -0.154 | [-0.421, -0.002] | no_workspace better |
| collapses | 4.38 ± 2.78 | 3.62 ± 3.39 | -0.750 | [-2.250, +0.000] | can't tell |
| loop_collapses | 3.50 ± 2.60 | 3.00 ± 3.00 | -0.500 | [-1.500, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 6.50 ± 6.86 | 9.12 ± 9.25 | +2.625 | [+0.000, +7.500] |  |
| drinks | 28.75 ± 23.03 | 38.38 ± 27.80 | +9.625 | [+1.250, +23.000] |  |
| lost | 0.004 ± 0.010 | 0.002 ± 0.002 | -0.002 | [-0.012, +0.003] | can't tell |
| unconscious | 0.263 ± 0.167 | 0.217 ± 0.203 | -0.045 | [-0.135, +0.000] | can't tell |

## dry_thirsty: summer or autumn (ponds drying), thirsty (8 pairs from 2 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.140 ± 0.091 | 0.136 ± 0.079 | -0.005 | [-0.058, +0.030] | can't tell |
| collapses | 0.25 ± 0.43 | 0.12 ± 0.33 | -0.125 | [-0.500, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 21.00 ± 4.42 | 21.75 ± 2.33 | +0.750 | [-2.875, +4.250] |  |
| drinks | 71.12 ± 4.14 | 73.25 ± 3.83 | +2.125 | [-0.875, +4.875] |  |
| lost | 0.001 ± 0.001 | 0.002 ± 0.006 | +0.002 | [-0.001, +0.008] | can't tell |
| unconscious | 0.015 ± 0.026 | 0.007 ± 0.020 | -0.007 | [-0.030, +0.000] | can't tell |

## plains: out on the windy plains (pushes hard to notice) (4 pairs from 1 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.360 ± 0.175 | 0.216 ± 0.087 | -0.144 | [-0.353, +0.104] | can't tell |
| collapses | 1.25 ± 0.83 | 0.75 ± 0.43 | -0.500 | [-1.500, +0.500] | can't tell |
| loop_collapses | 0.25 ± 0.43 | 0.00 ± 0.00 | -0.250 | [-0.750, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 14.50 ± 3.28 | 17.75 ± 3.34 | +3.250 | [-3.500, +9.250] |  |
| drinks | 57.25 ± 7.05 | 62.50 ± 5.94 | +5.250 | [-5.000, +14.250] |  |
| lost | 0.021 ± 0.032 | 0.012 ± 0.012 | -0.009 | [-0.053, +0.024] | can't tell |
| unconscious | 0.075 ± 0.050 | 0.045 ± 0.026 | -0.030 | [-0.090, +0.030] | can't tell |

## ordinary: nothing pressing: all needs above 60% (8 pairs from 2 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.255 ± 0.165 | 0.190 ± 0.081 | -0.065 | [-0.165, +0.027] | can't tell |
| collapses | 0.75 ± 0.83 | 0.50 ± 0.50 | -0.250 | [-0.750, +0.375] | can't tell |
| loop_collapses | 0.12 ± 0.33 | 0.00 ± 0.00 | -0.125 | [-0.500, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 16.75 ± 3.11 | 19.62 ± 3.43 | +2.875 | [+0.500, +5.000] |  |
| drinks | 64.12 ± 5.88 | 68.12 ± 4.17 | +4.000 | [-0.125, +7.125] |  |
| lost | 0.002 ± 0.004 | 0.013 ± 0.011 | +0.010 | [+0.001, +0.021] | baseline better |
| unconscious | 0.045 ± 0.050 | 0.028 ± 0.028 | -0.017 | [-0.052, +0.022] | can't tell |

## ALL HARD (32 pairs from 8 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.904 ± 0.570 | 0.814 ± 0.569 | -0.090 | [-0.184, -0.026] | no_workspace better |
| collapses | 4.47 ± 3.19 | 4.09 ± 3.32 | -0.375 | [-0.875, -0.031] | no_workspace better |
| loop_collapses | 3.69 ± 2.90 | 3.38 ± 2.96 | -0.312 | [-0.719, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 7.84 ± 9.10 | 9.16 ± 9.56 | +1.312 | [-0.344, +3.219] |  |
| drinks | 31.62 ± 27.93 | 38.06 ± 27.36 | +6.438 | [+3.250, +10.938] |  |
| lost | 0.001 ± 0.005 | 0.003 ± 0.008 | +0.001 | [-0.003, +0.006] | can't tell |
| unconscious | 0.262 ± 0.185 | 0.241 ± 0.194 | -0.022 | [-0.053, -0.002] | no_workspace better |

## ALL (48 pairs from 12 starting moments)

| | baseline | no_workspace | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.795 ± 0.574 | 0.709 ± 0.574 | -0.086 | [-0.154, -0.034] | no_workspace better |
| collapses | 3.81 ± 3.22 | 3.46 ± 3.28 | -0.354 | [-0.708, -0.083] | no_workspace better |
| loop_collapses | 3.02 ± 2.98 | 2.75 ± 2.98 | -0.271 | [-0.562, -0.062] | no_workspace better |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 9.23 ± 8.83 | 10.85 ± 9.61 | +1.625 | [+0.250, +3.042] |  |
| drinks | 36.92 ± 28.19 | 42.60 ± 27.57 | +5.688 | [+3.146, +8.834] |  |
| lost | 0.003 ± 0.012 | 0.005 ± 0.010 | +0.002 | [-0.004, +0.007] | can't tell |
| unconscious | 0.224 ± 0.187 | 0.204 ± 0.193 | -0.020 | [-0.041, -0.004] | no_workspace better |
