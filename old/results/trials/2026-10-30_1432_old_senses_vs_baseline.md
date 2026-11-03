# old_senses vs baseline

2026-10-30T14:32:36+01:00. Ember's saved life at moment 114,871; starting moments found by living a copy forward (bank built 2026-10-30T13:47:31+01:00). Each starting moment x 4 seeds x 1,000 moments, both versions with the same seeds (paired).

- **baseline**: Ember as it is now
- **old_senses**: its eyes before the light existed: 9 kinds of things instead of 10

Numbers: mean ± spread (sd) across lives. Diff = old_senses − baseline, with a 95% bootstrap interval that resamples starting moments, then lives within them (lives from the same moment aren't independent). With only 1-2 starting moments in a situation the interval is honest but wide. A verdict says "better" only when the interval is clear of zero; otherwise "can't tell".

Lower is better: need-error (how far its needs are from satisfied, averaged), collapses, loop collapses (collapsed again within 150 moments of coming round), lost (wrong about where it is), unconscious (share of moments). Higher is better: two-step plans (opened the gate, then ate).

## now: the saved life itself, as it is (4 pairs from 1 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.083 ± 0.011 | 0.101 ± 0.026 | +0.018 | [-0.007, +0.043] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.75 ± 0.83 | +0.750 | [+0.000, +1.500] | can't tell |
| meals | 22.50 ± 1.66 | 22.25 ± 1.92 | -0.250 | [-3.250, +2.000] |  |
| drinks | 68.25 ± 1.30 | 67.50 ± 1.12 | -0.750 | [-2.500, +1.250] |  |
| lost | 0.019 ± 0.018 | 0.024 ± 0.005 | +0.005 | [-0.009, +0.016] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## came_round: just came round from a collapse (the start of a collapse loop) (8 pairs from 2 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 1.026 ± 0.131 | 1.005 ± 0.162 | -0.021 | [-0.086, +0.016] | can't tell |
| collapses | 4.50 ± 0.50 | 4.62 ± 0.48 | +0.125 | [+0.000, +0.500] | can't tell |
| loop_collapses | 3.50 ± 0.50 | 3.62 ± 0.48 | +0.125 | [+0.000, +0.500] | can't tell |
| two_step | 1.12 ± 0.78 | 0.88 ± 0.78 | -0.250 | [-0.750, +0.000] | can't tell |
| meals | 7.50 ± 1.41 | 7.38 ± 1.73 | -0.125 | [-1.500, +1.250] |  |
| drinks | 28.50 ± 5.48 | 28.75 ± 5.45 | +0.250 | [-2.625, +3.125] |  |
| lost | 0.034 ± 0.021 | 0.017 ± 0.017 | -0.016 | [-0.040, +0.001] | can't tell |
| unconscious | 0.270 ± 0.030 | 0.277 ± 0.029 | +0.007 | [+0.000, +0.030] | can't tell |

## winter_gate: winter, hungry, the orchard gate shut (8 pairs from 2 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.869 ± 0.381 | 0.864 ± 0.379 | -0.006 | [-0.021, +0.017] | can't tell |
| collapses | 4.00 ± 2.00 | 4.00 ± 2.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 3.00 ± 2.00 | 3.00 ± 2.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.62 ± 0.48 | 0.75 ± 0.43 | +0.125 | [-0.250, +0.625] | can't tell |
| meals | 10.50 ± 5.81 | 11.25 ± 6.32 | +0.750 | [-1.000, +2.500] |  |
| drinks | 33.00 ± 18.29 | 33.25 ± 18.03 | +0.250 | [-0.750, +1.125] |  |
| lost | 0.028 ± 0.018 | 0.018 ± 0.020 | -0.011 | [-0.032, +0.006] | can't tell |
| unconscious | 0.240 ± 0.120 | 0.240 ± 0.120 | +0.000 | [+0.000, +0.000] | can't tell |

## two_needs: hungry and thirsty at the same time (8 pairs from 2 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.954 ± 0.267 | 0.959 ± 0.299 | +0.005 | [-0.180, +0.232] | can't tell |
| collapses | 4.25 ± 1.39 | 4.25 ± 1.64 | +0.000 | [-1.250, +1.375] | can't tell |
| loop_collapses | 3.25 ± 1.39 | 3.38 ± 1.32 | +0.125 | [-0.875, +1.500] | can't tell |
| two_step | 2.00 ± 0.50 | 2.00 ± 0.00 | +0.000 | [-0.500, +0.500] | can't tell |
| meals | 7.62 ± 3.84 | 8.00 ± 4.09 | +0.375 | [-2.875, +2.875] |  |
| drinks | 31.75 ± 14.71 | 32.50 ± 15.91 | +0.750 | [-10.625, +11.375] |  |
| lost | 0.027 ± 0.022 | 0.021 ± 0.017 | -0.006 | [-0.012, +0.000] | can't tell |
| unconscious | 0.252 ± 0.087 | 0.255 ± 0.098 | +0.003 | [-0.065, +0.083] | can't tell |

## dry_thirsty: summer or autumn (ponds drying), thirsty (4 pairs from 1 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.075 ± 0.005 | 0.079 ± 0.007 | +0.004 | [-0.001, +0.008] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 24.00 ± 1.41 | 22.75 ± 1.09 | -1.250 | [-3.750, +0.500] |  |
| drinks | 76.50 ± 1.50 | 72.75 ± 1.92 | -3.750 | [-7.250, -1.000] |  |
| lost | 0.050 ± 0.016 | 0.050 ± 0.014 | +0.000 | [-0.020, +0.018] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## plains: out on the windy plains (pushes hard to notice) (8 pairs from 2 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.090 ± 0.009 | 0.079 ± 0.007 | -0.012 | [-0.023, +0.001] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.12 ± 0.33 | 0.00 ± 0.00 | -0.125 | [-0.500, +0.000] | can't tell |
| meals | 21.38 ± 2.06 | 21.75 ± 1.48 | +0.375 | [-1.250, +1.625] |  |
| drinks | 70.25 ± 1.56 | 69.25 ± 2.73 | -1.000 | [-3.000, +1.500] |  |
| lost | 0.020 ± 0.011 | 0.014 ± 0.010 | -0.007 | [-0.018, +0.007] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## ordinary: nothing pressing: all needs above 60% (8 pairs from 2 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.076 ± 0.009 | 0.084 ± 0.012 | +0.008 | [-0.003, +0.023] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 22.12 ± 1.96 | 21.75 ± 2.77 | -0.375 | [-1.875, +1.750] |  |
| drinks | 70.50 ± 1.66 | 69.62 ± 0.99 | -0.875 | [-2.000, +0.875] |  |
| lost | 0.016 ± 0.011 | 0.055 ± 0.078 | +0.039 | [-0.017, +0.131] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## ALL HARD (28 pairs from 7 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.825 ± 0.405 | 0.819 ± 0.410 | -0.006 | [-0.062, +0.062] | can't tell |
| collapses | 3.64 ± 2.00 | 3.68 ± 2.07 | +0.036 | [-0.357, +0.464] | can't tell |
| loop_collapses | 2.79 ± 1.76 | 2.86 ± 1.77 | +0.071 | [-0.214, +0.464] | can't tell |
| two_step | 1.07 ± 0.88 | 1.04 ± 0.82 | -0.036 | [-0.286, +0.214] | can't tell |
| meals | 10.75 ± 6.75 | 10.86 ± 6.58 | +0.107 | [-1.036, +1.250] |  |
| drinks | 37.57 ± 20.54 | 37.39 ± 19.65 | -0.179 | [-3.679, +3.357] |  |
| lost | 0.033 ± 0.021 | 0.023 ± 0.021 | -0.010 | [-0.020, -0.001] | old_senses better |
| unconscious | 0.218 ± 0.121 | 0.221 ± 0.124 | +0.003 | [-0.017, +0.027] | can't tell |

## ALL (48 pairs from 12 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.516 ± 0.479 | 0.513 ± 0.479 | -0.002 | [-0.036, +0.038] | can't tell |
| collapses | 2.12 ± 2.36 | 2.15 ± 2.41 | +0.021 | [-0.208, +0.271] | can't tell |
| loop_collapses | 1.62 ± 1.92 | 1.67 ± 1.95 | +0.042 | [-0.125, +0.292] | can't tell |
| two_step | 0.65 ± 0.85 | 0.67 ± 0.82 | +0.021 | [-0.167, +0.250] | can't tell |
| meals | 15.40 ± 7.65 | 15.44 ± 7.52 | +0.042 | [-0.771, +0.854] |  |
| drinks | 51.06 ± 22.41 | 50.58 ± 21.69 | -0.479 | [-2.501, +1.688] |  |
| lost | 0.027 ± 0.020 | 0.027 ± 0.038 | +0.000 | [-0.014, +0.023] | can't tell |
| unconscious | 0.127 ± 0.141 | 0.129 ± 0.144 | +0.002 | [-0.011, +0.016] | can't tell |
