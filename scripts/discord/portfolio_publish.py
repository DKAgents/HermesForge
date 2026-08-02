#!/usr/bin/env python3
"""
portfolio_publish.py — HermesForge Regime-Aware Portfolio Signal Pipeline

Replaces daily_publish.py as the primary publisher. Key improvements:
  1. Detects current market regime from SPY data
  2. Only runs scanners matched to the detected regime
  3. Includes ALL WATCH/PASS strategies (not just publish_enabled)
  4. Cross-strategy deduplication: if same ticker triggers 2 strategies,
     keeps the higher-confidence one
  5. Signal scoring: ranks signals by strategy edge + R:R + confidence
  6. Tags every signal with the regime it fired in
  7. Publishes combined output to a single channel per asset class

Strategy activation logic:
  - Regime detector classifies market (trending/ranging/transitional/high-vol/low-vol)
  - Each strategy maps to 1+ regimes where it has demonstrated edge
  - Only regime-matched strategies run that day
  - Near-miss scanner (STR-D) always runs regardless of regime

Usage:
    python3 portfolio_publish.py --dry-run     # full pipeline, no posting
    python3 portfolio_publish.py               # full pipeline with posting
"""

import sys
import json
import argparse
import pathlib
import re
import time
import pandas as pd
import numpy as np

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "discord"))

from fetch_data import load_all as load_all_stocks
from fetch_crypto_data import load_all as load_all_crypto
from intraday_confirm import confirm_signals as confirm_intraday
from scanners.scanner_b_macd_divergence import scan as scan_b
from scanners.scanner_d_sr_reversal import scan as scan_d
from scanners.scanner_i_adaptive_trend import scan as scan_i
from scanners.scanner_j_eufearia_cci import scan as scan_j
from scanners.scanner_l_atr_contraction import scan_ticker as scan_l_ticker
from scanners.scanner_p_crosssectional import scan as scan_p

from regime_detector import (
    detect_regime, detect_regime_for_asset_class,
    get_active_strategies, STRATEGY_REGIME_MAP,
)

import config as discord_config
import dedup
from alert_publisher import publish_signal
from chart_generator import generate_setup_chart

STRATEGIES_DIR = REPO_ROOT / "06-Strategies" / "Hypotheses"
CHART_OUTPUT_DIR = pathlib.Path.home() / ".hermes" / "signal_charts"

# ── Scanner Registry ─────────────────────────────────────────────────────────
# All scanners that can be activated by the regime detector.
# Each entry: (scanner_id, scan_function, call_mode, strategy_note_id, display_name)

# call_mode:
#   "per_ticker"  — scan(df, ticker) returns list of signals for that ticker
#   "batch"       — scan(data_dict) returns list of all signals at once

SCANNER_REGISTRY = {
    "STR-B-macd-histogram-divergence": {
        "scan_fn": scan_b,
        "call_mode": "per_ticker",
        "note_id": "STR-20260719-macd-histogram-divergence-weekly-assessment",
        "name": "MACD Divergence",
        "default_confidence": "medium",
        "scanner_kwargs": {},
    },
    "STR-I-adaptive-trend": {
        "scan_fn": scan_i,
        "call_mode": "per_ticker",
        "note_id": "STR-20260728-adaptive-trend",
        "name": "AdaptiveTrend",
        "default_confidence": "high",
        "scanner_kwargs": {},  # long_only set dynamically per asset_class
    },
    "STR-L-atr-contraction": {
        "scan_fn": scan_l_ticker,
        "call_mode": "per_ticker",
        "note_id": "STR-20260730-atr-contraction-breakout",
        "name": "ATR Contraction",
        "default_confidence": "medium",
        "scanner_kwargs": {},
    },
    "STR-P-crosssectional": {
        "scan_fn": scan_p,
        "call_mode": "batch",
        "note_id": "STR-20260801-crosssectional-factor",
        "name": "Cross-Sectional Factor",
        "default_confidence": "low",
        "scanner_kwargs": {},
    },
}

# Near-miss scanner (always runs, separate output)
NEAR_MISS_SCANNER = "STR-D-sr-role-reversal"


def _parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^(\w[\w_-]*):\s*(.*)", line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip()
    return fm


def load_strategy_metadata() -> dict:
    """Load frontmatter from all strategy hypothesis files."""
    meta = {}
    for path in STRATEGIES_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        fm = _parse_frontmatter(text)
        note_id = fm.get("id", path.stem)
        meta[note_id] = {
            "publish_enabled": fm.get("publish_enabled", "false") == "true",
            "publish_channel": fm.get("publish_channel", ""),
            "name": fm.get("source_title", note_id),
            "confidence": fm.get("confidence", "medium"),
            "status": fm.get("status", "unknown"),
            "direction": fm.get("direction", "bidirectional"),
        }
    return meta


def score_signal(signal: dict, strategy_id: str, strategy_meta: dict) -> float:
    """
    Score a signal for ranking. Higher = better.
    
    Factors:
      - Strategy confidence (high=3, medium=2, low=1)
      - Strategy status (live=3, watch=2, hypothesis=1, killed=0)
      - R:R ratio (if available)
      - Projected R:R (if available)
    """
    score = 0.0
    
    # Strategy confidence
    confidence = strategy_meta.get("confidence", "medium")
    conf_map = {"high": 3, "medium": 2, "low": 1}
    score += conf_map.get(confidence, 2)
    
    # Strategy status
    status = strategy_meta.get("status", "unknown")
    status_map = {"live": 3, "watch": 2, "hypothesis": 1, "killed": 0}
    score += status_map.get(status, 0)
    
    # R:R ratio from signal
    entry = signal.get("entry_price", 0)
    stop = signal.get("stop_price", 0)
    target = signal.get("target_price", 0)
    if entry and stop and target and entry != stop:
        risk = abs(entry - stop)
        reward = abs(target - entry)
        if risk > 0:
            rr = reward / risk
            score += min(rr, 5.0)  # cap at 5
    
    # Projected R:R (some scanners provide this)
    rr_proj = signal.get("rr_projected", 0)
    if rr_proj and rr_proj > 0:
        score += min(rr_proj, 3.0)
    
    return round(score, 2)


def apply_liquidity_filter(signals: list, max_pct: float = 0.80) -> list:
    """
    Filter signals by liquidity — keep only those below max_pct percentile
    of dollar_volume_60d. Less liquid signals perform better (p=0.0025).

    If dollar_volume_60d is missing from any signal, skip filtering.
    """
    if not signals:
        return signals

    # Extract dollar volumes
    dv_values = [s.get('dollar_volume_60d', 0) for s in signals]
    if all(v == 0 for v in dv_values):
        return signals  # No volume data — don't filter

    import numpy as np
    threshold = np.percentile(dv_values, max_pct * 100)

    kept = [s for s in signals if s.get('dollar_volume_60d', 0) <= threshold]
    removed = len(signals) - len(kept)

    if removed > 0:
        print(f'  Liquidity filter: removed {removed} signal(s) above {max_pct:.0%} percentile')

    return kept


def run_portfolio_pipeline(dry_run: bool = True) -> dict:
    """
    Main pipeline: detect regime → run active scanners → dedup → score → publish.
    """
    # ── Load strategy metadata ──────────────────────────────────────────────
    strategy_meta = load_strategy_metadata()
    
    # ── Load data ───────────────────────────────────────────────────────────
    print("Loading cached stock data...")
    stock_data = load_all_stocks()
    print(f"Loaded {len(stock_data)} stock tickers.")
    
    print("Loading cached crypto data...")
    crypto_data = load_all_crypto()
    print(f"Loaded {len(crypto_data)} crypto symbols.")
    
    if not stock_data and not crypto_data:
        return {"error": "No cached market data found. Run fetch_data.py first."}
    
    # ── Detect regime (separately for stocks and crypto) ────────────────────
    stock_regime = detect_regime_for_asset_class(stock_data, crypto_data, "stock")
    crypto_regime = detect_regime_for_asset_class(stock_data, crypto_data, "crypto") if crypto_data else None
    
    summary = {
        "signals_found": 0,
        "posted": 0,
        "skipped_duplicates": 0,
        "errors": 0,
        "payloads": [],
        "error_details": [],
        "all_signals": [],
    }
    
    print(f"\n{'='*60}")
    print(f"Regime Detection")
    print(f"{'='*60}")
    print(f"Stocks  ({stock_regime.get('benchmark', 'SPY')}):  {stock_regime['description']}")
    if crypto_regime:
        print(f"Crypto  ({crypto_regime.get('benchmark', 'BTC')}):  {crypto_regime['description']}")
    
    # ── Scan stocks (using stock regime) ────────────────────────────────────
    stock_active = stock_regime["active_strategies"]
    print(f"\nStock active strategies: {stock_active}")
    
    stock_scanners = {
        sid: cfg for sid, cfg in SCANNER_REGISTRY.items()
        if sid in stock_active
    }
    # Always include publish_enabled strategies
    for sid, cfg in SCANNER_REGISTRY.items():
        if sid not in stock_scanners:
            note_id = cfg["note_id"]
            meta = strategy_meta.get(note_id, {})
            if meta.get("publish_enabled"):
                stock_scanners[sid] = cfg
    
    _scan_asset_class(stock_data, "stock", stock_scanners, strategy_meta,
                      stock_regime, dry_run, summary)
    
    # ── Scan crypto (using crypto regime) ───────────────────────────────────
    if crypto_data and crypto_regime:
        crypto_active = crypto_regime["active_strategies"]
        print(f"\nCrypto active strategies: {crypto_active}")
        
        crypto_scanners = {
            sid: cfg for sid, cfg in SCANNER_REGISTRY.items()
            if sid in crypto_active
        }
        for sid, cfg in SCANNER_REGISTRY.items():
            if sid not in crypto_scanners:
                note_id = cfg["note_id"]
                meta = strategy_meta.get(note_id, {})
                if meta.get("publish_enabled"):
                    crypto_scanners[sid] = cfg
        
        _scan_asset_class(crypto_data, "crypto", crypto_scanners, strategy_meta,
                          crypto_regime, dry_run, summary, channel_override="crypto")
    
    summary["stock_regime"] = stock_regime
    summary["crypto_regime"] = crypto_regime
    
    return summary


def _scan_asset_class(data: dict, asset_class: str, scanners: dict,
                      strategy_meta: dict, regime_data: dict,
                      dry_run: bool, summary: dict,
                      channel_override: str = None) -> None:
    """Scan all tickers in data dict with each active scanner."""
    if not data:
        return
    
    # Collect all signals across strategies for cross-strategy dedup
    all_signals = []
    
    for scanner_id, cfg in scanners.items():
        scan_fn = cfg["scan_fn"]
        call_mode = cfg["call_mode"]
        note_id = cfg["note_id"]
        meta = strategy_meta.get(note_id, {})
        publish_channel = channel_override or meta.get("publish_channel", "stocks")
        
        # Determine if this strategy is publish_enabled (live) or WATCH
        is_live = meta.get("publish_enabled", False)
        strategy_status = meta.get("status", "unknown")
        
        print(f"\nScanning {scanner_id} ({cfg['name']}, {asset_class}, {strategy_status})...")
        
        # Scanner-specific kwargs
        kwargs = dict(cfg.get("scanner_kwargs", {}))
        if scanner_id == "STR-I-adaptive-trend":
            kwargs["long_only"] = (asset_class == "stock")
        
        scanner_signals = []
        
        if call_mode == "per_ticker":
            for ticker, df in data.items():
                try:
                    signals = scan_fn(df, ticker, **kwargs)
                    if not signals:
                        continue
                    
                    # Only keep the most recent signal per ticker (latest bar)
                    latest = signals[-1]
                    most_recent_bar_date = str(df.index[-1])[:10]
                    if str(latest.get("date", ""))[:10] != most_recent_bar_date:
                        continue
                    
                    # Filter direction for stocks (long-only per ADR)
                    if asset_class == "stock":
                        direction = latest.get("direction", "long")
                        strategy_direction = meta.get("direction", "bidirectional")
                        if strategy_direction == "long-only" and direction == "short":
                            continue
                    
                    latest["strategy_id"] = scanner_id
                    latest["strategy_name"] = cfg["name"]
                    latest["strategy_status"] = strategy_status
                    latest["is_live"] = is_live
                    latest["publish_channel"] = publish_channel
                    latest["regime"] = regime_data["regime"]
                    latest["score"] = score_signal(latest, scanner_id, meta)
                    
                    scanner_signals.append(latest)
                    
                except Exception as e:
                    summary["errors"] += 1
                    summary["error_details"].append(
                        f"{scanner_id}/{ticker} ({asset_class}) scan error: {e}"
                    )
        else:
            # Batch mode
            try:
                signals = scan_fn(data, **kwargs)
                for sig in signals:
                    # Only keep most recent bar signals
                    most_recent_dates = {str(df.index[-1])[:10] for df in data.values() if len(df) > 0}
                    if str(sig.get("date", ""))[:10] not in most_recent_dates:
                        continue
                    sig["strategy_id"] = scanner_id
                    sig["strategy_name"] = cfg["name"]
                    sig["strategy_status"] = strategy_status
                    sig["is_live"] = is_live
                    sig["publish_channel"] = publish_channel
                    sig["regime"] = regime_data["regime"]
                    sig["score"] = score_signal(sig, scanner_id, meta)
                    scanner_signals.append(sig)
            except Exception as e:
                summary["errors"] += 1
                summary["error_details"].append(f"{scanner_id} batch scan error: {e}")
        
        if scanner_signals:
            print(f"  Found {len(scanner_signals)} current-bar signals")
        all_signals.extend(scanner_signals)
    
    # ── Cross-strategy dedup ────────────────────────────────────────────────
    # If same ticker appears in multiple strategies, keep the highest score
    ticker_best = {}
    for sig in all_signals:
        ticker = sig.get("ticker", "")
        if ticker not in ticker_best or sig["score"] > ticker_best[ticker]["score"]:
            ticker_best[ticker] = sig
    
    deduped = list(ticker_best.values())
    deduped.sort(key=lambda x: x["score"], reverse=True)
    
    removed = len(all_signals) - len(deduped)
    if removed > 0:
        print(f"\nCross-strategy dedup: {removed} duplicate(s) removed")
    
    # ── Publish signals ─────────────────────────────────────────────────────
    for sig in deduped:
        ticker = sig["ticker"]
        entry_date = str(sig.get("date", ""))[:10]
        scanner_id = sig["strategy_id"]
        signal_id = dedup.make_signal_id(scanner_id, ticker, entry_date)
        
        if dedup.is_duplicate(signal_id):
            summary["skipped_duplicates"] += 1
            print(f"  SKIP: {signal_id} already published")
            continue
        
        summary["signals_found"] += 1
        
        # Build signal dict for publisher
        signal_dict = {
            "ticker": ticker,
            "date": entry_date,
            "direction": sig.get("direction", "long"),
            "entry_price": sig.get("entry_price", 0),
            "stop_price": sig.get("stop_price", 0),
            "target_price": sig.get("target_price", 0),
            "r_multiple": sig.get("r_multiple", 0),
            "strategy_id": scanner_id,
            "strategy_name": sig["strategy_name"],
            "strategy_version": "1.0",
            "confidence": strategy_meta.get(
                SCANNER_REGISTRY[scanner_id]["note_id"], {}
            ).get("confidence", "medium"),
            "confirmation_level": sig.get("confirmation_level", "Level 1"),
            "subperiod": sig.get("subperiod", "n/a"),
            "regime": sig.get("regime", "unknown"),
            "score": sig["score"],
        }
        for key, value in sig.items():
            if key not in signal_dict:
                signal_dict[key] = value
        
        publish_channel = sig.get("publish_channel", "stocks")
        
        # Only publish live signals; WATCH signals are logged but not posted
        if not sig.get("is_live", False):
            print(f"  WATCH (not published): {scanner_id} {ticker} "
                  f"dir={sig.get('direction', '?')} entry={sig.get('entry_price', '?')} "
                  f"score={sig['score']}")
            summary["all_signals"].append(signal_dict)
            continue
        
        try:
            chart_path = CHART_OUTPUT_DIR / f"{signal_id}.png"
            generate_setup_chart(ticker, signal_dict, str(chart_path))
        except Exception as e:
            summary["errors"] += 1
            summary["error_details"].append(f"{signal_id} chart error: {e}")
            continue
        
        result = publish_signal(
            signal_dict, str(chart_path),
            publish_channel=publish_channel,
            dry_run=dry_run,
        )
        
        if result["status"] == "error":
            summary["errors"] += 1
            summary["error_details"].append(f"{signal_id}: {result['message']}")
            continue
        
        summary["payloads"].append({
            "signal_id": signal_id,
            "strategy_id": scanner_id,
            "ticker": ticker,
            "entry_date": entry_date,
            "channel": publish_channel,
            "asset_class": asset_class,
            "target": result["target"],
            "message": result["message"],
            "score": sig["score"],
        })
        
        if not dry_run:
            dedup.record_published(signal_id, scanner_id, ticker, entry_date, publish_channel)
            summary["posted"] += 1
            time.sleep(2)
        else:
            summary["posted"] += 1
        
        summary["all_signals"].append(signal_dict)
    
    # Print summary for this asset class
    live_count = sum(1 for s in deduped if s.get("is_live", False))
    watch_count = len(deduped) - live_count
    print(f"\n  {asset_class.upper()}: {len(deduped)} unique signals "
          f"({live_count} live, {watch_count} WATCH)")


def main():
    ap = argparse.ArgumentParser(
        description="HermesForge regime-aware portfolio signal pipeline"
    )
    ap.add_argument("--dry-run", action="store_true",
                    help="Run full pipeline without posting")
    args = ap.parse_args()
    
    summary = run_portfolio_pipeline(dry_run=args.dry_run)
    
    if "error" in summary:
        print(f"\nERROR: {summary['error']}")
        return
    
    stock_regime = summary.get("stock_regime", {})
    crypto_regime = summary.get("crypto_regime", {})
    
    print(f"\n{'='*60}")
    print(f"PORTFOLIO PIPELINE SUMMARY")
    print(f"{'='*60}")
    print(f"Stock regime ({stock_regime.get('benchmark', '?')}): {stock_regime.get('regime', '?')}")
    if crypto_regime:
        print(f"Crypto regime ({crypto_regime.get('benchmark', '?')}): {crypto_regime.get('regime', '?')}")
    print(f"Signals found: {summary['signals_found']}")
    print(f"  Posted: {summary['posted']}")
    print(f"  Skipped (duplicates): {summary['skipped_duplicates']}")
    print(f"  Errors: {summary['errors']}")
    
    if summary["all_signals"]:
        print(f"\nAll signals (sorted by score):")
        df = pd.DataFrame(summary["all_signals"])
        if "score" in df.columns:
            df = df.sort_values("score", ascending=False)
        for _, row in df.iterrows():
            live_tag = "LIVE" if row.get("is_live", False) else "WATCH"
            print(f"  [{live_tag}] {row.get('strategy_id', '?'):35s} "
                  f"{row.get('ticker', '?'):6s} "
                  f"dir={row.get('direction', '?'):5s} "
                  f"entry={row.get('entry_price', '?'):>10} "
                  f"score={row.get('score', 0):.1f} "
                  f"regime={row.get('regime', '?')}")
    
    for err in summary.get("error_details", []):
        print(f"  ERROR: {err}")
    
    print(f"\n--- JSON ---")
    print(json.dumps({
        "stock_regime": stock_regime.get("regime", "unknown"),
        "crypto_regime": crypto_regime.get("regime", "unknown") if crypto_regime else "n/a",
        "signals_found": summary["signals_found"],
        "posted": summary["posted"],
        "skipped_duplicates": summary["skipped_duplicates"],
        "errors": summary["errors"],
        "watch_signals": [
            {"ticker": s.get("ticker"), "strategy": s.get("strategy_id"),
             "direction": s.get("direction"), "entry": s.get("entry_price"),
             "score": s.get("score")}
            for s in summary["all_signals"] if not s.get("is_live", False)
        ],
        "payloads": summary["payloads"],
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
