# broadcast vs baseline

2026-10-30T10:57:38+01:00. Ember's saved life at moment 72,325; starting moments found by living a copy forward (bank built 2026-10-30T10:33:47+01:00). Each starting moment x 4 seeds x 1,000 moments, both versions with the same seeds (paired).

- **baseline**: Ember as it is now
- **broadcast**: experimental wiring: only what the workspace broadcasts decides which behaviour runs

Numbers: mean ± spread (sd) across lives. Diff = broadcast − baseline, with a 95% bootstrap interval that resamples starting moments, then lives within them (lives from the same moment aren't independent). With only 1-2 starting moments in a situation the interval is honest but wide. A verdict says "better" only when the interval is clear of zero; otherwise "can't tell".

Lower is better: need-error (how far its needs are from satisfied, averaged), collapses, loop collapses (collapsed again within 150 moments of coming round), lost (wrong about where it is), unconscious (share of moments). Higher is better: two-step plans (opened the gate, then ate).

## now: the saved life itself, as it is (4 pairs from 1 starting moments)

| | baseline | broadcast | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.075 ± 0.003 | 0.075 ± 0.003 | +0.000 | [+0.000, +0.000] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 23.00 ± 2.12 | 23.00 ± 2.12 | +0.000 | [+0.000, +0.000] |  |
| drinks | 67.25 ± 2.86 | 67.25 ± 2.86 | +0.000 | [+0.000, +0.000] |  |
| lost | 0.011 ± 0.002 | 0.011 ± 0.002 | +0.000 | [+0.000, +0.000] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## came_round: just came round from a collapse (the start of a collapse loop) (4 pairs from 1 starting moments)

| | baseline | broadcast | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.404 ± 0.175 | 0.489 ± 0.296 | +0.085 | [-0.342, +0.570] | can't tell |
| collapses | 1.50 ± 1.12 | 2.00 ± 1.87 | +0.500 | [-2.250, +3.750] | can't tell |
| loop_collapses | 0.50 ± 0.87 | 1.00 ± 1.73 | +0.500 | [-1.500, +3.000] | can't tell |
| two_step | 2.75 ± 0.43 | 3.00 ± 0.71 | +0.250 | [-0.500, +1.000] | can't tell |
| meals | 13.00 ± 2.74 | 13.75 ± 4.71 | +0.750 | [-6.500, +8.250] |  |
| drinks | 61.75 ± 11.63 | 55.25 ± 16.11 | -6.500 | [-34.000, +19.500] |  |
| lost | 0.025 ± 0.022 | 0.028 ± 0.029 | +0.003 | [-0.005, +0.013] | can't tell |
| unconscious | 0.090 ± 0.067 | 0.115 ± 0.104 | +0.025 | [-0.135, +0.210] | can't tell |

## winter_gate: winter, hungry, the orchard gate shut (8 pairs from 2 starting moments)

| | baseline | broadcast | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.382 ± 0.221 | 0.410 ± 0.210 | +0.027 | [-0.050, +0.156] | can't tell |
| collapses | 1.00 ± 1.32 | 1.25 ± 1.30 | +0.250 | [-0.250, +0.875] | can't tell |
| loop_collapses | 0.38 ± 0.99 | 0.38 ± 0.99 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 2.12 ± 0.60 | 2.12 ± 0.60 | +0.000 | [-0.500, +0.500] | can't tell |
| meals | 15.38 ± 3.31 | 15.62 ± 3.16 | +0.250 | [-0.750, +2.128] |  |
| drinks | 64.62 ± 11.16 | 62.88 ± 11.06 | -1.750 | [-7.000, +4.128] |  |
| lost | 0.012 ± 0.008 | 0.019 ± 0.011 | +0.007 | [-0.001, +0.018] | can't tell |
| unconscious | 0.060 ± 0.079 | 0.075 ± 0.077 | +0.015 | [-0.015, +0.052] | can't tell |

## two_needs: hungry and thirsty at the same time (8 pairs from 2 starting moments)

| | baseline | broadcast | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.471 ± 0.249 | 0.430 ± 0.220 | -0.041 | [-0.201, +0.113] | can't tell |
| collapses | 2.12 ± 1.45 | 1.88 ± 1.05 | -0.250 | [-1.125, +0.500] | can't tell |
| loop_collapses | 1.00 ± 1.41 | 0.62 ± 1.11 | -0.375 | [-1.500, +0.375] | can't tell |
| two_step | 2.50 ± 0.71 | 2.62 ± 0.48 | +0.125 | [-0.500, +1.000] | can't tell |
| meals | 14.25 ± 4.87 | 14.62 ± 4.03 | +0.375 | [-1.375, +2.375] |  |
| drinks | 56.38 ± 14.25 | 59.38 ± 13.03 | +3.000 | [-5.500, +12.000] |  |
| lost | 0.017 ± 0.015 | 0.014 ± 0.017 | -0.003 | [-0.021, +0.013] | can't tell |
| unconscious | 0.120 ± 0.080 | 0.110 ± 0.058 | -0.010 | [-0.060, +0.041] | can't tell |

## dry_thirsty: summer or autumn (ponds drying), thirsty (8 pairs from 2 starting moments)

| | baseline | broadcast | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.075 ± 0.008 | 0.075 ± 0.008 | +0.000 | [+0.000, +0.000] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 22.50 ± 2.12 | 22.50 ± 2.12 | +0.000 | [+0.000, +0.000] |  |
| drinks | 75.38 ± 2.12 | 75.38 ± 2.12 | +0.000 | [+0.000, +0.000] |  |
| lost | 0.033 ± 0.021 | 0.033 ± 0.021 | +0.000 | [+0.000, +0.000] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## plains: out on the windy plains (pushes hard to notice) (8 pairs from 2 starting moments)

| | baseline | broadcast | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.238 ± 0.174 | 0.206 ± 0.138 | -0.033 | [-0.093, +0.000] | can't tell |
| collapses | 0.62 ± 0.70 | 0.50 ± 0.50 | -0.125 | [-0.500, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 1.00 ± 1.00 | 1.00 ± 1.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 18.75 ± 4.66 | 19.88 ± 3.59 | +1.125 | [-0.125, +3.625] |  |
| drinks | 63.88 ± 5.06 | 63.12 ± 5.53 | -0.750 | [-3.250, +1.375] |  |
| lost | 0.034 ± 0.027 | 0.030 ± 0.015 | -0.005 | [-0.020, +0.005] | can't tell |
| unconscious | 0.037 ± 0.042 | 0.030 ± 0.030 | -0.007 | [-0.030, +0.000] | can't tell |

## ordinary: nothing pressing: all needs above 60% (8 pairs from 2 starting moments)

| | baseline | broadcast | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.193 ± 0.150 | 0.168 ± 0.098 | -0.024 | [-0.118, +0.021] | can't tell |
| collapses | 0.50 ± 0.71 | 0.50 ± 0.50 | +0.000 | [-0.375, +0.375] | can't tell |
| loop_collapses | 0.12 ± 0.33 | 0.00 ± 0.00 | -0.125 | [-0.500, +0.000] | can't tell |
| two_step | 0.62 ± 0.70 | 0.62 ± 0.70 | +0.000 | [-0.375, +0.375] | can't tell |
| meals | 20.00 ± 3.91 | 20.62 ± 3.35 | +0.625 | [-0.500, +2.625] |  |
| drinks | 63.88 ± 5.42 | 64.75 ± 2.90 | +0.875 | [-0.875, +4.750] |  |
| lost | 0.028 ± 0.025 | 0.030 ± 0.025 | +0.002 | [+0.000, +0.004] | can't tell |
| unconscious | 0.030 ± 0.042 | 0.017 ± 0.025 | -0.013 | [-0.055, +0.006] | can't tell |

## ALL HARD (28 pairs from 7 starting moments)

| | baseline | broadcast | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.323 ± 0.249 | 0.331 ± 0.256 | +0.008 | [-0.069, +0.104] | can't tell |
| collapses | 1.11 ± 1.40 | 1.18 ± 1.39 | +0.071 | [-0.429, +0.643] | can't tell |
| loop_collapses | 0.46 ± 1.05 | 0.43 ± 1.08 | -0.036 | [-0.571, +0.464] | can't tell |
| two_step | 1.71 ± 1.22 | 1.79 ± 1.26 | +0.071 | [-0.179, +0.357] | can't tell |
| meals | 16.75 ± 5.10 | 17.04 ± 4.92 | +0.286 | [-0.893, +1.643] |  |
| drinks | 64.93 ± 12.95 | 64.36 ± 13.27 | -0.571 | [-6.179, +4.179] |  |
| lost | 0.021 ± 0.019 | 0.023 ± 0.020 | +0.002 | [-0.005, +0.008] | can't tell |
| unconscious | 0.064 ± 0.080 | 0.069 ± 0.080 | +0.005 | [-0.022, +0.037] | can't tell |

## ALL (48 pairs from 12 starting moments)

| | baseline | broadcast | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.266 ± 0.225 | 0.262 ± 0.225 | -0.005 | [-0.053, +0.055] | can't tell |
| collapses | 0.83 ± 1.20 | 0.85 ± 1.17 | +0.021 | [-0.271, +0.375] | can't tell |
| loop_collapses | 0.29 ± 0.84 | 0.25 ± 0.85 | -0.042 | [-0.354, +0.250] | can't tell |
| two_step | 1.27 ± 1.20 | 1.31 ± 1.24 | +0.042 | [-0.104, +0.229] | can't tell |
| meals | 18.15 ± 5.05 | 18.60 ± 4.75 | +0.458 | [-0.396, +1.396] |  |
| drinks | 64.77 ± 10.41 | 64.46 ± 10.53 | -0.312 | [-3.688, +2.646] |  |
| lost | 0.024 ± 0.022 | 0.024 ± 0.020 | +0.000 | [-0.004, +0.004] | can't tell |
| unconscious | 0.049 ± 0.069 | 0.048 ± 0.068 | -0.000 | [-0.018, +0.021] | can't tell |
