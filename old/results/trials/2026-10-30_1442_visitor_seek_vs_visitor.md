# visitor_seek vs visitor

2026-10-30T14:42:10+01:00. Ember's saved life at moment 114,871; starting moments found by living a copy forward (bank built 2026-10-30T13:47:31+01:00). Each starting moment x 4 seeds x 1,000 moments, both versions with the same seeds (paired).

- **visitor**: a simulated you visits as a light and leaves food; Ember knows the light often holds food
- **visitor_seek**: as visitor, and when hungry Ember treats the light as a place to eat

Numbers: mean ± spread (sd) across lives. Diff = visitor_seek − visitor, with a 95% bootstrap interval that resamples starting moments, then lives within them (lives from the same moment aren't independent). With only 1-2 starting moments in a situation the interval is honest but wide. A verdict says "better" only when the interval is clear of zero; otherwise "can't tell".

Lower is better: need-error (how far its needs are from satisfied, averaged), collapses, loop collapses (collapsed again within 150 moments of coming round), lost (wrong about where it is), unconscious (share of moments). Higher is better: two-step plans (opened the gate, then ate); with a visitor, gifts (food you left in the light, eaten) and reached (share of visits it stepped into the light).

## now: the saved life itself, as it is (4 pairs from 1 starting moments)

| | visitor | visitor_seek | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.081 ± 0.007 | 0.085 ± 0.008 | +0.003 | [-0.001, +0.008] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.25 ± 0.43 | 0.25 ± 0.43 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 22.25 ± 1.09 | 23.00 ± 1.87 | +0.750 | [-0.500, +2.000] |  |
| drinks | 67.75 ± 2.05 | 67.50 ± 1.12 | -0.250 | [-1.500, +0.750] |  |
| lost | 0.011 ± 0.004 | 0.011 ± 0.009 | +0.000 | [-0.005, +0.005] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |
| gifts | 2.00 ± 0.71 | 2.25 ± 0.83 | +0.250 | [+0.000, +0.750] | can't tell |
| reached | 0.312 ± 0.207 | 0.500 ± 0.306 | +0.188 | [+0.000, +0.375] | can't tell |

## came_round: just came round from a collapse (the start of a collapse loop) (8 pairs from 2 starting moments)

| | visitor | visitor_seek | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.862 ± 0.135 | 0.805 ± 0.136 | -0.056 | [-0.182, +0.062] | can't tell |
| collapses | 3.88 ± 0.60 | 3.75 ± 0.66 | -0.125 | [-0.750, +0.375] | can't tell |
| loop_collapses | 2.38 ± 0.86 | 2.25 ± 0.83 | -0.125 | [-1.000, +0.625] | can't tell |
| two_step | 1.00 ± 0.71 | 0.88 ± 0.78 | -0.125 | [-0.500, +0.000] | can't tell |
| meals | 9.12 ± 1.90 | 9.25 ± 1.48 | +0.125 | [-1.125, +1.500] |  |
| drinks | 37.88 ± 7.22 | 38.38 ± 7.58 | +0.500 | [-7.750, +7.875] |  |
| lost | 0.016 ± 0.025 | 0.012 ± 0.012 | -0.004 | [-0.028, +0.016] | can't tell |
| unconscious | 0.232 ± 0.036 | 0.225 ± 0.040 | -0.007 | [-0.037, +0.022] | can't tell |
| gifts | 2.75 ± 0.43 | 3.00 ± 0.71 | +0.250 | [-0.375, +0.750] | can't tell |
| reached | 0.260 ± 0.234 | 0.729 ± 0.180 | +0.469 | [+0.229, +0.688] | visitor_seek better |

## winter_gate: winter, hungry, the orchard gate shut (8 pairs from 2 starting moments)

| | visitor | visitor_seek | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.821 ± 0.311 | 0.671 ± 0.240 | -0.150 | [-0.329, -0.038] | visitor_seek better |
| collapses | 3.75 ± 1.79 | 3.25 ± 1.30 | -0.500 | [-1.500, +0.000] | can't tell |
| loop_collapses | 2.62 ± 1.73 | 1.12 ± 1.05 | -1.500 | [-2.875, -0.500] | visitor_seek better |
| two_step | 1.25 ± 0.43 | 1.38 ± 0.48 | +0.125 | [-0.625, +0.750] | can't tell |
| meals | 10.62 ± 5.02 | 12.25 ± 5.09 | +1.625 | [-0.253, +3.500] |  |
| drinks | 38.62 ± 15.02 | 44.62 ± 9.99 | +6.000 | [-0.500, +16.250] |  |
| lost | 0.020 ± 0.021 | 0.029 ± 0.033 | +0.009 | [-0.012, +0.029] | can't tell |
| unconscious | 0.225 ± 0.107 | 0.195 ± 0.078 | -0.030 | [-0.090, +0.000] | can't tell |
| gifts | 2.00 ± 0.50 | 2.62 ± 0.48 | +0.625 | [+0.000, +1.500] | can't tell |
| reached | 0.146 ± 0.194 | 0.781 ± 0.181 | +0.635 | [+0.385, +0.896] | visitor_seek better |

## two_needs: hungry and thirsty at the same time (8 pairs from 2 starting moments)

| | visitor | visitor_seek | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.889 ± 0.097 | 0.736 ± 0.167 | -0.153 | [-0.338, -0.006] | visitor_seek better |
| collapses | 4.00 ± 0.71 | 3.25 ± 0.97 | -0.750 | [-1.875, +0.250] | can't tell |
| loop_collapses | 2.50 ± 1.00 | 1.75 ± 0.97 | -0.750 | [-1.750, +0.250] | can't tell |
| two_step | 1.88 ± 0.60 | 2.00 ± 0.50 | +0.125 | [-0.250, +0.625] | can't tell |
| meals | 8.12 ± 1.90 | 10.50 ± 2.24 | +2.375 | [+0.125, +5.125] |  |
| drinks | 38.25 ± 7.19 | 47.75 ± 10.92 | +9.500 | [-0.125, +19.500] |  |
| lost | 0.015 ± 0.012 | 0.016 ± 0.026 | +0.002 | [-0.015, +0.031] | can't tell |
| unconscious | 0.240 ± 0.042 | 0.195 ± 0.058 | -0.045 | [-0.112, +0.015] | can't tell |
| gifts | 2.38 ± 0.70 | 2.88 ± 0.60 | +0.500 | [-0.125, +1.250] | can't tell |
| reached | 0.250 ± 0.264 | 0.802 ± 0.212 | +0.552 | [+0.333, +0.740] | visitor_seek better |

## dry_thirsty: summer or autumn (ponds drying), thirsty (4 pairs from 1 starting moments)

| | visitor | visitor_seek | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.072 ± 0.005 | 0.074 ± 0.009 | +0.002 | [-0.006, +0.012] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 25.25 ± 1.64 | 24.25 ± 2.17 | -1.000 | [-3.000, +0.500] |  |
| drinks | 75.00 ± 2.45 | 74.25 ± 0.83 | -0.750 | [-3.000, +0.750] |  |
| lost | 0.028 ± 0.004 | 0.033 ± 0.009 | +0.005 | [-0.001, +0.012] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |
| gifts | 2.25 ± 0.83 | 3.00 ± 0.71 | +0.750 | [+0.250, +1.000] | visitor_seek better |
| reached | 0.396 ± 0.108 | 0.729 ± 0.180 | +0.333 | [+0.125, +0.500] | visitor_seek better |

## plains: out on the windy plains (pushes hard to notice) (8 pairs from 2 starting moments)

| | visitor | visitor_seek | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.077 ± 0.007 | 0.080 ± 0.007 | +0.003 | [-0.001, +0.009] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.12 ± 0.33 | +0.125 | [+0.000, +0.500] | can't tell |
| meals | 22.38 ± 1.73 | 21.88 ± 2.42 | -0.500 | [-2.750, +2.000] |  |
| drinks | 68.50 ± 1.41 | 68.75 ± 1.48 | +0.250 | [-0.750, +1.625] |  |
| lost | 0.017 ± 0.011 | 0.015 ± 0.026 | -0.002 | [-0.026, +0.033] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |
| gifts | 2.38 ± 0.99 | 3.12 ± 0.78 | +0.750 | [+0.250, +1.375] | visitor_seek better |
| reached | 0.406 ± 0.147 | 0.688 ± 0.272 | +0.281 | [+0.094, +0.448] | visitor_seek better |

## ordinary: nothing pressing: all needs above 60% (8 pairs from 2 starting moments)

| | visitor | visitor_seek | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.074 ± 0.006 | 0.075 ± 0.007 | +0.000 | [-0.007, +0.006] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 22.50 ± 2.12 | 22.38 ± 1.32 | -0.125 | [-1.000, +0.625] |  |
| drinks | 70.50 ± 2.69 | 70.12 ± 1.96 | -0.375 | [-1.750, +1.375] |  |
| lost | 0.029 ± 0.032 | 0.030 ± 0.026 | +0.001 | [-0.011, +0.013] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |
| gifts | 1.75 ± 0.97 | 2.38 ± 0.86 | +0.625 | [+0.000, +1.875] | can't tell |
| reached | 0.271 ± 0.219 | 0.542 ± 0.220 | +0.271 | [+0.000, +0.615] | can't tell |

## ALL HARD (28 pairs from 7 starting moments)

| | visitor | visitor_seek | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.745 ± 0.334 | 0.642 ± 0.294 | -0.103 | [-0.195, -0.023] | visitor_seek better |
| collapses | 3.32 ± 1.73 | 2.93 ± 1.53 | -0.393 | [-0.929, +0.036] | can't tell |
| loop_collapses | 2.14 ± 1.46 | 1.46 ± 1.15 | -0.679 | [-1.429, -0.071] | visitor_seek better |
| two_step | 1.18 ± 0.80 | 1.21 ± 0.86 | +0.036 | [-0.214, +0.286] | can't tell |
| meals | 11.57 ± 6.46 | 12.61 ± 5.83 | +1.036 | [-0.286, +2.500] |  |
| drinks | 43.50 ± 16.14 | 47.96 ± 14.40 | +4.464 | [-0.464, +10.000] |  |
| lost | 0.019 ± 0.019 | 0.021 ± 0.025 | +0.003 | [-0.009, +0.014] | can't tell |
| unconscious | 0.199 ± 0.104 | 0.176 ± 0.092 | -0.024 | [-0.056, +0.002] | can't tell |
| gifts | 2.36 ± 0.67 | 2.86 ± 0.64 | +0.500 | [+0.107, +0.893] | visitor_seek better |
| reached | 0.244 ± 0.232 | 0.765 ± 0.193 | +0.521 | [+0.387, +0.664] | visitor_seek better |

## ALL (48 pairs from 12 starting moments)

| | visitor | visitor_seek | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.467 ± 0.417 | 0.408 ± 0.357 | -0.059 | [-0.123, -0.009] | visitor_seek better |
| collapses | 1.94 ± 2.11 | 1.71 ± 1.86 | -0.229 | [-0.562, +0.021] | can't tell |
| loop_collapses | 1.25 ± 1.53 | 0.85 ± 1.14 | -0.396 | [-0.896, -0.021] | visitor_seek better |
| two_step | 0.71 ± 0.84 | 0.75 ± 0.88 | +0.042 | [-0.104, +0.208] | can't tell |
| meals | 16.08 ± 7.36 | 16.65 ± 6.66 | +0.562 | [-0.375, +1.583] |  |
| drinks | 54.19 ± 17.73 | 56.75 ± 15.18 | +2.562 | [-0.396, +6.313] |  |
| lost | 0.019 ± 0.021 | 0.021 ± 0.025 | +0.001 | [-0.007, +0.010] | can't tell |
| unconscious | 0.116 ± 0.126 | 0.102 ± 0.112 | -0.014 | [-0.034, +0.001] | can't tell |
| gifts | 2.23 ± 0.82 | 2.77 ± 0.77 | +0.542 | [+0.250, +0.875] | visitor_seek better |
| reached | 0.281 ± 0.224 | 0.693 ± 0.245 | +0.411 | [+0.280, +0.540] | visitor_seek better |
