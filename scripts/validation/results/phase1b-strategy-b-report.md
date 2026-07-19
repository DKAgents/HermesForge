# Phase 1B Results — Strategy B

## Pre-Registered Questions
- Q1: Does longer time stop (16 bars) improve EV?
- Q2: Does regime-aware direction filter fix edge decay?
- Q3: Does capping maturity at 40 bars improve quality?

## Results Table

| Variant                        |     N |  Sig/Yr |   Avg R |    Win% |      EV |
|--------------------------------|-------|---------|---------|---------|---------|
| baseline_8bar                  |   561 |    79.7 |   0.554 |   42.4% |   0.554 |
| time_stop_12                   |   561 |    79.7 |   0.470 |   33.9% |   0.470 |
| time_stop_16                   |   561 |    79.7 |   0.475 |   29.4% |   0.475 |
| time_stop_24                   |   561 |    79.7 |   0.582 |   26.6% |   0.582 |
| regime_aware                   |   416 |    59.2 |   0.714 |   44.5% |   0.714 |
| short_only                     |   448 |    63.6 |   0.489 |   41.3% |   0.489 |
| long_only                      |   113 |    16.5 |   0.810 |   46.9% |   0.810 |
| maturity_cap_40                |   389 |    55.2 |   0.634 |   43.4% |   0.634 |
| maturity_cap_30                |   287 |    40.8 |   0.598 |   43.9% |   0.598 |
| combined_best                  |   288 |    41.0 |   0.756 |   33.3% |   0.756 |