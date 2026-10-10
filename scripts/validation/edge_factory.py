#!/usr/bin/env python3
"""
Edge Factory — high-frequency trading thesis discovery via X crawl + backtest.

Runs every 4 hours. Crawls X for trading strategies, extracts rules,
backtests against cached OHLCV data, and ranks viable edges.

Generates 10+ new testable theses per day (3+ per 4h cycle).
"""
import json, os, re, shutil, subprocess, sys, time, csv
import urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from collections import defaultdict

# Ensure nvm/node binaries on PATH for xurl (cron shells lack it)
_nvm_root = Path.home() / ".nvm" / "versions" / "node"
if _nvm_root.exists():
    for _v in sorted(_nvm_root.iterdir(), reverse=True):
        _bin = _v / "bin"
        if _bin.is_dir():
            os.environ["PATH"] = str(_bin) + ":" + os.environ.get("PATH", "")
            break

PROJECT_ROOT = Path("/root/HermesForge")
CACHE_DIR = Path("/root/.hermes/market_data")
HYP_DIR = PROJECT_ROOT / "trading/strategies" / "Hypotheses"
RESULTS_DIR = PROJECT_ROOT / "code" / "forge-loop" / "edge-factory-results"
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
    all_results = []
    
    # xurl search (direct X API, works, requires nvm PATH)
    try:
        results = _search_xurl(query, max_results)
        all_results.extend(results)
    except Exception:
        pass
    
    return all_results[:max_results]


# ── JEV Relevance Pre-Filter ────────────────────────────────────────────
_JEV_API_KEY = None

def _get_jev_client():
    """Lazy-load JevClient with API key from env."""
    global _JEV_API_KEY
    if _JEV_API_KEY is None:
        env_path = Path.home() / ".hermes" / ".env"
        _JEV_API_KEY = ""
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.strip().startswith("TYPESAFE_API_KEY="):
                    _JEV_API_KEY = line.strip().split("=", 1)[1].strip().strip('"').strip("'")
                    break
        if not _JEV_API_KEY:
            _JEV_API_KEY = os.environ.get("TYPESAFE_API_KEY", "")
    
    if not _JEV_API_KEY:
        return None
    
    gauntlet_path = str(PROJECT_ROOT / "scripts" / "gauntlet")
    if gauntlet_path not in sys.path:
        sys.path.insert(0, gauntlet_path)
    from jev_client import JevClient
    return JevClient(api_key=_JEV_API_KEY)


def jev_score_snippets(snippets: list[dict], min_relevance: float = 0.40) -> list[dict]:
    """Use JEV to score search result snippets for trading strategy relevance.
    
    Returns snippets with relevance >= min_relevance, sorted by score descending.
    On JEV failure, returns all snippets unfiltered (fail-open for discovery).
    """
    if not snippets:
        return []
    
    jev = _get_jev_client()
    if jev is None:
        return snippets  # No JEV available — pass through unfiltered
    
    scored = []
    for s in snippets:
        snippet = (s.get("snippet", "") or s.get("title", ""))[:500]
        if not snippet.strip():
            scored.append({**s, "jev_score": 0.0})
            continue
        
        try:
            result = jev.score(
                snippet,
                "Does this text describe a specific trading strategy with entry/exit rules?",
                ["no", "vaguely", "somewhat", "yes_clearly"]
            )
            score = result.get("score", 0) / 3.0  # Normalize 0-3 to 0.0-1.0
            scored.append({**s, "jev_score": round(score, 3)})
        except Exception:
            scored.append({**s, "jev_score": 0.5})  # Fail-open: keep it
    
    # Filter and sort
    relevant = [s for s in scored if s["jev_score"] >= min_relevance]
    relevant.sort(key=lambda x: x["jev_score"], reverse=True)
    
    return relevant if relevant else scored[:5]  # Fallback: top 5 unfiltered


def _search_xurl(query: str, max_results: int) -> list[dict]:
    """Search X/Twitter via xurl CLI (works, requires nvm PATH)."""
    import shutil
    xurl_path = shutil.which("xurl")
    if not xurl_path:
        # Try nvm path
        for p in Path.home().glob(".nvm/versions/node/*/bin/xurl"):
            xurl_path = str(p)
            break
    if not xurl_path:
        return []
    
    try:
        result = subprocess.run(
            [xurl_path, "search", query, "-n", str(max_results)],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            return []
        data = json.loads(result.stdout)
        tweets = data.get("data", data if isinstance(data, list) else [])
        if isinstance(tweets, dict):
            tweets = tweets.get("tweets", tweets.get("data", []))
        if not isinstance(tweets, list):
            return []
        
        results = []
        for t in tweets:
            if isinstance(t, dict):
                url = t.get("url", f"https://x.com/i/status/{t.get('id', '')}")
                text = t.get("text", t.get("full_text", ""))[:300]
                results.append({"title": text[:80], "url": url, "snippet": text})
            if len(results) >= max_results:
                break
        return results
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════════════════
# Multi-Source Discovery — Quantocracy, arXiv, GitHub, RSS feeds
# ═══════════════════════════════════════════════════════════════════════════

# ── RSS Feed Sources ─────────────────────────────────────────────────────
RSS_FEEDS = [
    ("Quantocracy", "https://quantocracy.com/feed/"),
    ("Quantifiable Edges", "https://quantifiableedges.com/feed/"),
    ("Robot Wealth", "https://robotwealth.com/feed/"),
    ("Newfound Research", "https://blog.thinknewfound.com/feed/"),
    ("Allocate Smartly", "https://allocatesmartly.com/feed/"),
    ("Macro Tourist", "https://macrotourist.com/feed/"),
    ("Factor Research", "https://www.factorresearch.com/feed/"),
    ("Epsilon Theory", "https://www.epsilontheory.com/feed/"),
]

def _fetch_rss_feed(name: str, url: str, max_items: int = 3) -> list[dict]:
    """Fetch RSS feed and extract titles + links + descriptions."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; HermesForge/1.0)'
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            xml_data = r.read()
        root = ET.fromstring(xml_data)
        results = []
        # Support both RSS 2.0 and Atom formats
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        for item in items[:max_items]:
            title = (item.findtext('title') or '').strip()
            link = (item.findtext('link') or item.findtext('{http://www.w3.org/2005/Atom}link') or '')
            desc = (item.findtext('description') or item.findtext('summary') or item.findtext('{http://www.w3.org/2005/Atom}summary') or '')
            if '{' in link:  # Atom link may be in href attribute
                import re as _re; m = _re.search(r'href="([^"]+)"', link)
                link = m.group(1) if m else link
            desc_text = re.sub(r'<[^>]+>', '', desc).strip()[:500]
            if link and (title or desc_text):
                results.append({
                    "title": f"[{name}] {title[:100]}",
                    "url": link,
                    "snippet": desc_text or title,
                    "source": name,
                })
        return results
    except Exception as e:
        return []


# ── arXiv q-fin Fetcher ──────────────────────────────────────────────────
ARXIV_QUERIES = [
    "quantitative trading strategy",
    "statistical arbitrage",
    "machine learning trading",
    "factor investing",
    "market microstructure strategy",
]

def _fetch_arxiv(query: str, max_results: int = 3) -> list[dict]:
    """Search arXiv q-fin for recent trading papers."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"http://export.arxiv.org/api/query?search_query=all:{encoded}+AND+cat:q-fin*&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        req = urllib.request.Request(url, headers={'User-Agent': 'HermesForge/1.0'})
        with urllib.request.urlopen(req, timeout=20) as r:
            xml_data = r.read()
        root = ET.fromstring(xml_data)
        results = []
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in root.findall('atom:entry', ns)[:max_results]:
            title = (entry.findtext('atom:title', '', ns) or '').strip()
            summary = (entry.findtext('atom:summary', '', ns) or '').strip()[:600]
            link = entry.find('atom:id', ns)
            url = link.text.strip() if link is not None and link.text else ''
            if url:
                results.append({
                    "title": f"[arXiv] {title[:100]}",
                    "url": url,
                    "snippet": summary,
                    "source": "arXiv",
                })
        return results
    except Exception:
        return []


# ── GitHub Code Search ───────────────────────────────────────────────────
GITHUB_QUERIES = [
    "strategy backtest python language:python pushed:>2026-01-01",
    "trading bot python backtest language:python pushed:>2026-01-01",
]

def _fetch_github(query: str, max_results: int = 3) -> list[dict]:
    """Search GitHub for executable trading strategy repos."""
    import urllib.request, urllib.parse
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.github.com/search/repositories?q={encoded}&sort=updated&order=desc&per_page={max_results}"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'HermesForge/1.0',
            'Accept': 'application/vnd.github.v3+json',
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        results = []
        for item in data.get('items', [])[:max_results]:
            results.append({
                "title": f"[GitHub] {item.get('full_name', '')}",
                "url": item.get('html_url', ''),
                "snippet": (item.get('description', '') or '')[:500],
                "source": "GitHub",
            })
        return results
    except Exception:
        return []


# ── Reddit r/algotrading ─────────────────────────────────────────────────
def _fetch_reddit(max_results: int = 3) -> list[dict]:
    """Fetch top posts from r/algotrading (JSON feed, no auth)."""
    import urllib.request
    try:
        url = "https://www.reddit.com/r/algotrading/top.json?t=week&limit=10"
        req = urllib.request.Request(url, headers={
            'User-Agent': 'HermesForge/1.0 (research bot)'
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        results = []
        for post in data.get('data', {}).get('children', [])[:max_results]:
            pdata = post.get('data', {})
            title = pdata.get('title', '')
            selftext = (pdata.get('selftext', '') or '')[:600]
            url = f"https://reddit.com{pdata.get('permalink', '')}"
            if title:
                results.append({
                    "title": f"[Reddit] {title[:100]}",
                    "url": url,
                    "snippet": selftext or title,
                    "source": "Reddit",
                })
        return results
    except Exception:
        return []


# ── Rule Extraction ─────────────────────────────────────────────────────
def extract_trading_rules(snippet: str) -> Optional[dict]:
    """Extract testable trading rules from text snippet.
    
    Handles multiple source types: tweets (keyword-dense), blog posts (narrative),
    academic papers (dense), GitHub repos (technical). Lower confidence floor
    to capture candidates from all sources.
    """
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
    if not text.strip():
        return None
    
    # ── Direction ─────────────────────────────────────────────────────
    short_signals = ["short", "sell", "bearish", "put", "downside", "decline"]
    long_signals = ["long", "buy", "bullish", "call", "upside", "rally", "uptrend"]
    short_count = sum(1 for w in short_signals if w in text)
    long_count = sum(1 for w in long_signals if w in text)
    if short_count > long_count:
        rules["direction"] = "short"
    
    # ── Entry conditions (tweet patterns + academic/blog patterns) ──────
    entry_patterns = [
        # Classic tweet patterns
        (r"rsi\s*(?:below|under|<\s*|cross.*under)\s*(\d+)", "RSI oversold"),
        (r"rsi\s*(?:above|over|>\s*|cross.*above)\s*(\d+)", "RSI overbought"),
        (r"macd\s*cross", "MACD crossover"),
        (r"ema\s*(\d+)\s*cross", "EMA crossover"),
        (r"sma\s*(\d+)\s*cross", "SMA crossover"),
        (r"moving\s*average\s*cross", "MA crossover"),
        (r"bounce\s*(?:off|from)", "Support/resistance bounce"),
        (r"break\s*(?:out|above|below|through)", "Breakout"),
        (r"pullback\s*(?:to|toward)", "Pullback"),
        (r"retest\s*(?:of|at)", "Retest"),
        (r"fvg|fair\s*value\s*gap", "Fair Value Gap"),
        (r"order\s*block|ob", "Order Block"),
        (r"breaker\s*block", "Breaker Block"),
        (r"liquidity\s*(?:sweep|grab)", "Liquidity Sweep"),
        (r"inducement|induce", "Inducement"),
        # Academic/blog patterns
        (r"momentum|trend.*follow", "Momentum / Trend following"),
        (r"mean.reversion|revert", "Mean reversion"),
        (r"volatility|vol\s|vix", "Volatility-based"),
        (r"carry\s*trade|roll\s*yield", "Carry trade"),
        (r"value\s*factor|value\s*invest", "Value factor"),
        (r"statistical\s*arbitrage|stat\s*arb", "Statistical arbitrage"),
        (r"pairs?\s*trad", "Pairs trade"),
        (r"regime\s*(?:switch|change|filter)", "Regime filter"),
        (r"seasonal|calendar|time.*day|day.*week", "Seasonal pattern"),
        (r"sentiment|fear.*greed", "Sentiment-based"),
    ]
    
    for pattern, label in entry_patterns:
        if re.search(pattern, text):
            rules["entry_conditions"].append(label)
    
    # ── Indicators ────────────────────────────────────────────────────
    indicator_map = {
        "rsi": "RSI", "macd": "MACD", "ema": "EMA", "sma": "SMA",
        "volume": "Volume", "atr": "ATR", "bollinger": "Bollinger",
        "vwap": "VWAP", "stochastic": "Stochastics", "adx": "ADX",
        "ichimoku": "Ichimoku", "obv": "OBV", "cci": "CCI",
        "supertrend": "SuperTrend", "pivot": "Pivot Points",
    }
    for keyword, label in indicator_map.items():
        if keyword in text:
            rules["indicators"].append(label)
    
    # ── Stop conditions ───────────────────────────────────────────────
    stop_signals = []
    if "atr" in text:
        stop_signals.append("ATR-based stop")
    if "trailing" in text and ("stop" in text or "exit" in text):
        stop_signals.append("Trailing stop")
    if any(w in text for w in ["swing low", "swing high", "recent low", "recent high"]):
        stop_signals.append("Swing level stop")
    if "structure" in text or "support" in text:
        stop_signals.append("Structure-based stop")
    if "time stop" in text or "max hold" in text or "time exit" in text:
        stop_signals.append("Time stop")
    if re.search(r"(\d+)%\s*stop", text):
        stop_signals.append("Percentage stop")
    rules["stop_conditions"] = stop_signals
    
    # ── Target conditions ─────────────────────────────────────────────
    target_signals = []
    if re.search(r"(\d+):1\s*(?:rr|risk.*reward)", text):
        target_signals.append("Fixed R:R target")
    if "swing high" in text or "resistance" in text or "prior high" in text:
        target_signals.append("Swing level target")
    if "take profit" in text or "profit target" in text:
        target_signals.append("Take profit level")
    if "trailing" in text and "target" in text:
        target_signals.append("Trailing target")
    rules["target_conditions"] = target_signals
    
    # ── Timeframe ─────────────────────────────────────────────────────
    tf_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h",
              "4h": "4h", "daily": "daily", "weekly": "weekly", "monthly": "monthly",
              "intraday": "intraday", "eod": "daily", "end of day": "daily"}
    for keyword, tf in tf_map.items():
        if keyword in text:
            rules["timeframe"] = tf
            break
    
    # ── Confidence — generous scoring to capture multi-source candidates ──
    # Base score from concrete rules found
    rules["confidence"] = min(
        len(rules["entry_conditions"]) * 12 +
        len(rules["indicators"]) * 4 +
        len(rules["stop_conditions"]) * 8 +
        len(rules["target_conditions"]) * 8,
        100
    )
    
    # Bonus: if text contains strategy/edge language, bump baseline
    strategy_keywords = ["strategy", "edge", "alpha", "factor", "signal",
                         "trade", "backtest", "sharpe", "profit factor",
                         "outperform", "predict", "portfolio", "allocation"]
    if any(w in text for w in strategy_keywords):
        rules["confidence"] = max(rules["confidence"], 10)
    
    # Bonus: if indicators present but no entry rules, still keep it
    if len(rules["indicators"]) >= 2 and len(rules["entry_conditions"]) == 0:
        rules["entry_conditions"].append("Indicator-based entry")
        rules["confidence"] = max(rules["confidence"], 12)
    
    # Floor lowered for multi-source: capture blog/paper/repo text
    if rules["confidence"] < 15:
        return None
    
    return rules


# ── Quick Backtest ───────────────────────────────────────────────────────
def quick_backtest(rules: dict, ticker: str = "BTC") -> dict:
    """Run a quick backtest against cached data."""
    try:
        # Load cached data — try multiple formats
        import pandas as pd
        df = None
        for candidate in [
            CACHE_DIR / f"{ticker}_1d.csv",
            CACHE_DIR / f"{ticker}.csv",
            CACHE_DIR / f"{ticker}_1d.parquet",
            CACHE_DIR / f"{ticker}.parquet",
            CACHE_DIR / f"{ticker}_5m_hyperliquid.parquet",
            CACHE_DIR / f"{ticker}_5m_alpaca.parquet",
        ]:
            if candidate.exists():
                if candidate.suffix == '.parquet':
                    df = pd.read_parquet(candidate)
                    # Set timestamp as index if present
                    if 'timestamp' in df.columns:
                        df = df.set_index('timestamp')
                        df.index = pd.to_datetime(df.index)
                else:
                    df = pd.read_csv(candidate, index_col=0, parse_dates=True)
                break
        
        if df is None:
            return {"error": f"No cached data for {ticker}"}
        
        if len(df) < 100:
            return {"error": f"Insufficient data for {ticker}: {len(df)} bars"}
        
        # Simple signal detection based on extracted rules
        signals = []
        close = df["close"].values
        high = df["high"].values
        low = df["low"].values
        
        for i in range(50, len(close) - 1):
            entry_triggered = False
            
            # ── Precompute common indicators for this bar ─────────────
            def _ema(series, span):
                return pd.Series(series[:i+1]).ewm(span=span).mean().iloc[-1]
            def _sma(series, period):
                return pd.Series(series[:i+1]).rolling(period).mean().iloc[-1]
            
            # ── RSI-based patterns ──────────────────────────────────
            if "RSI oversold" in rules["entry_conditions"] or \
               "Mean reversion" in str(rules["entry_conditions"]):
                delta = close[i] - close[i-1]
                gain = max(delta, 0)
                loss = max(-delta, 0)
                if loss > gain * 3:  # rough oversold approximation
                    entry_triggered = True
            
            if "RSI overbought" in rules["entry_conditions"]:
                delta = close[i] - close[i-1]
                gain = max(delta, 0)
                loss = max(-delta, 0)
                if gain > loss * 3:
                    entry_triggered = True
            
            # ── MA crossover patterns ───────────────────────────────
            if any(p in str(rules["entry_conditions"]) for p in
                   ["MACD crossover", "MA crossover", "EMA crossover", "SMA crossover",
                    "Momentum", "Indicator-based entry"]):
                ema12 = _ema(close, 12)
                ema26 = _ema(close, 26)
                prev_ema12 = _ema(close[:i], 12)
                prev_ema26 = _ema(close[:i], 26)
                if (prev_ema12 < prev_ema26 and ema12 > ema26):
                    if rules["direction"] == "long":
                        entry_triggered = True
                elif (prev_ema12 > prev_ema26 and ema12 < ema26):
                    if rules["direction"] == "short":
                        entry_triggered = True
            
            # ── Breakout patterns ───────────────────────────────────
            if "Breakout" in rules["entry_conditions"] or \
               "Momentum" in str(rules["entry_conditions"]):
                lookback = 20
                if rules["direction"] == "long" and close[i] > max(high[i-lookback:i]):
                    entry_triggered = True
                elif rules["direction"] == "short" and close[i] < min(low[i-lookback:i]):
                    entry_triggered = True
            
            # ── Pullback / Support bounce ───────────────────────────
            if any(p in str(rules["entry_conditions"]) for p in
                   ["Support/resistance bounce", "Pullback"]):
                lookback = 20
                if rules["direction"] == "long":
                    if close[i] > min(low[i-lookback:i]) * 1.01 and \
                       low[i] <= min(low[i-lookback:i]) * 1.005:
                        entry_triggered = True
                else:
                    if close[i] < max(high[i-lookback:i]) * 0.99 and \
                       high[i] >= max(high[i-lookback:i]) * 0.995:
                        entry_triggered = True
            
            # ── Volatility-based / Bollinger squeeze ────────────────
            if "Volatility-based" in rules["entry_conditions"] or \
               "Bollinger" in str(rules["indicators"]):
                sma20 = _sma(close, 20)
                std20 = pd.Series(close[:i+1]).rolling(20).std().iloc[-1]
                bb_width = (std20 * 2) / sma20 if sma20 > 0 else 0
                # Squeeze: BB width in bottom quartile, then breakout
                if bb_width < 0.02:
                    if rules["direction"] == "long" and close[i] > sma20 * 1.005:
                        entry_triggered = True
                    elif rules["direction"] == "short" and close[i] < sma20 * 0.995:
                        entry_triggered = True
            
            # ── Mean reversion (price extreme) ──────────────────────
            if "Mean reversion" in str(rules["entry_conditions"]) and not entry_triggered:
                lookback = 20
                sma20 = _sma(close, 20)
                std20 = pd.Series(close[:i+1]).rolling(20).std().iloc[-1]
                zscore = (close[i] - sma20) / std20 if std20 > 0 else 0
                if rules["direction"] == "long" and zscore < -1.5:
                    entry_triggered = True
                elif rules["direction"] == "short" and zscore > 1.5:
                    entry_triggered = True
            
            # ── Seasonal pattern (day-of-week effect) ───────────────
            if "Seasonal pattern" in rules["entry_conditions"]:
                try:
                    dow = pd.Timestamp(df.index[i]).dayofweek
                    # Monday entry, Friday exit (common seasonal)
                    if dow == 0:
                        entry_triggered = True
                except:
                    pass
            
            # ── Trend following: price above rising MA ──────────────
            if "Momentum" in str(rules["entry_conditions"]) and not entry_triggered:
                sma50 = _sma(close, min(50, i))
                prev_sma50 = _sma(close[:i], min(50, i-1)) if i > 50 else sma50
                if rules["direction"] == "long" and close[i] > sma50 and sma50 > prev_sma50:
                    entry_triggered = True
                elif rules["direction"] == "short" and close[i] < sma50 and sma50 < prev_sma50:
                    entry_triggered = True
            
            # ── Fallback: if no specific pattern fired but we have rules, use MA cross ──
            if not entry_triggered and len(rules["entry_conditions"]) > 0:
                ema5 = _ema(close, 5)
                ema20 = _ema(close, 20)
                prev_ema5 = _ema(close[:i], 5)
                prev_ema20 = _ema(close[:i], 20)
                if rules["direction"] == "long" and prev_ema5 <= prev_ema20 and ema5 > ema20:
                    entry_triggered = True
                elif rules["direction"] == "short" and prev_ema5 >= prev_ema20 and ema5 < ema20:
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
        print(f"  [X] Searching: {query[:60]}...")
        results = search_x(query, max_results=6)
        print(f"    → {len(results)} results")
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_candidates.append(r)
    
    # ── RSS feeds ──
    for name, feed_url in RSS_FEEDS:
        print(f"  [RSS] {name}...")
        results = _fetch_rss_feed(name, feed_url, max_items=2)
        print(f"    → {len(results)} items")
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_candidates.append(r)
    
    # ── arXiv ──
    for query in ARXIV_QUERIES[:2]:  # 2 queries per cycle to stay fast
        print(f"  [arXiv] {query[:60]}...")
        results = _fetch_arxiv(query, max_results=2)
        print(f"    → {len(results)} papers")
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_candidates.append(r)
    
    # ── GitHub ──
    for query in GITHUB_QUERIES:
        print(f"  [GitHub] {query[:60]}...")
        results = _fetch_github(query, max_results=2)
        print(f"    → {len(results)} repos")
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_candidates.append(r)
    
    # ── Reddit ──
    print(f"  [Reddit] r/algotrading...")
    reddit_results = _fetch_reddit(max_results=3)
    print(f"    → {len(reddit_results)} posts")
    for r in reddit_results:
        if r["url"] not in seen_urls:
            seen_urls.add(r["url"])
            all_candidates.append(r)
    
    # US-156: JEV relevance pre-filter — score and filter before expensive extraction
    raw_count = len(all_candidates)
    if raw_count > 0:
        all_candidates = jev_score_snippets(all_candidates, min_relevance=0.25)
        print(f"  JEV filter: {raw_count} → {len(all_candidates)} relevant snippets")
    
    # Extract rules from filtered candidates
    candidates_with_rules = []
    for r in all_candidates:
        rules = extract_trading_rules(r.get("snippet", ""))
        if not rules:
            continue
        rules["source_url"] = r.get("url", "")
        rules["source_title"] = (r.get("title", "") or "")[:120]
        rules["jev_score"] = r.get("jev_score", 0)
        candidates_with_rules.append(rules)
    
    print(f"\n  Candidates with extractable rules: {len(candidates_with_rules)}")
    
    # Backtest top candidates (up to 5 per cycle to stay fast)
    backtested = []
    for rules in candidates_with_rules[:5]:
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
        json.dump({"cycle": cycle_index, "candidates": len(candidates_with_rules),
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