---
type: moc
topic: strategies
created: 2026-07-30
updated: 2026-07-30
tags: [moc, strategies, navigation]
---

# Strategies MOC

Navigation hub for all HermesForge trading strategies.

## Active (publish_enabled: true)

```dataview
TABLE core_idea AS "Idea", market_regime AS "Regime", asset_class AS "Asset", confidence AS "Confidence"
FROM "06-Strategies/Hypotheses"
WHERE type = "strategy" AND publish_enabled = true
SORT file.name ASC
```

## All Strategies by Status

```dataview
TABLE status, core_idea AS "Idea", market_regime AS "Regime", asset_class AS "Asset"
FROM "06-Strategies/Hypotheses"
WHERE type = "strategy"
SORT status ASC, file.name ASC
```

## By Regime

```dataview
TABLE rows.file.name AS "Strategies"
FROM "06-Strategies/Hypotheses"
WHERE type = "strategy"
GROUP BY market_regime
SORT rows.file.name ASC
```

## Backtest Results

```dataview
TABLE strategy_id, phase, sharpe, annual_return, max_drawdown, verdict
FROM "06-Strategies/Backtests"
WHERE type = "backtest-result"
SORT strategy_id ASC, phase ASC
```

## Failure Modes

```dataview
TABLE strategy_id, reason, phase
FROM "06-Strategies/Failure-Modes"
WHERE type = "failure-mode"
SORT strategy_id ASC
```

## Regime Nodes

```dataview
TABLE regime_type, description
FROM "06-Strategies/Regimes"
WHERE type = "regime"
SORT regime_type ASC
```

## Related
- [[GRAPH-INVENTORY-AND-ONTOLOGY]]
- [[SECOND-BRAIN-ELEVATION-PLAN]]
- [[ADR-004-Phase1-Validation-Framework]]
- [[RISK_RULES]]
