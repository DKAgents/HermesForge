# US-114 Walk-Forward Validation Report
**Generated:** 2026-08-16 01:21 UTC
**Job:** 19-strategy scan | IS=60% | OOS=40% | Bootstrap + t-test

## Summary Table

| Strategy | IS Trades | IS Win% | IS Avg R | IS PF | IS Expect. | OOS Trades | OOS Win% | OOS Avg R | OOS PF | OOS Expect. | OOS p-val | OOS 95% CI | VERDICT | Notes |
|----------|----------|--------|---------|------|-----------|-----------|---------|----------|-------|------------|----------|-----------|---------|-------|
| STR-R | 306 | 37.9% | 0.2994 | 1.568 | 0.2994 | 204 | 32.4% | 0.1559 | 1.267 | 0.1559 | 0.0750 | [-0.0637, 0.3755] | FAIL | OOS avg R (0.156) < IS avg R (0.299) - 0.1; OOS win rate (32.4%) < IS win rate (37.9%) - 5.0pp; OOS mean R not statistically significant (bootstrap p=0.0750, t-test p=0.0815) |
| STR-S | 30 | 56.7% | 0.1623 | 1.375 | 0.1623 | 21 | 42.9% | -0.1034 | 0.763 | -0.1034 | 0.7057 | [-0.5271, 0.3202] | FAIL | OOS avg R (-0.103) < IS avg R (0.162) - 0.1; OOS win rate (42.9%) < IS win rate (56.7%) - 5.0pp; OOS profit factor (0.763) < 1.0; OOS mean R not statistically significant (bootstrap p=0.7057, t-test p=0.6919) |
| STR-T | 176 | 67.0% | 0.2982 | 2.326 | 0.2982 | 118 | 58.5% | 0.1733 | 1.594 | 0.1733 | 0.0103 | [0.0246, 0.3221] | FAIL | OOS avg R (0.173) < IS avg R (0.298) - 0.1; OOS win rate (58.5%) < IS win rate (67.0%) - 5.0pp |
| STR-U | 51 | 64.7% | 0.2265 | 2.042 | 0.2265 | 35 | 60.0% | 0.0746 | 1.289 | 0.0746 | 0.2642 | [-0.1767, 0.3260] | FAIL | OOS avg R (0.075) < IS avg R (0.227) - 0.1; OOS mean R not statistically significant (bootstrap p=0.2642, t-test p=0.2751) |
| STR-V | 465 | 54.8% | 0.2103 | 1.581 | 0.2103 | 311 | 58.5% | 0.2853 | 1.844 | 0.2853 | 0.0000 | [0.1536, 0.4171] | PASS | — |
| STR-W | 9986 | 54.1% | 0.1678 | 1.437 | 0.1678 | 6658 | 55.8% | 0.1336 | 1.358 | 0.1336 | 0.0000 | [0.1089, 0.1584] | PASS | — |
| STR-X | 964 | 50.4% | 0.2812 | 1.648 | 0.2812 | 643 | 50.7% | 0.2647 | 1.625 | 0.2647 | 0.0000 | [0.1623, 0.3671] | PASS | — |
| STR-Y | 144 | 43.8% | 0.1551 | 1.295 | 0.1551 | 97 | 45.4% | 0.2275 | 1.439 | 0.2275 | 0.0655 | [-0.0665, 0.5216] | FAIL | OOS mean R not statistically significant (bootstrap p=0.0655, t-test p=0.0639) |
| STR-Z | 585 | 43.2% | 0.1344 | 1.252 | 0.1344 | 391 | 46.8% | 0.3527 | 1.713 | 0.3527 | 0.0000 | [0.1991, 0.5063] | PASS | — |
| STR-AA | 1300 | 43.2% | 0.1765 | 1.328 | 0.1765 | 867 | 43.5% | 0.2466 | 1.476 | 0.2466 | 0.0000 | [0.1470, 0.3463] | PASS | — |
| STR-AB | 138 | 52.9% | 0.2557 | 1.719 | 0.2557 | 92 | 53.3% | 0.2439 | 1.728 | 0.2439 | 0.0199 | [0.0063, 0.4814] | PASS | — |
| STR-AC | 879 | 43.7% | 0.1963 | 1.371 | 0.1963 | 587 | 44.8% | 0.2780 | 1.556 | 0.2780 | 0.0000 | [0.1576, 0.3984] | PASS | — |
| STR-AD | 795 | 53.1% | 0.3092 | 1.763 | 0.3092 | 531 | 52.0% | 0.3011 | 1.694 | 0.3011 | 0.0000 | [0.1869, 0.4153] | PASS | — |
| STR-AE | 1306 | 58.1% | 0.2041 | 1.751 | 0.2041 | 872 | 56.5% | 0.1778 | 1.678 | 0.1778 | 0.0000 | [0.1185, 0.2371] | PASS | — |
| STR-AF | 4317 | 42.4% | 0.1648 | 1.296 | 0.1648 | 2878 | 41.7% | 0.1622 | 1.287 | 0.1622 | 0.0000 | [0.1116, 0.2127] | PASS | — |
| STR-AG | 762 | 52.4% | 0.2165 | 1.548 | 0.2165 | 509 | 64.4% | 0.3717 | 2.411 | 0.3717 | 0.0000 | [0.2753, 0.4682] | PASS | — |
| STR-AH | 70 | 74.3% | 0.4767 | 3.968 | 0.4767 | 48 | 64.6% | 0.4451 | 3.039 | 0.4451 | 0.0020 | [0.1256, 0.7647] | FAIL | OOS win rate (64.6%) < IS win rate (74.3%) - 5.0pp |
| STR-AI | 158 | 57.6% | 0.5629 | 2.480 | 0.5629 | 106 | 37.7% | 0.1401 | 1.260 | 0.1401 | 0.1634 | [-0.1417, 0.4219] | FAIL | OOS avg R (0.140) < IS avg R (0.563) - 0.1; OOS win rate (37.7%) < IS win rate (57.6%) - 5.0pp; OOS mean R not statistically significant (bootstrap p=0.1634, t-test p=0.1633) |
| STR-AJ | 300 | 54.0% | 0.4519 | 2.102 | 0.4519 | 201 | 56.2% | 0.4803 | 2.262 | 0.4803 | 0.0000 | [0.2883, 0.6724] | PASS | — |

**Totals:** 12 PASS | 7 FAIL | 0 INSUFFICIENT | 0 NO-DATA

## Detailed Per-Strategy Breakdown

### STR-R
- **Verdict:** FAIL
- **Trades:** 306 IS → 204 OOS
- **IS period:** 2018-11-01 to 2023-08-28
- **OOS period:** 2023-08-31 to 2026-07-13
- **IS metrics:** Win Rate=37.9%, Avg R=0.2994, PF=1.568, Expectancy=0.2994
- **OOS metrics:** Win Rate=32.4%, Avg R=0.1559, PF=1.267, Expectancy=0.1559
- **OOS p-value (bootstrap):** 0.0750
- **OOS 95% CI:** [-0.0637, 0.3755]
- **Flags:** OOS avg R (0.156) < IS avg R (0.299) - 0.1; OOS win rate (32.4%) < IS win rate (37.9%) - 5.0pp; OOS mean R not statistically significant (bootstrap p=0.0750, t-test p=0.0815)

### STR-S
- **Verdict:** FAIL
- **Trades:** 30 IS → 21 OOS
- **IS period:** 2019-02-15 to 2023-03-16
- **OOS period:** 2023-04-20 to 2025-09-17
- **IS metrics:** Win Rate=56.7%, Avg R=0.1623, PF=1.375, Expectancy=0.1623
- **OOS metrics:** Win Rate=42.9%, Avg R=-0.1034, PF=0.763, Expectancy=-0.1034
- **OOS p-value (bootstrap):** 0.7057
- **OOS 95% CI:** [-0.5271, 0.3202]
- **Flags:** OOS avg R (-0.103) < IS avg R (0.162) - 0.1; OOS win rate (42.9%) < IS win rate (56.7%) - 5.0pp; OOS profit factor (0.763) < 1.0; OOS mean R not statistically significant (bootstrap p=0.7057, t-test p=0.6919)

### STR-T
- **Verdict:** FAIL
- **Trades:** 176 IS → 118 OOS
- **IS period:** 2018-11-05 to 2023-11-02
- **OOS period:** 2023-11-06 to 2026-07-28
- **IS metrics:** Win Rate=67.0%, Avg R=0.2982, PF=2.326, Expectancy=0.2982
- **OOS metrics:** Win Rate=58.5%, Avg R=0.1733, PF=1.594, Expectancy=0.1733
- **OOS p-value (bootstrap):** 0.0103
- **OOS 95% CI:** [0.0246, 0.3221]
- **Flags:** OOS avg R (0.173) < IS avg R (0.298) - 0.1; OOS win rate (58.5%) < IS win rate (67.0%) - 5.0pp

### STR-U
- **Verdict:** FAIL
- **Trades:** 51 IS → 35 OOS
- **IS period:** 2018-11-05 to 2023-04-28
- **OOS period:** 2023-06-01 to 2026-01-09
- **IS metrics:** Win Rate=64.7%, Avg R=0.2265, PF=2.042, Expectancy=0.2265
- **OOS metrics:** Win Rate=60.0%, Avg R=0.0746, PF=1.289, Expectancy=0.0746
- **OOS p-value (bootstrap):** 0.2642
- **OOS 95% CI:** [-0.1767, 0.3260]
- **Flags:** OOS avg R (0.075) < IS avg R (0.227) - 0.1; OOS mean R not statistically significant (bootstrap p=0.2642, t-test p=0.2751)

### STR-V
- **Verdict:** PASS
- **Trades:** 465 IS → 311 OOS
- **IS period:** 2018-11-01 to 2023-05-25
- **OOS period:** 2023-05-26 to 2026-08-03
- **IS metrics:** Win Rate=54.8%, Avg R=0.2103, PF=1.581, Expectancy=0.2103
- **OOS metrics:** Win Rate=58.5%, Avg R=0.2853, PF=1.844, Expectancy=0.2853
- **OOS p-value (bootstrap):** 0.0000
- **OOS 95% CI:** [0.1536, 0.4171]

### STR-W
- **Verdict:** PASS
- **Trades:** 9986 IS → 6658 OOS
- **IS period:** 2018-11-07 to 2023-05-18
- **OOS period:** 2023-05-18 to 2026-08-13
- **IS metrics:** Win Rate=54.1%, Avg R=0.1678, PF=1.437, Expectancy=0.1678
- **OOS metrics:** Win Rate=55.8%, Avg R=0.1336, PF=1.358, Expectancy=0.1336
- **OOS p-value (bootstrap):** 0.0000
- **OOS 95% CI:** [0.1089, 0.1584]

### STR-X
- **Verdict:** PASS
- **Trades:** 964 IS → 643 OOS
- **IS period:** 2018-10-09 to 2023-06-14
- **OOS period:** 2023-06-14 to 2026-08-11
- **IS metrics:** Win Rate=50.4%, Avg R=0.2812, PF=1.648, Expectancy=0.2812
- **OOS metrics:** Win Rate=50.7%, Avg R=0.2647, PF=1.625, Expectancy=0.2647
- **OOS p-value (bootstrap):** 0.0000
- **OOS 95% CI:** [0.1623, 0.3671]

### STR-Y
- **Verdict:** FAIL
- **Trades:** 144 IS → 97 OOS
- **IS period:** 2018-11-09 to 2023-08-04
- **OOS period:** 2023-08-10 to 2026-07-15
- **IS metrics:** Win Rate=43.8%, Avg R=0.1551, PF=1.295, Expectancy=0.1551
- **OOS metrics:** Win Rate=45.4%, Avg R=0.2275, PF=1.439, Expectancy=0.2275
- **OOS p-value (bootstrap):** 0.0655
- **OOS 95% CI:** [-0.0665, 0.5216]
- **Flags:** OOS mean R not statistically significant (bootstrap p=0.0655, t-test p=0.0639)

### STR-Z
- **Verdict:** PASS
- **Trades:** 585 IS → 391 OOS
- **IS period:** 2018-10-30 to 2023-08-09
- **OOS period:** 2023-08-14 to 2026-08-05
- **IS metrics:** Win Rate=43.2%, Avg R=0.1344, PF=1.252, Expectancy=0.1344
- **OOS metrics:** Win Rate=46.8%, Avg R=0.3527, PF=1.713, Expectancy=0.3527
- **OOS p-value (bootstrap):** 0.0000
- **OOS 95% CI:** [0.1991, 0.5063]

### STR-AA
- **Verdict:** PASS
- **Trades:** 1300 IS → 867 OOS
- **IS period:** 2018-10-22 to 2023-04-27
- **OOS period:** 2023-04-27 to 2026-08-12
- **IS metrics:** Win Rate=43.2%, Avg R=0.1765, PF=1.328, Expectancy=0.1765
- **OOS metrics:** Win Rate=43.5%, Avg R=0.2466, PF=1.476, Expectancy=0.2466
- **OOS p-value (bootstrap):** 0.0000
- **OOS 95% CI:** [0.1470, 0.3463]

### STR-AB
- **Verdict:** PASS
- **Trades:** 138 IS → 92 OOS
- **IS period:** 2018-10-29 to 2023-08-28
- **OOS period:** 2023-09-08 to 2026-08-13
- **IS metrics:** Win Rate=52.9%, Avg R=0.2557, PF=1.719, Expectancy=0.2557
- **OOS metrics:** Win Rate=53.3%, Avg R=0.2439, PF=1.728, Expectancy=0.2439
- **OOS p-value (bootstrap):** 0.0199
- **OOS 95% CI:** [0.0063, 0.4814]

### STR-AC
- **Verdict:** PASS
- **Trades:** 879 IS → 587 OOS
- **IS period:** 2018-10-30 to 2023-05-17
- **OOS period:** 2023-05-22 to 2026-08-13
- **IS metrics:** Win Rate=43.7%, Avg R=0.1963, PF=1.371, Expectancy=0.1963
- **OOS metrics:** Win Rate=44.8%, Avg R=0.2780, PF=1.556, Expectancy=0.2780
- **OOS p-value (bootstrap):** 0.0000
- **OOS 95% CI:** [0.1576, 0.3984]

### STR-AD
- **Verdict:** PASS
- **Trades:** 795 IS → 531 OOS
- **IS period:** 2018-10-26 to 2023-06-22
- **OOS period:** 2023-06-22 to 2026-08-13
- **IS metrics:** Win Rate=53.1%, Avg R=0.3092, PF=1.763, Expectancy=0.3092
- **OOS metrics:** Win Rate=52.0%, Avg R=0.3011, PF=1.694, Expectancy=0.3011
- **OOS p-value (bootstrap):** 0.0000
- **OOS 95% CI:** [0.1869, 0.4153]

### STR-AE
- **Verdict:** PASS
- **Trades:** 1306 IS → 872 OOS
- **IS period:** 2018-11-05 to 2023-06-27
- **OOS period:** 2023-06-28 to 2026-08-13
- **IS metrics:** Win Rate=58.1%, Avg R=0.2041, PF=1.751, Expectancy=0.2041
- **OOS metrics:** Win Rate=56.5%, Avg R=0.1778, PF=1.678, Expectancy=0.1778
- **OOS p-value (bootstrap):** 0.0000
- **OOS 95% CI:** [0.1185, 0.2371]

### STR-AF
- **Verdict:** PASS
- **Trades:** 4317 IS → 2878 OOS
- **IS period:** 2018-10-03 to 2023-07-20
- **OOS period:** 2023-07-20 to 2026-08-13
- **IS metrics:** Win Rate=42.4%, Avg R=0.1648, PF=1.296, Expectancy=0.1648
- **OOS metrics:** Win Rate=41.7%, Avg R=0.1622, PF=1.287, Expectancy=0.1622
- **OOS p-value (bootstrap):** 0.0000
- **OOS 95% CI:** [0.1116, 0.2127]

### STR-AG
- **Verdict:** PASS
- **Trades:** 762 IS → 509 OOS
- **IS period:** 2018-10-31 to 2023-10-10
- **OOS period:** 2023-10-10 to 2026-08-06
- **IS metrics:** Win Rate=52.4%, Avg R=0.2165, PF=1.548, Expectancy=0.2165
- **OOS metrics:** Win Rate=64.4%, Avg R=0.3717, PF=2.411, Expectancy=0.3717
- **OOS p-value (bootstrap):** 0.0000
- **OOS 95% CI:** [0.2753, 0.4682]

### STR-AH
- **Verdict:** FAIL
- **Trades:** 70 IS → 48 OOS
- **IS period:** 2019-01-31 to 2023-05-30
- **OOS period:** 2023-05-30 to 2026-07-28
- **IS metrics:** Win Rate=74.3%, Avg R=0.4767, PF=3.968, Expectancy=0.4767
- **OOS metrics:** Win Rate=64.6%, Avg R=0.4451, PF=3.039, Expectancy=0.4451
- **OOS p-value (bootstrap):** 0.0020
- **OOS 95% CI:** [0.1256, 0.7647]
- **Flags:** OOS win rate (64.6%) < IS win rate (74.3%) - 5.0pp

### STR-AI
- **Verdict:** FAIL
- **Trades:** 158 IS → 106 OOS
- **IS period:** 2023-11-01 to 2025-07-01
- **OOS period:** 2025-07-01 to 2026-08-03
- **IS metrics:** Win Rate=57.6%, Avg R=0.5629, PF=2.480, Expectancy=0.5629
- **OOS metrics:** Win Rate=37.7%, Avg R=0.1401, PF=1.260, Expectancy=0.1401
- **OOS p-value (bootstrap):** 0.1634
- **OOS 95% CI:** [-0.1417, 0.4219]
- **Flags:** OOS avg R (0.140) < IS avg R (0.563) - 0.1; OOS win rate (37.7%) < IS win rate (57.6%) - 5.0pp; OOS mean R not statistically significant (bootstrap p=0.1634, t-test p=0.1633)

### STR-AJ
- **Verdict:** PASS
- **Trades:** 300 IS → 201 OOS
- **IS period:** 2019-03-25 to 2023-11-07
- **OOS period:** 2023-11-07 to 2026-04-14
- **IS metrics:** Win Rate=54.0%, Avg R=0.4519, PF=2.102, Expectancy=0.4519
- **OOS metrics:** Win Rate=56.2%, Avg R=0.4803, PF=2.262, Expectancy=0.4803
- **OOS p-value (bootstrap):** 0.0000
- **OOS 95% CI:** [0.2883, 0.6724]

## Gate Decision

**Only PASS strategies clear the gate for paper trading.**
FAIL strategies require redesign and re-validation before advancing to Phase 1B/2.
INSUFFICIENT strategies need more data before a conclusion can be drawn.

| Outcome | Count |
|---------|-------|
| PASS (clears gate) | 12 |
| FAIL (blocked) | 7 |
| INSUFFICIENT (need data) | 0 |
| NO-DATA (not tested) | 0 |
| **Total** | **19** |

### BLOCKED STRATEGIES — Immediate Attention Required

- **STR-R**: OOS avg R (0.156) < IS avg R (0.299) - 0.1; OOS win rate (32.4%) < IS win rate (37.9%) - 5.0pp; OOS mean R not statistically significant (bootstrap p=0.0750, t-test p=0.0815)
- **STR-S**: OOS avg R (-0.103) < IS avg R (0.162) - 0.1; OOS win rate (42.9%) < IS win rate (56.7%) - 5.0pp; OOS profit factor (0.763) < 1.0; OOS mean R not statistically significant (bootstrap p=0.7057, t-test p=0.6919)
- **STR-T**: OOS avg R (0.173) < IS avg R (0.298) - 0.1; OOS win rate (58.5%) < IS win rate (67.0%) - 5.0pp
- **STR-U**: OOS avg R (0.075) < IS avg R (0.227) - 0.1; OOS mean R not statistically significant (bootstrap p=0.2642, t-test p=0.2751)
- **STR-Y**: OOS mean R not statistically significant (bootstrap p=0.0655, t-test p=0.0639)
- **STR-AH**: OOS win rate (64.6%) < IS win rate (74.3%) - 5.0pp
- **STR-AI**: OOS avg R (0.140) < IS avg R (0.563) - 0.1; OOS win rate (37.7%) < IS win rate (57.6%) - 5.0pp; OOS mean R not statistically significant (bootstrap p=0.1634, t-test p=0.1633)

These strategies showed significant OOS degradation consistent with overfitting. They must be re-optimized with walk-forward constraints (curfitted stop caps, regime-aware parameters) before re-entering validation.

---
_Generated by HermesForge Backtester Agent — US-114 Walk-Forward Gate_