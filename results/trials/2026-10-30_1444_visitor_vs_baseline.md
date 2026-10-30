# visitor vs baseline

2026-10-30T14:44:58+01:00. Ember's saved life at moment 114,871; starting moments found by living a copy forward (bank built 2026-10-30T13:47:31+01:00). Each starting moment x 4 seeds x 1,000 moments, both versions with the same seeds (paired).

- **baseline**: Ember as it is now
- **visitor**: a simulated you visits as a light and leaves food; Ember knows the light often holds food

Numbers: mean ± spread (sd) across lives. Diff = visitor − baseline, with a 95% bootstrap interval that resamples starting moments, then lives within them (lives from the same moment aren't independent). With only 1-2 starting moments in a situation the interval is honest but wide. A verdict says "better" only when the interval is clear of zero; otherwise "can't tell".

Lower is better: need-error (how far its needs are from satisfied, averaged), collapses, loop collapses (collapsed again within 150 moments of coming round), lost (wrong about where it is), unconscious (share of moments). Higher is better: two-step plans (opened the gate, then ate); with a visitor, gifts (food you left in the light, eaten) and reached (share of visits it stepped into the light).

## now: the saved life itself, as it is (4 pairs from 1 starting moments)

| | baseline | visitor | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.087 ± 0.006 | 0.081 ± 0.007 | -0.005 | [-0.008, -0.000] | visitor better |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.25 ± 0.43 | 0.25 ± 0.43 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 21.75 ± 1.30 | 22.25 ± 1.09 | +0.500 | [+0.000, +1.000] |  |
| drinks | 68.25 ± 1.64 | 67.75 ± 2.05 | -0.500 | [-2.500, +2.500] |  |
| lost | 0.014 ± 0.013 | 0.011 ± 0.004 | -0.002 | [-0.013, +0.004] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## came_round: just came round from a collapse (the start of a collapse loop) (8 pairs from 2 starting moments)

| | baseline | visitor | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 1.007 ± 0.147 | 0.862 ± 0.135 | -0.146 | [-0.229, -0.045] | visitor better |
| collapses | 4.50 ± 0.50 | 3.88 ± 0.60 | -0.625 | [-1.000, -0.250] | visitor better |
| loop_collapses | 3.50 ± 0.50 | 2.38 ± 0.86 | -1.125 | [-1.625, -0.625] | visitor better |
| two_step | 0.88 ± 0.60 | 1.00 ± 0.71 | +0.125 | [-0.375, +0.625] | can't tell |
| meals | 7.38 ± 0.99 | 9.12 ± 1.90 | +1.750 | [+0.250, +3.500] |  |
| drinks | 28.50 ± 5.32 | 37.88 ± 7.22 | +9.375 | [+4.875, +14.000] |  |
| lost | 0.017 ± 0.018 | 0.016 ± 0.025 | -0.000 | [-0.018, +0.017] | can't tell |
| unconscious | 0.270 ± 0.030 | 0.232 ± 0.036 | -0.037 | [-0.060, -0.015] | visitor better |

## winter_gate: winter, hungry, the orchard gate shut (8 pairs from 2 starting moments)

| | baseline | visitor | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.872 ± 0.377 | 0.821 ± 0.311 | -0.051 | [-0.164, +0.032] | can't tell |
| collapses | 4.00 ± 2.00 | 3.75 ± 1.79 | -0.250 | [-0.750, +0.000] | can't tell |
| loop_collapses | 3.00 ± 2.00 | 2.62 ± 1.73 | -0.375 | [-1.125, +0.000] | can't tell |
| two_step | 0.62 ± 0.48 | 1.25 ± 0.43 | +0.625 | [+0.250, +1.000] | visitor better |
| meals | 10.25 ± 5.76 | 10.62 ± 5.02 | +0.375 | [-1.625, +2.125] |  |
| drinks | 33.75 ± 18.77 | 38.62 ± 15.02 | +4.875 | [-0.250, +12.759] |  |
| lost | 0.017 ± 0.018 | 0.020 ± 0.021 | +0.003 | [-0.010, +0.021] | can't tell |
| unconscious | 0.240 ± 0.120 | 0.225 ± 0.107 | -0.015 | [-0.045, +0.000] | can't tell |

## two_needs: hungry and thirsty at the same time (8 pairs from 2 starting moments)

| | baseline | visitor | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 1.072 ± 0.051 | 0.889 ± 0.097 | -0.183 | [-0.238, -0.132] | visitor better |
| collapses | 5.00 ± 0.00 | 4.00 ± 0.71 | -1.000 | [-1.500, -0.500] | visitor better |
| loop_collapses | 4.00 ± 0.00 | 2.50 ± 1.00 | -1.500 | [-2.250, -0.875] | visitor better |
| two_step | 1.75 ± 0.43 | 1.88 ± 0.60 | +0.125 | [-0.375, +0.500] | can't tell |
| meals | 6.12 ± 1.17 | 8.12 ± 1.90 | +2.000 | [+0.875, +3.250] |  |
| drinks | 26.00 ± 4.58 | 38.25 ± 7.19 | +12.250 | [+8.875, +15.375] |  |
| lost | 0.021 ± 0.022 | 0.015 ± 0.012 | -0.006 | [-0.027, +0.008] | can't tell |
| unconscious | 0.300 ± 0.000 | 0.240 ± 0.042 | -0.060 | [-0.090, -0.030] | visitor better |

## dry_thirsty: summer or autumn (ponds drying), thirsty (4 pairs from 1 starting moments)

| | baseline | visitor | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.079 ± 0.008 | 0.072 ± 0.005 | -0.007 | [-0.011, -0.002] | visitor better |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 21.75 ± 1.48 | 25.25 ± 1.64 | +3.500 | [+3.000, +4.000] |  |
| drinks | 73.25 ± 2.28 | 75.00 ± 2.45 | +1.750 | [-2.500, +5.750] |  |
| lost | 0.067 ± 0.025 | 0.028 ± 0.004 | -0.039 | [-0.062, -0.014] | visitor better |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## plains: out on the windy plains (pushes hard to notice) (8 pairs from 2 starting moments)

| | baseline | visitor | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.088 ± 0.011 | 0.077 ± 0.007 | -0.011 | [-0.020, +0.000] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 22.12 ± 1.76 | 22.38 ± 1.73 | +0.250 | [-1.375, +1.500] |  |
| drinks | 69.50 ± 2.50 | 68.50 ± 1.41 | -1.000 | [-2.625, +0.500] |  |
| lost | 0.030 ± 0.035 | 0.017 ± 0.011 | -0.013 | [-0.037, +0.006] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## ordinary: nothing pressing: all needs above 60% (8 pairs from 2 starting moments)

| | baseline | visitor | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.081 ± 0.009 | 0.074 ± 0.006 | -0.007 | [-0.014, -0.001] | visitor better |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 22.75 ± 3.53 | 22.50 ± 2.12 | -0.250 | [-2.875, +2.000] |  |
| drinks | 70.38 ± 2.23 | 70.50 ± 2.69 | +0.125 | [-1.375, +1.625] |  |
| lost | 0.030 ± 0.034 | 0.029 ± 0.032 | -0.001 | [-0.033, +0.029] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## ALL HARD (28 pairs from 7 starting moments)

| | baseline | visitor | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.854 ± 0.392 | 0.745 ± 0.334 | -0.109 | [-0.172, -0.044] | visitor better |
| collapses | 3.86 ± 1.96 | 3.32 ± 1.73 | -0.536 | [-0.893, -0.214] | visitor better |
| loop_collapses | 3.00 ± 1.69 | 2.14 ± 1.46 | -0.857 | [-1.393, -0.357] | visitor better |
| two_step | 0.93 ± 0.75 | 1.18 ± 0.80 | +0.250 | [-0.036, +0.536] | can't tell |
| meals | 9.89 ± 6.04 | 11.57 ± 6.46 | +1.679 | [+0.500, +2.679] |  |
| drinks | 35.68 ± 18.97 | 43.50 ± 16.14 | +7.821 | [+3.821, +11.643] |  |
| lost | 0.025 ± 0.026 | 0.019 ± 0.019 | -0.006 | [-0.021, +0.006] | can't tell |
| unconscious | 0.231 ± 0.118 | 0.199 ± 0.104 | -0.032 | [-0.054, -0.013] | visitor better |

## ALL (48 pairs from 12 starting moments)

| | baseline | visitor | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.534 ± 0.483 | 0.467 ± 0.417 | -0.067 | [-0.119, -0.023] | visitor better |
| collapses | 2.25 ± 2.42 | 1.94 ± 2.11 | -0.312 | [-0.583, -0.083] | visitor better |
| loop_collapses | 1.75 ± 1.96 | 1.25 ± 1.53 | -0.500 | [-0.896, -0.146] | visitor better |
| two_step | 0.56 ± 0.73 | 0.71 ± 0.84 | +0.146 | [-0.021, +0.333] | can't tell |
| meals | 15.06 ± 7.84 | 16.08 ± 7.36 | +1.021 | [+0.083, +1.917] |  |
| drinks | 49.81 ± 22.18 | 54.19 ± 17.73 | +4.375 | [+1.312, +7.771] |  |
| lost | 0.026 ± 0.029 | 0.019 ± 0.021 | -0.006 | [-0.017, +0.004] | can't tell |
| unconscious | 0.135 ± 0.145 | 0.116 ± 0.126 | -0.019 | [-0.035, -0.005] | visitor better |
