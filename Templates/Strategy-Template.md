---
id: STR-{{date:YYYYMMDD}}-{{slug}}
type: strategy
status: hypothesis
asset_class: stocks
trade_style: swing
timeframe: daily
market_regime: trending
core_idea: breakout
confidence: low
evidence_links: []
last_reviewed: {{date:YYYY-MM-DD}}
created: {{date:YYYY-MM-DD}}
updated: {{date:YYYY-MM-DD}}
tags: [strategy, hypothesis]
---

# {{title}}

## Thesis

> One-paragraph summary: what is the edge? Why should this setup produce positive expectancy?

## Entry Criteria

- [ ] **Trend filter:** (e.g., price above 50-day MA on daily AND weekly chart confirms uptrend)
- [ ] **Pattern / Setup:** (e.g., flag/pennant, pullback to support, breakout above resistance)
- [ ] **Volume filter:** (e.g., breakout accompanied by volume > 20-day average)
- [ ] **Confirmation signal:** (e.g., RSI not overbought, MACD cross, no divergence)

## Exit Criteria

- [ ] **Stop loss:** (e.g., below breakout bar low, below prior swing low, at support)
- [ ] **Take profit / target:** (e.g., measured move, next resistance, 3:1 R:R minimum)
- [ ] **Time stop:** (e.g., exit if no progress within N bars)
- [ ] **Trailing stop:** (optional — e.g., trail below each new swing low)

## Risk Rules Applied

- [ ] PS-001: Max 1% capital risk per position
- [ ] LL-001: Daily loss limit 2% — stop trading if hit
- [ ] PT-001: Paper mode minimum 30 days before live consideration
- [ ] (add additional applicable rules)

## Supporting Evidence

> Each item below MUST be a wikilink to an existing vault note. validate_strategy.py enforces this.

- [[]] — (Murphy rule or concept)
- [[]] — (Indicator note)
- [[]] — (Risk guideline)
- [[]] — (Insight note from Insights/)

## Counter-Evidence

> Notes or edge-conditions that weaken this thesis. Be honest.

- [[]] — (e.g., edge-condition that causes this setup to fail)

## Backtest / Paper Trade Log

> Link to results files once available.

- Paper trade log: _not started_
- Backtest results: _not started_

## Change Log

| Date | Change | Trigger |
|------|--------|---------|
| {{date:YYYY-MM-DD}} | Strategy created | Initial hypothesis |
