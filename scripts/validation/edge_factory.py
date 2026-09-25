#!/usr/bin/env python3
"""
Edge Factory — high-frequency trading thesis discovery via X crawl + backtest.

Runs every 4 hours. Crawls X for trading strategies, extracts rules,
backtests against cached OHLCV data, and ranks viable edges.

Generates 10+ new testable theses per day (3+ per 4h cycle).
"""
import json, os, re, subprocess, sys, time, csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from collections import defaultdict
import urllib.request

PROJECT_ROOT = Path("/root/HermesForge")
CACHE_DIR = Path("/root/.hermes/market_data")
HYP_DIR = PROJECT_ROOT / "06-Strategies" / "Hypotheses"
RESULTS_DIR = PROJECT_ROOT / "04-ForgeLoop" / "edge-factory-results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ── X Search Queries (rotated per cycle to maximize diversity) ────────────
SEARCH_QUERIES_ALL = [
    "profitable trading strategy setup rules entry stop target",
    "backtest results win rate sharpe ratio strategy",
    "ICT FVG entry model order block strategy",
    "SMC breaker block mitigation strategy rules",
    "supply demand zone strategy rules entry criteria",
    "RSI divergence MACD crossover strategy results",
    "volume profile VWAP trading strategy setup",
    "orderflow footprint delta divergence strategy",
    "market structure shift CHoCH strategy rules",
    "liquidity sweep inducement strategy setup",
    "fair value gap inversion strategy rules",
    "swing failure pattern SFP strategy results",
    "turtle soup pattern strategy rules",
    "wyckoff accumulation distribution strategy setup",
    "Elliott wave impulse correction strategy rules",
    "harmonic pattern gartley bat crab strategy",
    "open interest volume divergence strategy crypto",
    "funding rate cascade liquidation strategy crypto",
    "momentum breakout retest strategy rules",
    "mean reversion Bollinger band strategy setup",
    "gap fill strategy overnight gap rules",
    "opening range breakout ORB strategy rules",
    "initial balance high low strategy setup",
    "value area high low VAH VAL strategy rules",
    "market profile POC strategy setup",
]

# Rotate queries: use 5-8 per cycle based on cycle index
def get_cycle_queries(cycle_index: int) -> list:
    """Get queries for this cycle, rotated from master list."""
    queries_per_cycle = 7
    start = (cycle_index * queries_per_cycle) % len(SEARCH_QUERIES_ALL)
    queries = []
    for i in range(queries_per_cycle):
        idx = (start + i) % len(SEARCH_QUERIES_ALL)
        queries.append(SEARCH_QUERIES_ALL[idx])
    return queries


# ── Search X via web search (no X API needed) ─────────────────────────────
def search_x(query: str, max_results: int = 8) -> list[dict]:
    """Search X/Twitter via web. Returns list of {title, url, snippet}."""
    try:
        encoded = urllib.parse.quote(f"site:twitter.com OR site:x.com {query}")
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html = r.read().decode()
        
        results = []
        # Parse DuckDuckGo HTML results
        for match in re.finditer(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
            html, re.DOTALL
        ):
            url = match.group(1)
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            snippet = re.sub(r'<[^>]+>', '', match.group(3)).strip()
            if 'twitter.com' in url or 'x.com' in url:
                results.append({"title": title, "url": url, "snippet": snippet})
            if len(results) >= max_results:
                break
        return results
    except Exception as e:
        print(f"    Search error: {e}")
        return []


# ── Rule Extraction ─────────────────────────────────────────────────────
def extract_trading_rules(snippet: str) -> Optional[dict]:
    """Extract testable trading rules from text snippet."""
    rules = {
        "direction": "long",
        "entry_conditions": [],
        "stop_conditions": [],
        "target_conditions": [],
        "indicators": [],
        "timeframe": "daily",
        "confidence": 0,
    }
    
    text = snippet.lower()
    
    # Direction
    if any(w in text for w in ["short", "sell", "bearish", "put"]):
        rules["direction"] = "short"
    
    # Entry conditions
    entry_patterns = [
        (r"rsi\s*(?:below|under|<\s*)\s*(\d+)", "RSI oversold"),
        (r"rsi\s*(?:above|over|>\s*)\s*(\d+)", "RSI overbought"),
        (r"macd\s*cross", "MACD crossover"),
        (r"ema\s*(\d+)\s*cross", "EMA crossover"),
        (r"sma\s*(\d+)\s*cross", "SMA crossover"),
        (r"bounce\s*(?:off|from)", "Support/resistance bounce"),
        (r"break\s*(?:out|above|below)", "Breakout"),
        (r"pullback\s*(?:to|toward)", "Pullback"),
        (r"retest\s*(?:of|at)", "Retest"),
        (r"fvg|fair\s*value\s*gap", "Fair Value Gap"),
        (r"order\s*block|ob", "Order Block"),
        (r"breaker\s*block", "Breaker Block"),
        (r"liquidity\s*(?:sweep|grab)", "Liquidity Sweep"),
        (r"inducement|induce", "Inducement"),
    ]
    
    for pattern, label in entry_patterns:
        if re.search(pattern, text):
            rules["entry_conditions"].append(label)
    
    # Indicators
    if "rsi" in text: rules["indicators"].append("RSI")
    if "macd" in text: rules["indicators"].append("MACD")
    if "ema" in text: rules["indicators"].append("EMA")
    if "sma" in text: rules["indicators"].append("SMA")
    if "volume" in text: rules["indicators"].append("Volume")
    if "atr" in text: rules["indicators"].append("ATR")
    if "bollinger" in text: rules["indicators"].append("Bollinger")
    if "vwap" in text: rules["indicators"].append("VWAP")
    
    # Stop conditions
    if "atr" in text:
        rules["stop_conditions"].append("ATR-based stop")
    if any(w in text for w in ["swing low", "swing high"]):
        rules["stop_conditions"].append("Swing level stop")
    if "structure" in text:
        rules["stop_conditions"].append("Structure-based stop")
    
    # Target conditions
    if re.search(r"(\d+):1\s*(?:rr|risk.*reward)", text):
        rules["target_conditions"].append("Fixed R:R target")
    if "swing high" in text or "resistance" in text:
        rules["target_conditions"].append("Swing level target")
    
    # Timeframe
    for tf in ["1m", "5m", "15m", "1h", "4h", "daily", "weekly"]:
        if tf in text:
            rules["timeframe"] = tf
            break
    
    # Confidence — based on how many concrete rules extracted
    rules["confidence"] = min(
        len(rules["entry_conditions"]) * 15 +
        len(rules["indicators"]) * 5 +
        len(rules["stop_conditions"]) * 10 +
        len(rules["target_conditions"]) * 10,
        100
    )
    
    if rules["confidence"] < 30:
        return None
    
    return rules


# ── Quick Backtest ───────────────────────────────────────────────────────
def quick_backtest(rules: dict, ticker: str = "BTC") -> dict:
    """Run a quick backtest against cached data."""
    try:
        # Load cached data
        data_file = CACHE_DIR / f"{ticker}_1d.csv"
        if not data_file.exists():
            # Try crypto cache
            data_file = CACHE_DIR / f"{ticker}.csv"
        if not data_file.exists():
            return {"error": f"No cached data for {ticker}"}
        
        df = None
        import pandas as pd
        df = pd.read_csv(data_file, index_col=0, parse_dates=True)
        
        if len(df) < 100:
            return {"error": f"Insufficient data for {ticker}: {len(df)} bars"}
        
        # Simple signal detection based on extracted rules
        signals = []
        close = df["close"].values
        high = df["high"].values
        low = df["low"].values
        
        for i in range(50, len(close) - 1):
            entry_triggered = False
            
            # Check entry conditions
            if "RSI oversold" in rules["entry_conditions"]:
                # Approximate RSI oversold
                delta = close[i] - close[i-1]
                gain = max(delta, 0)
                loss = max(-delta, 0)
                if loss > gain * 3:  # rough oversold
                    entry_triggered = True
            
            if "RSI overbought" in rules["entry_conditions"]:
                delta = close[i] - close[i-1]
                gain = max(delta, 0)
                loss = max(-delta, 0)
                if gain > loss * 3:
                    entry_triggered = True
            
            if "MACD crossover" in rules["entry_conditions"]:
                ema12 = pd.Series(close[:i+1]).ewm(span=12).mean().iloc[-1]
                ema26 = pd.Series(close[:i+1]).ewm(span=26).mean().iloc[-1]
                prev_ema12 = pd.Series(close[:i]).ewm(span=12).mean().iloc[-1]
                prev_ema26 = pd.Series(close[:i]).ewm(span=26).mean().iloc[-1]
                if (prev_ema12 < prev_ema26 and ema12 > ema26) or \
                   (prev_ema12 > prev_ema26 and ema12 < ema26):
                    entry_triggered = True
            
            if "Breakout" in rules["entry_conditions"]:
                lookback = 20
                if close[i] > max(high[i-lookback:i]):
                    entry_triggered = True
            
            if "Support/resistance bounce" in rules["entry_conditions"]:
                lookback = 20
                if close[i] > min(low[i-lookback:i]) * 1.01 and \
                   low[i] <= min(low[i-lookback:i]) * 1.005:
                    entry_triggered = True
            
            if not entry_triggered:
                continue
            
            # Simple stop: 2% below entry (or based on ATR)
            stop_pct = 0.02
            if "ATR" in rules.get("indicators", []):
                atr = pd.Series(
                    pd.DataFrame({"h": high[:i+1], "l": low[:i+1], "c": close[:i+1]})
                    .apply(lambda x: max(x["h"]-x["l"], abs(x["h"]-close[i-1]), abs(x["l"]-close[i-1])), axis=1)
                ).rolling(14).mean().iloc[-1]
                if atr > 0:
                    stop_pct = min(atr / close[i], 0.05)
            
            entry = close[i]
            stop = entry * (1 - stop_pct) if rules["direction"] == "long" else entry * (1 + stop_pct)
            target = entry * (1 + stop_pct * 3) if rules["direction"] == "long" else entry * (1 - stop_pct * 3)
            
            # Simulate exit
            for j in range(i+1, min(i+21, len(close))):
                if rules["direction"] == "long":
                    if low[j] <= stop:
                        r = (stop - entry) / abs(entry - stop)
                        signals.append({"entry_date": str(df.index[i])[:10], "exit_date": str(df.index[j])[:10], "r": r, "exit": "stop"})
                        break
                    elif high[j] >= target:
                        r = (target - entry) / abs(entry - stop)
                        signals.append({"entry_date": str(df.index[i])[:10], "exit_date": str(df.index[j])[:10], "r": r, "exit": "target"})
                        break
                else:
                    if high[j] >= stop:
                        r = (stop - entry) / abs(entry - stop)
                        signals.append({"entry_date": str(df.index[i])[:10], "exit_date": str(df.index[j])[:10], "r": r, "exit": "stop"})
                        break
                    elif low[j] <= target:
                        r = (target - entry) / abs(entry - stop)
                        signals.append({"entry_date": str(df.index[i])[:10], "exit_date": str(df.index[j])[:10], "r": r, "exit": "target"})
                        break
                if j == min(i+20, len(close)-1):
                    r = (close[j] - entry) / abs(entry - stop) if rules["direction"] == "long" else (entry - close[j]) / abs(entry - stop)
                    signals.append({"entry_date": str(df.index[i])[:10], "exit_date": str(df.index[j])[:10], "r": r, "exit": "time"})
        
        if not signals:
            return {"error": "No signals generated", "signals": 0, "mean_r": 0, "win_rate": 0}
        
        n = len(signals)
        wins = sum(1 for s in signals if s["r"] > 0)
        mean_r = sum(s["r"] for s in signals) / n
        max_r = max(s["r"] for s in signals)
        min_r = min(s["r"] for s in signals)
        
        return {
            "signals": n,
            "win_rate": round(wins / n * 100, 1),
            "mean_r": round(mean_r, 3),
            "max_r": round(max_r, 2),
            "min_r": round(min_r, 2),
            "total_r": round(sum(s["r"] for s in signals), 1),
        }
    except Exception as e:
        return {"error": str(e)}


# ── Main Pipeline ────────────────────────────────────────────────────────
def run_edge_factory(cycle_index: int = 0) -> dict:
    """Run one cycle of edge discovery."""
    print(f"🏭 Edge Factory — Cycle {cycle_index}")
    print(f"   Time: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    queries = get_cycle_queries(cycle_index)
    print(f"   Queries: {len(queries)}")
    
    all_candidates = []
    seen_urls = set()
    
    for query in queries:
        print(f"  Searching: {query[:60]}...")
        results = search_x(query, max_results=6)
        print(f"    → {len(results)} results")
        
        for r in results:
            if r["url"] in seen_urls:
                continue
            seen_urls.add(r["url"])
            
            rules = extract_trading_rules(r["snippet"])
            if not rules:
                continue
            
            rules["source_url"] = r["url"]
            rules["source_title"] = r["title"][:120]
            all_candidates.append(rules)
    
    print(f"\n  Candidates with extractable rules: {len(all_candidates)}")
    
    # Backtest top candidates (up to 5 per cycle to stay fast)
    backtested = []
    for rules in all_candidates[:5]:
        ticker = "BTC"  # Default, could be inferred from snippet
        bt = quick_backtest(rules, ticker)
        rules["backtest"] = bt
        backtested.append(rules)
        
        if "error" not in bt:
            print(f"  ✓ {rules['source_title'][:60]}: {bt['signals']} sigs, "
                  f"WR={bt['win_rate']}%, mean R={bt['mean_r']}")
        else:
            print(f"  ✗ {rules['source_title'][:60]}: {bt['error']}")
    
    # Rank by mean R * sqrt(signals)
    viable = [b for b in backtested if "error" not in b["backtest"] and b["backtest"]["signals"] >= 5]
    viable.sort(key=lambda x: x["backtest"]["mean_r"] * (x["backtest"]["signals"] ** 0.5), reverse=True)
    
    # Save results
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    result_file = RESULTS_DIR / f"cycle_{timestamp}.json"
    with open(result_file, "w") as f:
        json.dump({"cycle": cycle_index, "candidates": len(all_candidates),
                   "backtested": len(backtested), "viable": len(viable),
                   "results": [{"title": r["source_title"], "direction": r["direction"],
                                "confidence": r["confidence"], "backtest": r["backtest"]}
                              for r in viable]}, f, indent=2)
    
    return {
        "cycle": cycle_index,
        "candidates_found": len(all_candidates),
        "backtested": len(backtested),
        "viable_edges": len(viable),
        "top_edges": viable[:3],
        "result_file": str(result_file),
    }


if __name__ == "__main__":
    cycle = 0
    if len(sys.argv) > 1:
        try:
            cycle = int(sys.argv[1])
        except ValueError:
            pass
    
    summary = run_edge_factory(cycle)
    
    print(f"\n{'='*50}")
    print(f"Edge Factory Summary")
    print(f"{'='*50}")
    print(f"Candidates: {summary['candidates_found']}")
    print(f"Backtested: {summary['backtested']}")
    print(f"Viable edges: {summary['viable_edges']}")
    
    if summary["top_edges"]:
        print(f"\nTop Viable Edges:")
        for i, edge in enumerate(summary["top_edges"]):
            bt = edge["backtest"]
            print(f"  {i+1}. {edge['title'][:70]}")
            print(f"     Dir={edge['direction']}, Conf={edge['confidence']}%")
            print(f"     {bt['signals']} sigs, WR={bt['win_rate']}%, "
                  f"mean R={bt['mean_r']}, total R={bt['total_r']}")
    
    print(f"\n--- JSON ---")
    print(json.dumps(summary, indent=2, default=str))