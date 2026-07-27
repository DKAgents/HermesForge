---
type: market-briefing
date: 2026-07-20
model_tier: T3
model: google/gemini-2.0-flash-001
sources: [vault-cache, cron-history]
tags: [market-intelligence, daily-briefing, automated, partial-data]
topic: research
confidence: high
has_quotes: false
source: unknown
---
# HermesForge Daily Market Intelligence Briefing — 2026-07-20

**⚠️ Data Limitation Notice:** This briefing was produced without web search or code execution tools. Live market prices, VIX, Fear & Greed index, and breaking news could not be retrieved. The briefing structure and vault file format are established for future runs once web search capability is available. Existing vault data (lessons, insights, scan results) is used where relevant.

---

## 1. US Equity Market Overview

**Data unavailable — web search tools not available in this session.** The required data points (SPY/QQQ/IWM current prices, 1-day % change, MA position, VIX level, Fear & Greed index, pre-market/after-hours moves) require live web retrieval.

**Context from vault:** The most recent trade reference in the vault (LSN-2026-07-19) mentions AMD at ~$159.80 on July 15, indicating the market was in a period of earnings-driven volatility. The Phase 1B validation results show QQQ was trading at ~518-522 in May 2025 (period3_current), and IWM at ~218 in October 2024. These are historical, not current.

**Cached data available:** Parquet files exist at `~/.hermes/market_data/` for SPY, QQQ, IWM, and 89 other tickers. These could provide the last cached close prices if read programmatically.

---

## 2. Macro & Catalyst Watch

**Data unavailable — web search tools not available.** Required data points (Fed/interest rate news, economic data releases, geopolitical events, earnings calendar) require live web retrieval.

**From vault context:**
- The latest lesson (LSN-2026-07-19) references an AMD earnings guidance revision as a catalyst that overrode a technical setup. This suggests earnings season is active.
- Today is Monday, July 20, 2026 — a new trading week begins. Weekend news flow and Monday morning macro context is critical.

**Cron schedule note:** The CRON-001-Market-Intelligence job is configured for weekdays at 13:00 UTC (9:00 AM ET), which is appropriate for pre-market / early-session context.

---

## 3. Crypto Snapshot

**Data unavailable — web search tools not available.** Required data (BTC/ETH current prices, 24h % change, BTC dominance, crypto-specific news) requires live web retrieval.

**Cached data available:** Parquet files exist at `~/.hermes/market_data/crypto/` for BTC, ETH, and SOL. These were last fetched from Hyperliquid's API (crypto data is set to refresh if cache is >1 day old, per `fetch_crypto_data.py`).

---

## 4. Swing Trading Opportunities

**Sector / Theme Observations (from vault knowledge):**

- **Volume-Confirmed Breakouts:** The vault's most recent high-actionability insight (INS-2026-07-19, actionability: 4/5) describes a two-stage volume test for flag/pennant breakouts — requiring volume contraction during consolidation AND a volume surge at breakout. This is an active filter to apply to any breakout setups this week.

- **Support/Resistance Role-Reversal (AMD example):** Lesson LSN-2026-07-19 documents a failed short on AMD at $159.80 where an earnings catalyst overrode the technical role-reversal setup. This flags the risk of holding earnings-sensitive positions through catalyst events.

- **Sectors to Watch (from scanner universe):** The HermesForge universe covers mega-cap tech (AAPL, MSFT, NVDA, META, AMZN), financials (JPM, GS, BAC), energy (XOM, CVX, COP), and healthcare (LLY, UNH, JNJ). Any of these sectors showing momentum would be relevant.

**Data unavailable — live sector momentum scans and technical setups require web search or cached data analysis.**

---

## 5. Risk Flags

1. **Earnings Season Active:** The AMD lesson (LSN-2026-07-19) explicitly documents earnings guidance as a catalyst that overrode a technical setup. Check which large-cap names report this week before entering swing trades.

2. **Monday Session:** First trading day of the week often sees weekend news gap risk. Position traders should be aware of potential gap opens from weekend geopolitical or macro developments.

3. **Data Gap on This Briefing:** This is the first run of CRON-001. The web search toolset was not available in this session, meaning live market data could not be gathered. **This should be resolved before the next scheduled run (2026-07-21 13:00 UTC).** Review the cron job's `enabled_toolsets` configuration to ensure `web` toolset is properly loaded.

---

## Next Run

- **Scheduled:** 2026-07-21 13:00 UTC (weekdays only)
- **Model:** google/gemini-2.0-flash-001 (T3)
- **Action Required:** Verify web search tool availability before next run. The `enabled_toolsets: ["web", "file"]` is configured in the cron job but web tools were not accessible in this session.