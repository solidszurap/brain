# old_senses vs baseline

2026-10-30T14:36:16+01:00. Ember's saved life at moment 114,871; starting moments found by living a copy forward (bank built 2026-10-30T13:47:31+01:00). Each starting moment x 4 seeds x 1,000 moments, both versions with the same seeds (paired).

- **baseline**: Ember as it is now
- **old_senses**: its eyes before the light existed: 9 kinds of things instead of 10

Numbers: mean ± spread (sd) across lives. Diff = old_senses − baseline, with a 95% bootstrap interval that resamples starting moments, then lives within them (lives from the same moment aren't independent). With only 1-2 starting moments in a situation the interval is honest but wide. A verdict says "better" only when the interval is clear of zero; otherwise "can't tell".

Lower is better: need-error (how far its needs are from satisfied, averaged), collapses, loop collapses (collapsed again within 150 moments of coming round), lost (wrong about where it is), unconscious (share of moments). Higher is better: two-step plans (opened the gate, then ate).

## now: the saved life itself, as it is (4 pairs from 1 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.087 ± 0.006 | 0.101 ± 0.026 | +0.014 | [-0.006, +0.038] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.25 ± 0.43 | 0.75 ± 0.83 | +0.500 | [+0.000, +1.000] | can't tell |
| meals | 21.75 ± 1.30 | 22.25 ± 1.92 | +0.500 | [-1.000, +2.750] |  |
| drinks | 68.25 ± 1.64 | 67.50 ± 1.12 | -0.750 | [-2.500, +1.013] |  |
| lost | 0.014 ± 0.013 | 0.024 ± 0.005 | +0.010 | [+0.001, +0.017] | baseline better |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## came_round: just came round from a collapse (the start of a collapse loop) (8 pairs from 2 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 1.007 ± 0.147 | 1.005 ± 0.162 | -0.002 | [-0.043, +0.040] | can't tell |
| collapses | 4.50 ± 0.50 | 4.62 ± 0.48 | +0.125 | [+0.000, +0.500] | can't tell |
| loop_collapses | 3.50 ± 0.50 | 3.62 ± 0.48 | +0.125 | [+0.000, +0.500] | can't tell |
| two_step | 0.88 ± 0.60 | 0.88 ± 0.78 | +0.000 | [-0.500, +0.500] | can't tell |
| meals | 7.38 ± 0.99 | 7.38 ± 1.73 | +0.000 | [-0.750, +1.250] |  |
| drinks | 28.50 ± 5.32 | 28.75 ± 5.45 | +0.250 | [-1.125, +1.125] |  |
| lost | 0.017 ± 0.018 | 0.017 ± 0.017 | +0.001 | [-0.011, +0.009] | can't tell |
| unconscious | 0.270 ± 0.030 | 0.277 ± 0.029 | +0.007 | [+0.000, +0.030] | can't tell |

## winter_gate: winter, hungry, the orchard gate shut (8 pairs from 2 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.872 ± 0.377 | 0.864 ± 0.379 | -0.009 | [-0.029, +0.011] | can't tell |
| collapses | 4.00 ± 2.00 | 4.00 ± 2.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 3.00 ± 2.00 | 3.00 ± 2.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.62 ± 0.48 | 0.75 ± 0.43 | +0.125 | [-0.250, +0.625] | can't tell |
| meals | 10.25 ± 5.76 | 11.25 ± 6.32 | +1.000 | [+0.000, +1.750] |  |
| drinks | 33.75 ± 18.77 | 33.25 ± 18.03 | -0.500 | [-1.750, +0.875] |  |
| lost | 0.017 ± 0.018 | 0.018 ± 0.020 | +0.001 | [-0.029, +0.029] | can't tell |
| unconscious | 0.240 ± 0.120 | 0.240 ± 0.120 | +0.000 | [+0.000, +0.000] | can't tell |

## two_needs: hungry and thirsty at the same time (8 pairs from 2 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 1.072 ± 0.051 | 0.959 ± 0.299 | -0.113 | [-0.442, +0.039] | can't tell |
| collapses | 5.00 ± 0.00 | 4.25 ± 1.64 | -0.750 | [-2.625, +0.000] | can't tell |
| loop_collapses | 4.00 ± 0.00 | 3.38 ± 1.32 | -0.625 | [-2.000, +0.000] | can't tell |
| two_step | 1.75 ± 0.43 | 2.00 ± 0.00 | +0.250 | [+0.000, +0.750] | can't tell |
| meals | 6.12 ± 1.17 | 8.00 ± 4.09 | +1.875 | [-0.125, +6.250] |  |
| drinks | 26.00 ± 4.58 | 32.50 ± 15.91 | +6.500 | [-1.625, +22.000] |  |
| lost | 0.021 ± 0.022 | 0.021 ± 0.017 | +0.001 | [-0.020, +0.022] | can't tell |
| unconscious | 0.300 ± 0.000 | 0.255 ± 0.098 | -0.045 | [-0.157, +0.000] | can't tell |

## dry_thirsty: summer or autumn (ponds drying), thirsty (4 pairs from 1 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.079 ± 0.008 | 0.079 ± 0.007 | -0.000 | [-0.013, +0.009] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 21.75 ± 1.48 | 22.75 ± 1.09 | +1.000 | [-1.500, +3.000] |  |
| drinks | 73.25 ± 2.28 | 72.75 ± 1.92 | -0.500 | [-2.000, +1.000] |  |
| lost | 0.066 ± 0.025 | 0.050 ± 0.014 | -0.017 | [-0.042, +0.014] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## plains: out on the windy plains (pushes hard to notice) (8 pairs from 2 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.088 ± 0.011 | 0.079 ± 0.007 | -0.009 | [-0.017, -0.001] | old_senses better |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 22.12 ± 1.76 | 21.75 ± 1.48 | -0.375 | [-1.375, +1.125] |  |
| drinks | 69.50 ± 2.50 | 69.25 ± 2.73 | -0.250 | [-1.875, +1.500] |  |
| lost | 0.030 ± 0.035 | 0.014 ± 0.010 | -0.017 | [-0.056, +0.004] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## ordinary: nothing pressing: all needs above 60% (8 pairs from 2 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.081 ± 0.009 | 0.084 ± 0.012 | +0.002 | [-0.005, +0.013] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 22.75 ± 3.53 | 21.75 ± 2.77 | -1.000 | [-4.125, +1.125] |  |
| drinks | 70.38 ± 2.23 | 69.62 ± 0.99 | -0.750 | [-2.500, +0.875] |  |
| lost | 0.030 ± 0.034 | 0.055 ± 0.078 | +0.025 | [-0.023, +0.117] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## ALL HARD (28 pairs from 7 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.854 ± 0.392 | 0.819 ± 0.410 | -0.035 | [-0.139, +0.012] | can't tell |
| collapses | 3.86 ± 1.96 | 3.68 ± 2.07 | -0.179 | [-0.786, +0.143] | can't tell |
| loop_collapses | 3.00 ± 1.69 | 2.86 ± 1.77 | -0.143 | [-0.679, +0.107] | can't tell |
| two_step | 0.93 ± 0.75 | 1.04 ± 0.82 | +0.107 | [-0.107, +0.357] | can't tell |
| meals | 9.89 ± 6.04 | 10.86 ± 6.58 | +0.964 | [+0.000, +2.393] |  |
| drinks | 35.68 ± 18.97 | 37.39 ± 19.65 | +1.714 | [-0.857, +7.107] |  |
| lost | 0.025 ± 0.026 | 0.023 ± 0.021 | -0.002 | [-0.014, +0.010] | can't tell |
| unconscious | 0.231 ± 0.118 | 0.221 ± 0.124 | -0.011 | [-0.047, +0.009] | can't tell |

## ALL (48 pairs from 12 starting moments)

| | baseline | old_senses | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.534 ± 0.483 | 0.513 ± 0.479 | -0.021 | [-0.082, +0.007] | can't tell |
| collapses | 2.25 ± 2.42 | 2.15 ± 2.41 | -0.104 | [-0.500, +0.062] | can't tell |
| loop_collapses | 1.75 ± 1.96 | 1.67 ± 1.95 | -0.083 | [-0.396, +0.062] | can't tell |
| two_step | 0.56 ± 0.73 | 0.67 ± 0.82 | +0.104 | [-0.042, +0.271] | can't tell |
| meals | 15.06 ± 7.84 | 15.44 ± 7.52 | +0.375 | [-0.562, +1.438] |  |
| drinks | 49.81 ± 22.18 | 50.58 ± 21.69 | +0.771 | [-0.876, +4.104] |  |
| lost | 0.026 ± 0.029 | 0.027 ± 0.038 | +0.001 | [-0.013, +0.021] | can't tell |
| unconscious | 0.135 ± 0.145 | 0.129 ± 0.144 | -0.006 | [-0.027, +0.004] | can't tell |
