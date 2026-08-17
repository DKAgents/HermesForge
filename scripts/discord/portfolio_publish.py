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
import os
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
        "disabled_asset_classes": ["crypto"],  # KILLED on crypto per ADR-004 Amendment 1
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

# Near-miss scanner (disabled — STR-D killed in walk-forward, ADR-004 Amendment 1)
# NEAR_MISS_SCANNER = "STR-D-sr-role-reversal"
NEAR_MISS_SCANNER = None

# ── Per-ticker signal recency window ──────────────────────────────────────────
# Event-driven per-ticker scanners (STR-B MACD divergence, STR-I AdaptiveTrend,
# STR-L ATR contraction) fire rarely — a handful of times per ticker per year.
# Requiring a signal to land on the exact latest bar (the original filter) meant
# these scanners essentially NEVER produced a publishable signal on any given
# cron run, so LIVE strategies STR-B and STR-I generated zero trades despite
# being marked publish_enabled. The batch scanner STR-P avoids this because it
# keeps its most-recent *rebalance* date (which can be weeks old).
#
# To make per-ticker strategies actually usable as LIVE strategies, we accept
# the most recent signal per ticker if it fired within the last
# SIGNAL_RECENCY_BARS bars of the data. Each kept signal is tagged with
# `signal_age_bars` so downstream consumers (publisher, paper-trading monitor)
# can judge freshness and avoid entering very stale setups.
SIGNAL_RECENCY_BARS = 5


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


def run_portfolio_pipeline(dry_run: bool = True, crypto_only: bool = False,
                          post_embeds: bool = False) -> dict:
    """
    Main pipeline: detect regime → run active scanners → dedup → score → publish.
    
    If crypto_only=True, skips stock scanning entirely (weekend mode).
    If post_embeds=True, posts signals as Discord embeds via Bot API.
    """
    # ── Load strategy metadata ──────────────────────────────────────────────
    strategy_meta = load_strategy_metadata()
    
    # ── Load data ───────────────────────────────────────────────────────────
    if crypto_only:
        stock_data = {}
        print("[--crypto-only] Skipping stock data load")
    else:
        print("Loading cached stock data...")
        stock_data = load_all_stocks()
        print(f"Loaded {len(stock_data)} stock tickers.")
    
    print("Loading cached crypto data...")
    crypto_data = load_all_crypto()
    print(f"Loaded {len(crypto_data)} crypto symbols.")
    
    if not stock_data and not crypto_data:
        return {"error": "No cached market data found. Run fetch_data.py first."}
    
    # ── Detect regime (separately for stocks and crypto) ────────────────────
    if crypto_only:
        stock_regime = {"regime": "skipped", "benchmark": "n/a",
                        "active_strategies": [], "description": "skipped (weekend mode)"}
    else:
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
    if crypto_only:
        print("\n[--crypto-only] Skipping stock scan (weekend mode)")
        stock_regime = {"regime": "skipped", "benchmark": "n/a", "active_strategies": [],
                        "description": "Stocks skipped — weekend crypto-only mode"}
    else:
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
                          stock_regime, dry_run, summary, post_embeds=post_embeds)
    
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
                          crypto_regime, dry_run, summary, channel_override="crypto",
                          post_embeds=post_embeds)
    
    summary["stock_regime"] = stock_regime
    summary["crypto_regime"] = crypto_regime
    
    return summary


def apply_confirmation_filters(signals: list, data: dict, asset_class: str) -> list:
    """Apply confirmation filters to improve signal quality.
    Only filters STR-P cross-sectional signals. Other strategies pass through."""

    if not signals:
        return signals

    filtered = []
    rejected = 0

    for sig in signals:
        strategy_id = sig.get("strategy_id", "")

        # Only filter STR-P signals
        if "STR-P" not in strategy_id and "P_CROSSSECTIONAL" not in strategy_id:
            filtered.append(sig)
            continue

        ticker = sig.get("ticker", "")
        direction = sig.get("direction", "long")

        # ── Filter 1: Multi-factor agreement ──
        # MOM12_1 and PRICEMOM must agree in direction
        mom = sig.get("factor_mom12_1", 0)
        pricemom = sig.get("factor_pricemom", 0)

        if direction == "long":
            # For longs: both momentum and pricemom should be positive (or at least not strongly negative)
            if mom < -0.05 and pricemom < -0.05:
                rejected += 1
                print(f"  ❌ {ticker} rejected: factor disagreement (MOM={mom:+.2f}, PM={pricemom:+.2f} both negative for long)")
                continue
        else:  # short
            # For shorts: both should be negative (or at least not strongly positive)
            if mom > 0.05 and pricemom > 0.05:
                rejected += 1
                print(f"  ❌ {ticker} rejected: factor disagreement (MOM={mom:+.2f}, PM={pricemom:+.2f} both positive for short)")
                continue

        # ── Filter 2: Composite score minimum ──
        # Reject signals with very low composite scores (near-zero edge)
        composite = abs(sig.get("composite_score", 0))
        if composite < 0.3:
            rejected += 1
            print(f"  ❌ {ticker} rejected: composite score too low ({composite:.2f} < 0.3)")
            continue

        # ── Filter 3: Trend alignment with benchmark ──
        # For crypto: check if BTC is above/below its 50-day SMA
        # Longs only taken when BTC trend is neutral-to-up, shorts when neutral-to-down
        if asset_class == "crypto" and "BTC" in data:
            btc_df = data["BTC"]
            if len(btc_df) >= 50:
                btc_close = btc_df["close"]
                btc_sma50 = btc_close.iloc[-50:].mean()
                btc_current = btc_close.iloc[-1]
                btc_above_sma = btc_current > btc_sma50

                if direction == "short" and btc_above_sma and (btc_current / btc_sma50 - 1) > 0.05:
                    # BTC is 5%+ above SMA50 — don't short
                    rejected += 1
                    print(f"  ❌ {ticker} rejected: trend misalignment (BTC {((btc_current/btc_sma50-1)*100):.1f}% above SMA50, shorting against uptrend)")
                    continue

        # ── Filter 4: Volume confirmation ──
        # Check if signal bar volume is above 20-bar average
        df = data.get(ticker)
        if df is not None and len(df) >= 21:
            vol_20 = df["volume"].iloc[-20:].mean()
            vol_latest = df["volume"].iloc[-1]
            if vol_20 > 0 and vol_latest < vol_20 * 0.5:
                rejected += 1
                print(f"  ❌ {ticker} rejected: low volume ({vol_latest/vol_20:.1f}x 20-bar avg)")
                continue

        # Add confirmation flags to signal
        sig["factor_agreement"] = True
        sig["volume_confirmed"] = True
        sig["trend_aligned"] = True
        filtered.append(sig)

    if rejected > 0:
        print(f"\n  Confirmation filters: {rejected} signal(s) rejected, {len(filtered)} passed")

    return filtered


def _scan_asset_class(data: dict, asset_class: str, scanners: dict,
                      strategy_meta: dict, regime_data: dict,
                      dry_run: bool, summary: dict,
                      channel_override: str = None,
                      post_embeds: bool = False) -> None:
    """Scan all tickers in data dict with each active scanner."""
    if not data:
        return
    
    # Collect all signals across strategies for cross-strategy dedup
    all_signals = []
    
    # Infer asset class per signal, not from channel override
    # STR-P cross-sectional can produce both stock and crypto signals
    # when run in non-crypto-only mode
    if asset_class == "stock":
        signal_publish_channel = "stocks"
    else:
        signal_publish_channel = "crypto"

    for scanner_id, cfg in scanners.items():
        # Check if this scanner is disabled for the current asset class
        disabled = cfg.get("disabled_asset_classes", [])
        if asset_class in disabled:
            print(f"\n  [{scanner_id}] DISABLED for {asset_class} (ADR-004 Amendment 1) — skipping")
            continue

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
                    
                    # Keep the most recent signal per ticker if it fired within
                    # the last SIGNAL_RECENCY_BARS bars (recency window).
                    # The original "exact latest-bar match" filter starved the
                    # rare event-driven scanners (STR-B, STR-I, STR-L) of any
                    # publishable signal — see SIGNAL_RECENCY_BARS docstring.
                    latest = signals[-1]
                    n_bars = len(df)
                    sig_date = latest.get("date")
                    try:
                        sig_pos = int(df.index.get_indexer([pd.Timestamp(sig_date)])[0])
                    except Exception:
                        sig_pos = -1
                    if sig_pos < 0:
                        # Fallback: exact-date string match (old behaviour)
                        most_recent_bar_date = str(df.index[-1])[:10]
                        if str(sig_date)[:10] != most_recent_bar_date:
                            continue
                        sig_pos = n_bars - 1
                    signal_age_bars = (n_bars - 1) - sig_pos
                    if signal_age_bars < 0 or signal_age_bars > SIGNAL_RECENCY_BARS:
                        continue
                    latest["signal_age_bars"] = int(signal_age_bars)
                    
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
                    latest["asset_class"] = asset_class  # routing guard
                    
                    scanner_signals.append(latest)
                    
                except Exception as e:
                    summary["errors"] += 1
                    summary["error_details"].append(
                        f"{scanner_id}/{ticker} ({asset_class}) scan error: {e}"
                    )
        else:
            # Batch mode (STR-P cross-sectional)
            try:
                signals = scan_fn(data, **kwargs)
                # Find the most recent signal date (last rebalance date)
                # This is NOT the same as the most recent data date, because
                # the scanner rebalances every N bars (e.g., 21 days).
                if signals:
                    most_recent_signal_date = max(str(s.get("date", ""))[:10] for s in signals)
                else:
                    most_recent_signal_date = None
                
                # Recency check: only publish if the most recent rebalance is
                # within SIGNAL_RECENCY_BARS of today. A monthly rebalance
                # strategy that rebalanced 17 days ago should NOT be published
                # as new — the entry prices are stale and unactionable.
                # This is the same check that per_ticker mode does, but
                # applied to the rebalance date for batch scanners.
                batch_recency_ok = True
                if signals and most_recent_signal_date:
                    # Use any ticker's data to compute age
                    sample_ticker = next(iter(data))
                    sample_df = data[sample_ticker]
                    n_bars = len(sample_df)
                    try:
                        rebal_pos = int(sample_df.index.get_indexer(
                            [pd.Timestamp(most_recent_signal_date)])[0])
                    except Exception:
                        rebal_pos = -1
                    if rebal_pos >= 0:
                        rebal_age = (n_bars - 1) - rebal_pos
                        if rebal_age > SIGNAL_RECENCY_BARS:
                            print(f"  ⏭️ {scanner_id}: last rebalance {most_recent_signal_date} "
                                  f"is {rebal_age} bars old (> {SIGNAL_RECENCY_BARS}), skipping")
                            batch_recency_ok = False
                
                if batch_recency_ok:
                    for sig in signals:
                        # Only keep signals from the most recent rebalance date
                        if most_recent_signal_date and str(sig.get("date", ""))[:10] != most_recent_signal_date:
                            continue
                        # Skip signals that have already completed (exit set)
                        if sig.get("exit_reason") and sig.get("bars_held", 0) > 0:
                            continue
                        sig["strategy_id"] = scanner_id
                        sig["strategy_name"] = cfg["name"]
                        sig["strategy_status"] = strategy_status
                        sig["is_live"] = is_live
                        sig["publish_channel"] = publish_channel
                        sig["regime"] = regime_data["regime"]
                        sig["score"] = score_signal(sig, scanner_id, meta)
                        sig["asset_class"] = asset_class  # routing guard
                        scanner_signals.append(sig)
            except Exception as e:
                summary["errors"] += 1
                summary["error_details"].append(f"{scanner_id} batch scan error: {e}")
        
        if scanner_signals:
            print(f"  Found {len(scanner_signals)} current-bar signals")
        all_signals.extend(scanner_signals)

    # After collecting all_signals, check if any are live
    live_signals = [s for s in all_signals if s.get("is_live", False)]
    if all_signals and not live_signals:
        print(f"\n  ⚠️ No LIVE strategy signals — all {len(all_signals)} signals are WATCH status")
        print(f"  ⚠️ STR-B needs MACD divergence (fires in trending markets), STR-I is stocks-only")

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

    # ── Confirmation filters ────────────────────────────────────────────────
    # Apply multi-factor, composite-score, trend, and volume confirmation gates
    # to STR-P cross-sectional signals. Other strategies pass through unchanged.
    deduped = apply_confirmation_filters(deduped, data, asset_class)

    # ── Top-N filter: only publish the strongest signals ───────────────────
    MAX_PUBLISH_SIGNALS = 5
    if len(deduped) > MAX_PUBLISH_SIGNALS:
        # Keep top N by score (already sorted by score descending)
        # But ensure we keep at least 1 long and 1 short if available
        top_n = deduped[:MAX_PUBLISH_SIGNALS]
        # Check if we have both directions in top N
        has_long = any(s.get("direction") == "long" for s in top_n)
        has_short = any(s.get("direction") == "short" for s in top_n)
        if not has_long or not has_short:
            # Find best missing direction from remaining signals
            for sig in deduped[MAX_PUBLISH_SIGNALS:]:
                if not has_long and sig.get("direction") == "long":
                    top_n.append(sig)
                    has_long = True
                elif not has_short and sig.get("direction") == "short":
                    top_n.append(sig)
                    has_short = True
                if has_long and has_short:
                    break
        print(f"\n  Top-N filter: publishing {len(top_n)} of {len(deduped)} signals (max {MAX_PUBLISH_SIGNALS})")
        deduped = top_n

    # ── Publish signals ─────────────────────────────────────────────────────
    
    if post_embeds and not dry_run:
        # Embed posting path: post daily header + all signals as embeds
        from embed_publisher import post_daily_batch
        import config as discord_config

        # CRITICAL ROUTING GUARD: Ensure signals are posted to the correct channel.
        # Stocks → DISCORD_STOCK_CHANNEL_ID, Crypto → DISCORD_CRYPTO_CHANNEL_ID
        # Never allow stock signals in the crypto channel or vice versa.
        expected_channel_key = channel_override or ("crypto" if asset_class == "crypto" else "stocks")
        channel_id = discord_config.PUBLISH_CHANNEL_MAP.get(expected_channel_key, expected_channel_key)

        # Validate: every signal in deduped must match the current asset_class
        for sig in deduped:
            sig_asset = sig.get("asset_class", asset_class)
            # Infer from ticker data source if not set
            if sig_asset != asset_class:
                print(f"  ⚠️ ROUTING GUARD: {sig.get('ticker', '?')} is {sig_asset} but being posted in {asset_class} batch — SKIPPING")
        # Filter out any signals that don't match the current asset class
        deduped = [s for s in deduped if s.get("asset_class", asset_class) == asset_class]
        if not deduped:
            print(f"\n  {asset_class.upper()}: 0 signals after routing guard — skipping post")
            return

        # Generate charts for all signals
        for sig in deduped:
            ticker = sig["ticker"]
            entry_date = str(sig.get("date", ""))[:10]
            scanner_id = sig["strategy_id"]
            signal_id = dedup.make_signal_id(scanner_id, ticker, entry_date)

            # Build signal dict (same as text path)
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
                "regime_benchmark": regime_data.get("benchmark", ""),
                "regime_adx": regime_data.get("adx", ""),
                "score": sig["score"],
                "is_live": sig.get("is_live", False),
                "publish_channel": sig.get("publish_channel", signal_publish_channel),
                "asset_class": asset_class,
            }
            for key, value in sig.items():
                if key not in signal_dict:
                    signal_dict[key] = value

            # Generate chart
            chart_path = CHART_OUTPUT_DIR / f"{signal_id}.png"
            try:
                generate_setup_chart(ticker, signal_dict, str(chart_path))
                signal_dict["_chart_path"] = str(chart_path)
            except Exception as e:
                signal_dict["_chart_path"] = None
                print(f"  Chart error for {ticker}: {e}")

            summary["all_signals"].append(signal_dict)

        # Post the batch — ONLY if we have signals for THIS asset class
        # CRITICAL: When deduped is empty, list[-0:] returns the ENTIRE list
        # (Python slicing bug), which would re-post the previous asset class's
        # signals to the wrong channel. Guard against this explicitly.
        if not deduped:
            print(f"\n  {asset_class.upper()}: 0 signals — skipping post (nothing to publish)")
            return

        live_count = sum(1 for s in deduped if s.get("is_live", False))
        watch_count = len(deduped) - live_count
        strategy_names = sorted(set(s.get("strategy_name", "?") for s in deduped))

        # Use only the signals added in THIS call (last len(deduped) entries)
        batch_signals = summary["all_signals"][-len(deduped):]

        batch_result = post_daily_batch(
            batch_signals,
            channel_id, asset_class, regime_data, dry_run=False,
        )
        summary["posted"] = batch_result["posted"]
        summary["errors"] += batch_result["errors"]

        print(f"\n  {asset_class.upper()}: {batch_result['posted']} embeds posted "
              f"({live_count} live, {watch_count} watch)")
        return

    # Text posting path (original)
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
            "regime_benchmark": regime_data.get("benchmark", ""),
            "regime_adx": regime_data.get("adx", ""),
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
    ap.add_argument("--crypto-only", action="store_true",
                    help="Skip stock scanning, run crypto only (weekend mode)")
    ap.add_argument("--post-embeds", action="store_true",
                    help="Post signals as Discord embeds (colored borders, charts, "
                         "daily header, horizontal rules). Requires DISCORD_BOT_TOKEN.")
    args = ap.parse_args()
    
    summary = run_portfolio_pipeline(dry_run=args.dry_run, crypto_only=args.crypto_only,
                                     post_embeds=args.post_embeds)
    
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
