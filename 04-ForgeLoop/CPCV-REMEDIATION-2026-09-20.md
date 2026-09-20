# CPCV Remediation Plan — 2026-09-20

## Problem

All 4 strategies tested through CPCV (G4+G5) fail overfitting gates:

| Strategy | PBO | G4 (PBO<0.10) | G5 (Worst-DD<15R) | Verdict |
|---|---|---|---|---|
| STR-X | 0.71 | FAIL | FAIL (554R) | KILL |
| STR-AA | 0.52 | FAIL | FAIL (97R) | KILL |
| STR-AF | 0.56 | FAIL | FAIL (211R) | KILL |
| STR-B | 0.44 | FAIL | PASS (97R) | NEEDS_WORK |

Source: `04-ForgeLoop/CPCV-TRANSFER-2026-09-19.md`

## Root Cause

These strategies were built with high-DOF scanners that allow parameter optimization to overfit.
The CPCV harness correctly identifies that out-of-sample performance degrades significantly
under combinatorial purged cross-validation.

## Remediation Strategy

### Step 1: G2 Parameter Sensitivity (building now)
Identify which parameters are fragile. Strategy must survive ±20% parameter variation.

### Step 2: Slim Variants
For each failing strategy, create a "slim" variant with:
- Fewer parameters (reduce DOF by 30-50%)
- Wider stops (reduce cost drag on tight-stop strategies)
- Simpler entry rules (fewer conditions)

| Strategy | Slim Target | Reduction |
|---|---|---|
| STR-B-slim | Remove weakest indicators, keep MACD core | 8→3 params |
| STR-AA-slim | Remove secondary filters | 6→2 params |
| STR-AF-slim | Single-candle pattern only | 5→1 param |

### Step 3: Re-run CPCV on Slim Variants
If slim variant passes PBO < 0.10 → promote to Active as replacement.
If slim variant still fails → demote original to Hypotheses, kill slim.

### Step 4: Fallback — Demotion
Any strategy that cannot produce a passing slim variant is demoted:
- Move from `Active/` → `Hypotheses/`
- Update frontmatter: `status: hypothesis`
- Add CPCV failure note to strategy file

## Implementation Order

1. ✅ G2 (parameter sensitivity) — building via delegate
2. 🔲 G2 results → identify fragile params
3. 🔲 Build slim variants for STR-B (best CPCV candidate at PBO=0.44)
4. 🔲 Re-run CPCV on STR-B-slim
5. 🔲 If STR-B-slim passes → promote, deprecate STR-B-original
6. 🔲 If STR-B-slim fails → demote STR-B to Hypotheses
7. 🔲 Repeat for STR-AA, STR-AF (STR-X: PBO 0.71 is too high to salvage)

## Gate Integration

Add to `strategy-gauntlet` skill's gate sequence:
```
G0 → G1 → G2 → G3 → G4 → G5 → G6 → G7
         ↑           ↑           ↑     ↑
    parameter    overfitting  regime   live
    sensitivity  (CPCV)       robust   forward
```

G2 must pass before G4 (CPCV) runs — no point CPCV-testing a strategy that can't survive parameter perturbation.