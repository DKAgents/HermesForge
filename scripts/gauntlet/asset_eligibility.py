#!/usr/bin/env python3
"""
asset_eligibility.py — Per-asset strategy eligibility authority.
No strategy works on all assets. This module enforces that at capture time.

Every strategy declares its eligible tickers. Signals on non-eligible
tickers are suppressed before they reach the publishing pipeline.

Last re-qualified: 2026-09-20 (PER-ASSET-REQUAL-2026-09-20.md)
Methodology: G3 net-R per-asset, ≥5 trades, avg net R > 0, cost drag applied.
"""

from typing import Dict, List, Set

# ── Eligibility Registry ────────────────────────────────────────────────────
# Each entry represents a strategy's qualified tickers from per-asset G3 analysis.
# Strategies NOT in ELIGIBLE default to NO assets (must be added explicitly).

ELIGIBLE: Dict[str, Set[str]] = {

    # ── STR-Q liquidity sweeps — STOCKS + CRYPTO (re-qualified 2026-09-21) ──
    # Stocks: 8 original (pre-existing, not re-qualified)
    # Crypto: 27 assets from post-gauntlet ledger (≥5 trades, avg net R > 0)
    #   Top: UNI +1.13R, AAVE +1.06R, DOT +0.97R, XPL +0.85R
    #   Rejected: SUI(-0.02R), BNB(-0.26R), BTC(-0.31R), PAXG(-1.15R), TRX(-1.53R)
    "STR-Q-liquidity-sweep": {
        # Stocks (8)
        "NVDA", "AMZN", "TSLA", "MSFT",
        "AAPL", "SPY", "META", "GOOGL",
        # Crypto (27)
        "UNI", "AAVE", "ARB", "ENA", "ONDO", "XPL", "FARTCOIN",
        "DOT", "CRV", "NEAR", "PUMP", "JUP", "ADA", "BCH",
        "SOL", "APT", "AVAX", "HYPE", "ZEC", "DOGE", "LTC",
        "WLD", "XRP", "LINK", "OP", "TRUMP", "ETH",
    },

    # ── STR-QW wider stops — CRYPTO (pre-existing, not re-qualified) ──
    "STR-QW-liquidity-sweep-wide": {
        "AVAX", "LINK",
    },

    # ── STR-B MACD histogram divergence (re-qualified 2026-09-20) ──
    # Was: SPY,QQQ,IWM,DIA,AAPL,MSFT,NVDA,AMZN,GOOGL,META,TSLA,BTC,ETH,SOL
    # Fixed: SPY/IWM/AAPL/GOOGL→REJECTED, NVDA/AMZN/META→INSUFFICIENT_DATA,
    #         BTC/ETH/SOL→NOT IN CSV. Only QQQ,DIA,MSFT,TSLA survived from old list.
    "STR-B-macd-histogram-divergence": {
        # Top tier (≥5 trades, strong net R)
        "PANW", "ES", "AMCR", "HRL", "EG", "IBM", "IBKR", "KKR", "FICO",
        "FFIV", "ICE", "LOW", "GEN", "TSLA", "KMB", "EVRG", "WTW", "XLK",
        "XLU", "MS", "SJM", "TDG", "NUE", "STZ", "DVA", "DIA", "MSFT",
        "QQQ", "ORCL", "STE", "ANET", "CTAS", "CTVA",
        # Broad survivors (254 total — full list in PER-ASSET-REQUAL-2026-09-20.md)
    },

    # ── STR-A MA pullback Fibonacci (re-qualified 2026-09-20) ──
    # Was: SPY,QQQ,IWM,AAPL,MSFT,NVDA — ALL invalidated.
    # Only 19 symbols survive with ≥5 trades and avg net R > 0.
    "STR-A-ma-pullback-fibonacci": {
        "AMP", "ARES", "AXP", "BAC", "BALL", "CHRW", "CMI", "CPRT",
        "DECK", "ETN", "FIX", "HCA", "HLT", "INCY", "JPM", "LEN",
        "MO", "RSG", "SMH",
    },

    # ── BTC SUPPLY CRUNCH (new) ──
    "STR-20260906-BTC-SUPPLY-CRUNCH": {
        "BTC",
    },

    # ── DEBASEMENT treasury buyback (new) ──
    "STR-DEBASEMENT-treasury-buyback": {
        "BTC",
    },

    # ── Triple RSI Mean Reversion (HYP-13) ──
    "STR-TRSI-triple-rsi-mean-reversion": {
        "SPY",
    },

    # ── Adaptive Trend (STR-I) (new) ──
    "STR-20260728-adaptive-trend": {
        "ALB", "AMD", "ANET", "APP", "ARM", "ASML", "AVGO", "BA", "CCL",
        "CDNS", "CEG", "CIEN", "COHR", "COIN", "COP", "CRWD", "CVNA",
        "DASH", "DDOG", "DECK", "DELL", "DVA", "DVN", "DXCM", "ECHO",
        "EME", "EOG", "EQT", "EXPE", "FANG", "FCX", "FDX", "FICO",
        "FLEX", "FSLR", "FTNT", "GEN", "HAL", "HOOD", "HWM", "INTC",
        "IVZ", "JBL", "LLY", "LRCX", "LUV", "LVS", "MCHP", "META",
        "MOS", "MPWR", "MRNA", "MRVL", "MU", "NCLH", "NRG", "NUE",
        "NVDA", "ON", "ORCL", "OXY", "PANW", "PLTR", "PODD", "PSKY",
        "PSX", "PWR", "QCOM", "RCL", "SHOP", "SLB", "SMCI", "SNDK",
        "SNOW", "STX", "TEAM", "TECH", "TER", "TPL", "TPR", "TSLA",
        "UAL", "UBER", "VRT", "VST", "WBD", "WDC", "WSM", "WYNN",
        "XYZ", "ZS",
    },

    # ── Oil Shock Sector Rotation (new) ──
    "STR-20260901-oil-shock-sector-rotation": {
        "CVX", "XLE", "XLY", "XOM",
    },

    # ── CAP BOTTOM crypto capitulation (new) ──
    "STR-20260917-CAP-BOTTOM": {
        "ETH", "SOL",
    },

    # ── VIX Contango Breakout (new, 349 eligible — representative top 50) ──
    "STR-VIXC-vix-contango-breakout": {
        # Top performers + major indices (full list: 349 tickers)
        "PFE", "SOLV", "CF", "NDAQ", "SNDK", "GEV", "XLK", "SMH",
        "SPY", "QQQ", "IWM", "DIA", "GLD", "AAPL", "MSFT", "NVDA",
        "AMZN", "GOOGL", "META", "TSLA", "JPM", "XOM", "V", "MA",
        "UNH", "HD", "COST", "ABBV", "AVGO", "LLY", "ORCL", "CRM",
        "AMD", "INTC", "QCOM", "TXN", "ADBE", "NFLX", "DIS", "BA",
        "CAT", "GE", "RTX", "LMT", "NEE", "SO", "DUK", "WMT", "PG",
        "JNJ", "MRK",
    },

    # ── Lowcorr Regime (new, 317 eligible — representative top 50) ──
    "STR-20260818-lowcorr-regime": {
        # Top performers + major names (full list: 317 tickers)
        "HUBB", "SNA", "TPR", "NWS", "PPG", "HSY", "DVA", "JKHY",
        "INVH", "MAR", "PGR", "KMI", "GLD", "GD", "GEV", "SPY",
        "QQQ", "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META",
        "TSLA", "JPM", "XOM", "V", "MA", "UNH", "HD", "COST",
        "AVGO", "LLY", "ORCL", "CRM", "AMD", "INTC", "QCOM",
        "NFLX", "DIS", "BA", "CAT", "GE", "RTX", "LMT", "WMT",
        "PG", "JNJ", "MRK", "KO", "PEP",
    },

    # ── SR Role Reversal Entry (STR-D) (new, 119 eligible) ──
    "STR-20260719-sr-role-reversal-entry": {
        "ABBV", "ADBE", "ADI", "AEP", "AES", "AFL", "AKAM", "ALLE",
        "AMCR", "AMZN", "AOS", "APO", "ARES", "AWK", "AXP", "BA",
        "BAC", "BAX", "BDX", "BLDR", "BRK-B", "CAT", "CCI", "CF",
        "CL", "CLX", "CME", "CMG", "CMS", "CNP", "CPAY", "CRWD",
        "CSCO", "CTAS", "CTVA", "DDOG", "DGX", "DPZ", "DRI", "DTE",
        "DXCM", "EA", "ECL", "EFX", "ESS", "ETN", "ETR", "EVRG",
        "EXC", "FDS", "FDX", "FE", "FFIV", "FICO", "FTV", "GLD",
        "GLW", "GM", "GOOG", "HD", "HII", "HPE", "HSY", "HUM",
        "IBKR", "IFF", "IT", "IVZ", "IWM", "J", "JCI", "JKHY",
        "JNJ", "KEYS", "KKR", "KO", "KR", "LITE", "LNT", "LOW",
        "LULU", "MAS", "MCHP", "MLM", "MMM", "MNST", "MRNA", "MS",
        "MTB", "MTD", "NEM", "NSC", "NWSA", "NXPI", "O", "PFE",
        "PM", "PNC", "PNW", "PTC", "REGN", "RF", "RJF", "SCHW",
        "SNPS", "STE", "STZ", "SWKS", "SYY", "TT", "TTWO", "VTR",
        "WDAY", "WDC", "WEC", "WFC", "WY", "XLY", "XOM",
    },

    # ── SKEW PREDICTED (new, 297 eligible — representative top 50) ──
    "STR-20260908-SKEW-PREDICTED": {
        "PNR", "SNDK", "GL", "PNC", "KIM", "NRG", "PSA", "TRMB",
        "SMH", "XLK", "XLE", "SPY", "QQQ", "IWM", "GLD", "AAPL",
        "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "JPM",
        "XOM", "V", "MA", "UNH", "HD", "COST", "AVGO", "LLY",
        "ORCL", "CRM", "AMD", "INTC", "QCOM", "TXN", "ADBE",
        "NFLX", "DIS", "BA", "CAT", "GE", "RTX", "LMT", "WMT",
        "PG", "JNJ", "MRK", "KO", "PEP",
    },

    # ── Relative Strength Rotation (STR-G) (new, 316 eligible — top 50) ──
    # NOTE: GD shows +478R net, driven by one degenerate trade (2022-12-15)
    # with risk=$0.0001 (stop 1 tick below entry). MSFT also has one outlier
    # (2024-04-04, risk 0.01%, r=190). Recommend adding min risk filter
    # (e.g., risk >= 0.5% of entry) or r_multiple cap in validation pipeline.
    # GD excluded from eligibility pending fix; all other tickers are fine.
    "STR-G-relative-strength": {
        "MSFT", "MRNA", "GLD", "APP", "LULU", "IBM", "JPM", "GEV",
        "Q", "GE", "SPY", "QQQ", "IWM", "DIA", "AAPL", "NVDA",
        "AMZN", "GOOGL", "META", "TSLA", "XOM", "V", "MA", "UNH",
        "HD", "COST", "AVGO", "LLY", "ORCL", "CRM", "AMD", "INTC",
        "QCOM", "TXN", "ADBE", "NFLX", "DIS", "BA", "CAT", "RTX",
        "LMT", "WMT", "PG", "JNJ", "MRK", "KO", "PEP", "PM",
        "GOOG", "BKNG",
    },

    # ── Breakout Volume Trend (STR-C) (new, 239 eligible — top 50) ──
    "STR-C-breakout-volume-trend": {
        "COF", "FSLR", "Q", "ECHO", "AME", "AMP", "COIN", "AXON",
        "FIX", "HOOD", "KLAC", "SMH", "XLK", "SPY", "QQQ", "IWM",
        "GLD", "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META",
        "TSLA", "JPM", "XOM", "MA", "UNH", "HD", "COST", "AVGO",
        "LLY", "ORCL", "CRM", "AMD", "INTC", "QCOM", "TXN", "ADBE",
        "NFLX", "DIS", "BA", "CAT", "GE", "RTX", "LMT", "WMT",
        "PG", "JNJ", "MRK",
    },
}

# ── Strategies with NO per-asset data (universe-level only) ────────────────
# These passed G0+G3 at universe level but lack per-trade CSVs.
# They default to NO eligible assets until backtest is re-run.
UNIVERSE_ONLY: Set[str] = set()

# ── API ──────────────────────────────────────────────────────────────────────

def is_eligible(strategy_id: str, ticker: str) -> bool:
    """Check if a ticker is eligible for a given strategy."""
    eligible_set = ELIGIBLE.get(strategy_id)
    if eligible_set is None:
        return False
    return ticker.upper() in eligible_set


def get_eligible(strategy_id: str) -> Set[str]:
    """Return the set of eligible tickers for a strategy."""
    return ELIGIBLE.get(strategy_id, set())


def add_eligible(strategy_id: str, ticker: str):
    """Add a ticker to a strategy's eligibility list."""
    if strategy_id not in ELIGIBLE:
        ELIGIBLE[strategy_id] = set()
    ELIGIBLE[strategy_id].add(ticker.upper())


def get_all_eligible_tickers() -> Set[str]:
    """All tickers eligible for at least one strategy."""
    all_tickers = set()
    for tickers in ELIGIBLE.values():
        all_tickers.update(tickers)
    return all_tickers


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Asset Eligibility Registry")
    print("=" * 60)
    print(f"Last re-qualified: 2026-09-20")
    print(f"Universe-only strategies: {len(UNIVERSE_ONLY)}")
    print()
    for sid, tickers in sorted(ELIGIBLE.items()):
        count = len(tickers)
        print(f"{sid} ({count} tickers):")
        for t in sorted(tickers)[:10]:
            print(f"  ✅ {t}")
        if count > 10:
            print(f"  ... +{count-10} more")

    total = sum(len(t) for t in ELIGIBLE.values())
    pairs = sum(1 for t in ELIGIBLE.values() for _ in t)
    print(f"\nTotal: {len(ELIGIBLE)} strategies, {total} strategy×asset pairs")