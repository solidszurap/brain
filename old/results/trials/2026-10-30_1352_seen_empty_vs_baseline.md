# seen_empty vs baseline

2026-10-30T13:52:36+01:00. Ember's saved life at moment 114,871; starting moments found by living a copy forward (bank built 2026-10-30T13:47:31+01:00). Each starting moment x 4 seeds x 1,000 moments, both versions with the same seeds (paired).

- **baseline**: Ember as it is now
- **seen_empty**: a let-down counts when it sees an expected food place empty, not only when it stands on it

Numbers: mean ± spread (sd) across lives. Diff = seen_empty − baseline, with a 95% bootstrap interval that resamples starting moments, then lives within them (lives from the same moment aren't independent). With only 1-2 starting moments in a situation the interval is honest but wide. A verdict says "better" only when the interval is clear of zero; otherwise "can't tell".

Lower is better: need-error (how far its needs are from satisfied, averaged), collapses, loop collapses (collapsed again within 150 moments of coming round), lost (wrong about where it is), unconscious (share of moments). Higher is better: two-step plans (opened the gate, then ate).

## now: the saved life itself, as it is (4 pairs from 1 starting moments)

| | baseline | seen_empty | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.101 ± 0.026 | 0.101 ± 0.026 | +0.000 | [+0.000, +0.000] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.75 ± 0.83 | 0.75 ± 0.83 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 22.25 ± 1.92 | 22.25 ± 1.92 | +0.000 | [+0.000, +0.000] |  |
| drinks | 67.50 ± 1.12 | 67.50 ± 1.12 | +0.000 | [+0.000, +0.000] |  |
| lost | 0.024 ± 0.005 | 0.024 ± 0.005 | +0.000 | [+0.000, +0.000] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## came_round: just came round from a collapse (the start of a collapse loop) (8 pairs from 2 starting moments)

| | baseline | seen_empty | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 1.151 ± 0.335 | 1.005 ± 0.162 | -0.146 | [-0.342, +0.078] | can't tell |
| collapses | 5.50 ± 1.50 | 4.62 ± 0.48 | -0.875 | [-2.000, +0.500] | can't tell |
| loop_collapses | 4.50 ± 1.50 | 3.62 ± 0.48 | -0.875 | [-2.000, +0.500] | can't tell |
| two_step | 0.00 ± 0.00 | 0.88 ± 0.78 | +0.875 | [+0.125, +1.750] | seen_empty better |
| meals | 4.25 ± 4.38 | 7.38 ± 1.73 | +3.125 | [-0.500, +7.000] |  |
| drinks | 18.38 ± 16.94 | 28.75 ± 5.45 | +10.375 | [-4.000, +23.875] |  |
| lost | 0.011 ± 0.011 | 0.017 ± 0.017 | +0.007 | [-0.002, +0.025] | can't tell |
| unconscious | 0.330 ± 0.090 | 0.277 ± 0.029 | -0.052 | [-0.120, +0.030] | can't tell |

## winter_gate: winter, hungry, the orchard gate shut (8 pairs from 2 starting moments)

| | baseline | seen_empty | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.995 ± 0.510 | 0.864 ± 0.379 | -0.131 | [-0.271, +0.000] | can't tell |
| collapses | 5.00 ± 3.00 | 4.00 ± 2.00 | -1.000 | [-2.000, +0.000] | can't tell |
| loop_collapses | 4.00 ± 3.00 | 3.00 ± 2.00 | -1.000 | [-2.000, +0.000] | can't tell |
| two_step | 0.25 ± 0.43 | 0.75 ± 0.43 | +0.500 | [+0.000, +1.000] | can't tell |
| meals | 8.62 ± 8.83 | 11.25 ± 6.32 | +2.625 | [+0.000, +5.625] |  |
| drinks | 26.62 ± 24.66 | 33.25 ± 18.03 | +6.625 | [+0.000, +14.250] |  |
| lost | 0.009 ± 0.008 | 0.018 ± 0.020 | +0.008 | [-0.000, +0.027] | can't tell |
| unconscious | 0.275 ± 0.155 | 0.240 ± 0.120 | -0.035 | [-0.070, +0.000] | can't tell |

## two_needs: hungry and thirsty at the same time (8 pairs from 2 starting moments)

| | baseline | seen_empty | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 1.188 ± 0.409 | 0.959 ± 0.299 | -0.229 | [-0.369, -0.054] | seen_empty better |
| collapses | 5.62 ± 2.34 | 4.25 ± 1.64 | -1.375 | [-2.000, -0.375] | seen_empty better |
| loop_collapses | 4.75 ± 2.05 | 3.38 ± 1.32 | -1.375 | [-2.000, -0.375] | seen_empty better |
| two_step | 0.62 ± 0.70 | 2.00 ± 0.00 | +1.375 | [+0.500, +2.000] | seen_empty better |
| meals | 4.50 ± 5.55 | 8.00 ± 4.09 | +3.500 | [+1.625, +5.000] |  |
| drinks | 21.12 ± 20.56 | 32.50 ± 15.91 | +11.375 | [+6.250, +15.625] |  |
| lost | 0.017 ± 0.014 | 0.021 ± 0.017 | +0.004 | [-0.003, +0.012] | can't tell |
| unconscious | 0.331 ± 0.138 | 0.255 ± 0.098 | -0.076 | [-0.120, -0.016] | seen_empty better |

## dry_thirsty: summer or autumn (ponds drying), thirsty (4 pairs from 1 starting moments)

| | baseline | seen_empty | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.079 ± 0.007 | 0.079 ± 0.007 | +0.000 | [+0.000, +0.000] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 22.75 ± 1.09 | 22.75 ± 1.09 | +0.000 | [+0.000, +0.000] |  |
| drinks | 72.75 ± 1.92 | 72.75 ± 1.92 | +0.000 | [+0.000, +0.000] |  |
| lost | 0.050 ± 0.014 | 0.050 ± 0.014 | +0.000 | [+0.000, +0.000] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## plains: out on the windy plains (pushes hard to notice) (8 pairs from 2 starting moments)

| | baseline | seen_empty | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.079 ± 0.007 | 0.079 ± 0.007 | +0.000 | [+0.000, +0.000] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 21.75 ± 1.48 | 21.75 ± 1.48 | +0.000 | [+0.000, +0.000] |  |
| drinks | 69.25 ± 2.73 | 69.25 ± 2.73 | +0.000 | [+0.000, +0.000] |  |
| lost | 0.014 ± 0.010 | 0.014 ± 0.010 | +0.000 | [+0.000, +0.000] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## ordinary: nothing pressing: all needs above 60% (8 pairs from 2 starting moments)

| | baseline | seen_empty | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.084 ± 0.012 | 0.084 ± 0.012 | +0.000 | [+0.000, +0.000] | can't tell |
| collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| meals | 21.75 ± 2.77 | 21.75 ± 2.77 | +0.000 | [+0.000, +0.000] |  |
| drinks | 69.62 ± 0.99 | 69.62 ± 0.99 | +0.000 | [+0.000, +0.000] |  |
| lost | 0.055 ± 0.078 | 0.055 ± 0.078 | +0.000 | [+0.000, +0.000] | can't tell |
| unconscious | 0.000 ± 0.000 | 0.000 ± 0.000 | +0.000 | [+0.000, +0.000] | can't tell |

## ALL HARD (28 pairs from 7 starting moments)

| | baseline | seen_empty | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.964 ± 0.539 | 0.819 ± 0.410 | -0.145 | [-0.262, -0.028] | seen_empty better |
| collapses | 4.61 ± 2.90 | 3.68 ± 2.07 | -0.929 | [-1.714, -0.214] | seen_empty better |
| loop_collapses | 3.79 ± 2.62 | 2.86 ± 1.77 | -0.929 | [-1.714, -0.214] | seen_empty better |
| two_step | 0.25 ± 0.51 | 1.04 ± 0.82 | +0.786 | [+0.286, +1.357] | seen_empty better |
| meals | 8.21 ± 8.68 | 10.86 ± 6.58 | +2.643 | [+0.714, +4.607] |  |
| drinks | 29.29 ± 26.50 | 37.39 ± 19.65 | +8.107 | [+1.893, +14.644] |  |
| lost | 0.018 ± 0.018 | 0.023 ± 0.021 | +0.005 | [-0.000, +0.013] | can't tell |
| unconscious | 0.267 ± 0.165 | 0.221 ± 0.124 | -0.047 | [-0.086, -0.008] | seen_empty better |

## ALL (48 pairs from 12 starting moments)

| | baseline | seen_empty | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.598 ± 0.598 | 0.513 ± 0.479 | -0.084 | [-0.175, -0.014] | seen_empty better |
| collapses | 2.69 ± 3.17 | 2.15 ± 2.41 | -0.542 | [-1.062, -0.104] | seen_empty better |
| loop_collapses | 2.21 ± 2.74 | 1.67 ± 1.95 | -0.542 | [-1.062, -0.104] | seen_empty better |
| two_step | 0.21 ± 0.50 | 0.67 ± 0.82 | +0.458 | [+0.104, +0.875] | seen_empty better |
| meals | 13.90 ± 9.55 | 15.44 ± 7.52 | +1.542 | [+0.312, +3.042] |  |
| drinks | 45.85 ± 28.21 | 50.58 ± 21.69 | +4.729 | [+0.833, +9.521] |  |
| lost | 0.024 ± 0.038 | 0.027 ± 0.038 | +0.003 | [-0.000, +0.008] | can't tell |
| unconscious | 0.156 ± 0.182 | 0.129 ± 0.144 | -0.027 | [-0.056, -0.003] | seen_empty better |
