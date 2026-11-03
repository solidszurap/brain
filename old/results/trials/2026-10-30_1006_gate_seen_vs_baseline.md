# gate_seen vs baseline

2026-10-30T10:06:07+01:00. Ember's saved life at moment 62,704; starting moments found by living a copy forward (bank built 2026-10-30T09:39:59+01:00). Each starting moment x 4 seeds x 1,000 moments, both versions with the same seeds (paired).

- **baseline**: Ember as it is now
- **gate_seen**: candidate fix: seeing the shut gate corrects its belief that the gate is open

Numbers: mean ± spread (sd) across lives. Diff = gate_seen − baseline, with a 95% bootstrap interval that resamples starting moments, then lives within them (lives from the same moment aren't independent). With only 1-2 starting moments in a situation the interval is honest but wide. A verdict says "better" only when the interval is clear of zero; otherwise "can't tell".

Lower is better: need-error (how far its needs are from satisfied, averaged), collapses, loop collapses (collapsed again within 150 moments of coming round), lost (wrong about where it is), unconscious (share of moments). Higher is better: two-step plans (opened the gate, then ate).

## now: the saved life itself, as it is (4 pairs from 1 starting moments)

| | baseline | gate_seen | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 1.435 ± 0.042 | 0.792 ± 0.269 | -0.643 | [-0.871, -0.418] | gate_seen better |
| collapses | 7.25 ± 0.43 | 3.50 ± 1.80 | -3.750 | [-5.250, -2.500] | gate_seen better |
| loop_collapses | 6.25 ± 0.43 | 1.50 ± 1.66 | -4.750 | [-6.000, -3.500] | gate_seen better |
| two_step | 0.00 ± 0.00 | 1.75 ± 0.43 | +1.750 | [+1.250, +2.000] | gate_seen better |
| meals | 0.00 ± 0.00 | 10.50 ± 4.77 | +10.500 | [+6.000, +15.000] |  |
| drinks | 4.50 ± 3.35 | 45.75 ± 16.90 | +41.250 | [+28.000, +57.750] |  |
| lost | 0.000 ± 0.000 | 0.009 ± 0.009 | +0.009 | [+0.001, +0.017] | baseline better |
| unconscious | 0.421 ± 0.002 | 0.183 ± 0.095 | -0.238 | [-0.321, -0.150] | gate_seen better |

## came_round: just came round from a collapse (the start of a collapse loop) (8 pairs from 2 starting moments)

| | baseline | gate_seen | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 1.140 ± 0.314 | 0.394 ± 0.092 | -0.746 | [-0.999, -0.447] | gate_seen better |
| collapses | 5.50 ± 1.73 | 1.25 ± 0.43 | -4.250 | [-5.750, -2.500] | gate_seen better |
| loop_collapses | 4.50 ± 1.73 | 0.00 ± 0.00 | -4.500 | [-6.000, -2.500] | gate_seen better |
| two_step | 0.00 ± 0.00 | 2.25 ± 0.66 | +2.250 | [+1.750, +2.750] | gate_seen better |
| meals | 3.50 ± 3.87 | 15.38 ± 1.93 | +11.875 | [+8.250, +15.500] |  |
| drinks | 18.62 ± 15.43 | 58.62 ± 1.93 | +40.000 | [+23.000, +54.253] |  |
| lost | 0.001 ± 0.003 | 0.031 ± 0.030 | +0.030 | [+0.004, +0.052] | baseline better |
| unconscious | 0.330 ± 0.104 | 0.075 ± 0.026 | -0.255 | [-0.345, -0.150] | gate_seen better |

## winter_gate: winter, hungry, the orchard gate shut (8 pairs from 2 starting moments)

| | baseline | gate_seen | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 1.432 ± 0.069 | 0.557 ± 0.109 | -0.875 | [-0.963, -0.724] | gate_seen better |
| collapses | 7.75 ± 0.43 | 2.62 ± 0.70 | -5.125 | [-5.750, -4.125] | gate_seen better |
| loop_collapses | 6.75 ± 0.43 | 1.00 ± 0.00 | -5.750 | [-6.000, -5.250] | gate_seen better |
| two_step | 0.00 ± 0.00 | 2.38 ± 0.48 | +2.375 | [+2.000, +2.750] | gate_seen better |
| meals | 0.38 ± 0.70 | 14.25 ± 2.44 | +13.875 | [+11.250, +15.750] |  |
| drinks | 8.00 ± 6.20 | 50.00 ± 5.10 | +42.000 | [+31.375, +49.628] |  |
| lost | 0.000 ± 0.000 | 0.036 ± 0.023 | +0.036 | [+0.021, +0.053] | baseline better |
| unconscious | 0.442 ± 0.013 | 0.157 ± 0.042 | -0.284 | [-0.316, -0.239] | gate_seen better |

## two_needs: hungry and thirsty at the same time (8 pairs from 2 starting moments)

| | baseline | gate_seen | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.905 ± 0.518 | 0.356 ± 0.257 | -0.549 | [-0.890, -0.177] | gate_seen better |
| collapses | 4.38 ± 2.78 | 1.25 ± 1.48 | -3.125 | [-5.000, -1.125] | gate_seen better |
| loop_collapses | 3.50 ± 2.60 | 0.38 ± 0.70 | -3.125 | [-5.625, -0.500] | gate_seen better |
| two_step | 0.00 ± 0.00 | 1.88 ± 0.60 | +1.875 | [+1.500, +2.375] | gate_seen better |
| meals | 6.50 ± 6.86 | 17.50 ± 4.85 | +11.000 | [+6.750, +14.500] |  |
| drinks | 28.75 ± 23.03 | 58.25 ± 10.49 | +29.500 | [+10.125, +49.375] |  |
| lost | 0.004 ± 0.010 | 0.027 ± 0.019 | +0.023 | [+0.005, +0.046] | baseline better |
| unconscious | 0.263 ± 0.167 | 0.065 ± 0.076 | -0.198 | [-0.314, -0.068] | gate_seen better |

## dry_thirsty: summer or autumn (ponds drying), thirsty (8 pairs from 2 starting moments)

| | baseline | gate_seen | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.140 ± 0.091 | 0.086 ± 0.007 | -0.054 | [-0.165, +0.020] | can't tell |
| collapses | 0.25 ± 0.43 | 0.00 ± 0.00 | -0.250 | [-0.750, +0.000] | can't tell |
| loop_collapses | 0.00 ± 0.00 | 0.00 ± 0.00 | +0.000 | [+0.000, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.25 ± 0.43 | +0.250 | [+0.000, +0.750] | can't tell |
| meals | 21.00 ± 4.42 | 21.75 ± 2.17 | +0.750 | [-3.000, +4.125] |  |
| drinks | 71.12 ± 4.14 | 74.12 ± 1.45 | +3.000 | [+0.250, +6.500] |  |
| lost | 0.001 ± 0.001 | 0.011 ± 0.009 | +0.010 | [+0.003, +0.020] | baseline better |
| unconscious | 0.015 ± 0.026 | 0.000 ± 0.000 | -0.015 | [-0.045, +0.000] | can't tell |

## plains: out on the windy plains (pushes hard to notice) (4 pairs from 1 starting moments)

| | baseline | gate_seen | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.360 ± 0.175 | 0.111 ± 0.016 | -0.249 | [-0.398, -0.063] | gate_seen better |
| collapses | 1.25 ± 0.83 | 0.00 ± 0.00 | -1.250 | [-2.000, -0.500] | gate_seen better |
| loop_collapses | 0.25 ± 0.43 | 0.00 ± 0.00 | -0.250 | [-0.750, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 1.25 ± 0.43 | +1.250 | [+1.000, +1.750] | gate_seen better |
| meals | 14.50 ± 3.28 | 21.50 ± 2.29 | +7.000 | [+3.500, +11.000] |  |
| drinks | 57.25 ± 7.05 | 69.25 ± 2.49 | +12.000 | [+4.500, +19.500] |  |
| lost | 0.021 ± 0.032 | 0.019 ± 0.011 | -0.001 | [-0.043, +0.028] | can't tell |
| unconscious | 0.075 ± 0.050 | 0.000 ± 0.000 | -0.075 | [-0.120, -0.030] | gate_seen better |

## ordinary: nothing pressing: all needs above 60% (8 pairs from 2 starting moments)

| | baseline | gate_seen | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.255 ± 0.165 | 0.113 ± 0.023 | -0.142 | [-0.277, -0.025] | gate_seen better |
| collapses | 0.75 ± 0.83 | 0.00 ± 0.00 | -0.750 | [-1.625, +0.000] | can't tell |
| loop_collapses | 0.12 ± 0.33 | 0.00 ± 0.00 | -0.125 | [-0.500, +0.000] | can't tell |
| two_step | 0.00 ± 0.00 | 0.75 ± 0.43 | +0.750 | [+0.250, +1.000] | gate_seen better |
| meals | 16.75 ± 3.11 | 21.88 ± 1.45 | +5.125 | [+2.250, +7.875] |  |
| drinks | 64.12 ± 5.88 | 70.00 ± 2.24 | +5.875 | [-0.628, +13.375] |  |
| lost | 0.002 ± 0.004 | 0.020 ± 0.016 | +0.018 | [+0.009, +0.027] | baseline better |
| unconscious | 0.045 ± 0.050 | 0.000 ± 0.000 | -0.045 | [-0.098, +0.000] | can't tell |

## ALL HARD (32 pairs from 8 starting moments)

| | baseline | gate_seen | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.904 ± 0.570 | 0.348 ± 0.224 | -0.556 | [-0.793, -0.293] | gate_seen better |
| collapses | 4.47 ± 3.19 | 1.28 ± 1.26 | -3.188 | [-4.594, -1.688] | gate_seen better |
| loop_collapses | 3.69 ± 2.90 | 0.34 ± 0.54 | -3.344 | [-5.094, -1.625] | gate_seen better |
| two_step | 0.00 ± 0.00 | 1.69 ± 1.01 | +1.688 | [+1.031, +2.250] | gate_seen better |
| meals | 7.84 ± 9.10 | 17.22 ± 4.20 | +9.375 | [+5.249, +13.001] |  |
| drinks | 31.62 ± 27.93 | 60.25 ± 10.56 | +28.625 | [+15.343, +40.970] |  |
| lost | 0.001 ± 0.005 | 0.026 ± 0.024 | +0.025 | [+0.014, +0.036] | baseline better |
| unconscious | 0.262 ± 0.185 | 0.074 ± 0.072 | -0.188 | [-0.269, -0.099] | gate_seen better |

## ALL (48 pairs from 12 starting moments)

| | baseline | gate_seen | diff | 95% interval | verdict |
|---|---|---|---|---|---|
| need_error | 0.795 ± 0.574 | 0.326 ± 0.264 | -0.469 | [-0.674, -0.270] | gate_seen better |
| collapses | 3.81 ± 3.22 | 1.15 ± 1.46 | -2.667 | [-3.833, -1.479] | gate_seen better |
| loop_collapses | 3.02 ± 2.98 | 0.35 ± 0.75 | -2.667 | [-4.083, -1.208] | gate_seen better |
| two_step | 0.00 ± 0.00 | 1.50 ± 0.94 | +1.500 | [+1.042, +1.958] | gate_seen better |
| meals | 9.23 ± 8.83 | 17.79 ± 4.80 | +8.562 | [+5.749, +11.250] |  |
| drinks | 36.92 ± 28.19 | 61.42 ± 11.76 | +24.500 | [+14.042, +35.273] |  |
| lost | 0.003 ± 0.012 | 0.023 ± 0.021 | +0.020 | [+0.011, +0.030] | baseline better |
| unconscious | 0.224 ± 0.187 | 0.065 ± 0.080 | -0.159 | [-0.227, -0.090] | gate_seen better |
