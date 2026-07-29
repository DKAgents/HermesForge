#!/usr/bin/env python3
"""
daily_publish.py — HermesForge EPIC-009 (US-062)

Daily pipeline: load cached OHLCV data -> run scanners for strategies with
publish_enabled: true -> for each signal, dedup check -> generate chart ->
build alert payload. Designed to be invoked either standalone (prints a
JSON summary + a list of ready-to-post payloads) or via a Hermes cron job
where the agent reads the JSON and dispatches with send_message.

Usage:
    python3 daily_publish.py --dry-run     # full pipeline, no posting/dedup writes
    python3 daily_publish.py               # full pipeline, writes dedup records
                                            # (posting itself is done by the caller)

Env vars required for live posting (see scripts/discord/config.py):
    DISCORD_STOCK_CHANNEL_ID, DISCORD_CRYPTO_CHANNEL_ID
"""

import sys
import json
import argparse
import pathlib
import re
import time

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "validation"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "paper_trading"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "discord"))

from fetch_data import load_all as load_all_stocks  # noqa: E402
from fetch_crypto_data import load_all as load_all_crypto  # noqa: E402
from scanners.scanner_a_ma_pullback import scan as scan_a       # noqa: E402
from scanners.scanner_b_macd_divergence import scan as scan_b   # noqa: E402
from scanners.scanner_c_breakout_volume import scan as scan_c  # noqa: E402
from scanners.scanner_d_sr_reversal import scan as scan_d       # noqa: E402
from scanners.scanner_i_adaptive_trend import scan as scan_i   # noqa: E402

import config as discord_config  # noqa: E402
import dedup                      # noqa: E402
from alert_publisher import publish_signal  # noqa: E402
from chart_generator import generate_setup_chart  # noqa: E402

STRATEGIES_DIR = REPO_ROOT / "06-Strategies" / "Hypotheses"

SCANNER_MAP = {
    "STR-A-ma-pullback-fibonacci": scan_a,
    "STR-B-macd-histogram-divergence": scan_b,
    "STR-C-breakout-volume": scan_c,
    "STR-D-sr-role-reversal": scan_d,
    "STR-I-adaptive-trend": scan_i,
}

# Maps scanner_id prefix (used inside scanner output / STRATEGY_ID consts)
# to the strategy note's frontmatter `id` field, so we can look up publish flags.
SCANNER_TO_NOTE_ID = {
    "STR-A-ma-pullback-fibonacci": "STR-20260719-ma-pullback-fibonacci-entry",
    "STR-B-macd-histogram-divergence": "STR-20260719-macd-histogram-divergence-weekly-assessment",
    "STR-C-breakout-volume": "STR-20260719-breakout-volume-trend",
    "STR-D-sr-role-reversal": "STR-20260719-sr-role-reversal-entry",
    "STR-I-adaptive-trend": "STR-20260728-adaptive-trend",
}

CHART_OUTPUT_DIR = pathlib.Path.home() / ".hermes" / "signal_charts"


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


def load_publish_flags() -> dict:
    """Returns {strategy_note_id: {'publish_enabled': bool, 'publish_channel': str, 'name': str, 'version': str, 'confidence': str}}"""
    flags = {}
    for path in STRATEGIES_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        fm = _parse_frontmatter(text)
        note_id = fm.get("id", path.stem)
        flags[note_id] = {
            "publish_enabled": fm.get("publish_enabled", "false") == "true",
            "publish_channel": fm.get("publish_channel", ""),
            "name": fm.get("name", note_id),
            "version": fm.get("version", "1.0").strip('"'),
            "confidence": fm.get("confidence", "medium"),
        }
    return flags


def run_pipeline(dry_run: bool = False) -> dict:
    publish_flags = load_publish_flags()
    enabled_scanners = {
        scanner_id: fn for scanner_id, fn in SCANNER_MAP.items()
        if publish_flags.get(SCANNER_TO_NOTE_ID.get(scanner_id, ""), {}).get("publish_enabled")
    }

    summary = {
        "signals_found": 0,
        "posted": 0,
        "skipped_duplicates": 0,
        "errors": 0,
        "payloads": [],   # ready_to_post payloads for the caller to dispatch
        "error_details": [],
    }

    if not enabled_scanners:
        summary["note"] = "No strategies have publish_enabled: true — nothing to scan."
        return summary

    # --- Load stock + crypto data ---
    print("Loading cached stock data...")
    stock_data = load_all_stocks()
    print(f"Loaded {len(stock_data)} stock tickers.")

    print("Loading cached crypto data...")
    crypto_data = load_all_crypto()
    print(f"Loaded {len(crypto_data)} crypto symbols.")

    if not stock_data and not crypto_data:
        summary["note"] = "No cached market data found. Run fetch_data.py and fetch_crypto_data.py first."
        return summary

    # --- Scan stocks (route to strategy's publish_channel, typically "stocks") ---
    _scan_and_publish(stock_data, "stock", enabled_scanners, publish_flags,
                      dry_run, summary)

    # --- Scan crypto (override publish_channel to "crypto" regardless of strategy setting) ---
    _scan_and_publish(crypto_data, "crypto", enabled_scanners, publish_flags,
                      dry_run, summary, channel_override="crypto")

    return summary


def _scan_and_publish(data: dict, asset_class: str, enabled_scanners: dict,
                       publish_flags: dict, dry_run: bool, summary: dict,
                       channel_override: str | None = None) -> None:
    """Scan a data dict with each enabled scanner and build publish payloads.

    channel_override: if set (e.g. "crypto"), overrides the strategy's
    publish_channel for routing signals to the correct Discord channel.
    """
    if not data:
        return

    for scanner_id, scan_fn in enabled_scanners.items():
        note_id = SCANNER_TO_NOTE_ID[scanner_id]
        flags = publish_flags[note_id]
        publish_channel = channel_override or flags["publish_channel"]
        print(f"\nScanning {scanner_id} ({flags['name']}, {asset_class})...")

        # Scanner I (AdaptiveTrend) is long-only for stocks, bidirectional for crypto.
        # Other scanners don't accept this kwarg.
        scanner_kwargs = {}
        if scanner_id == "STR-I-adaptive-trend":
            scanner_kwargs["long_only"] = (asset_class == "stock")

        for ticker, df in data.items():
            try:
                signals = scan_fn(df, ticker, **scanner_kwargs)
            except Exception as e:
                summary["errors"] += 1
                summary["error_details"].append(f"{scanner_id}/{ticker} ({asset_class}) scan error: {e}")
                continue

            if not signals:
                continue

            # Only the most recent signal per ticker is actionable for daily publishing.
            # Guard against posting stale historical signals (e.g. on first run
            # against a full history backlog): only consider a signal "new" if
            # it fired on the most recent bar available for this ticker.
            latest = signals[-1]
            most_recent_bar_date = str(df.index[-1])[:10]
            if str(latest["date"])[:10] != most_recent_bar_date:
                continue

            summary["signals_found"] += 1

            entry_date = str(latest["date"])[:10]
            signal_id = dedup.make_signal_id(scanner_id, ticker, entry_date)

            if dedup.is_duplicate(signal_id):
                summary["skipped_duplicates"] += 1
                print(f"  SKIP: {signal_id} already published within lookback window")
                continue

            signal_dict = {
                "ticker": ticker,
                "date": entry_date,
                "direction": latest["direction"],
                "entry_price": latest["entry_price"],
                "stop_price": latest["stop_price"],
                "target_price": latest["target_price"],
                "r_multiple": latest.get("r_multiple", 0),
                "strategy_id": scanner_id,
                "strategy_name": flags["name"],
                "strategy_version": flags["version"],
                "confidence": flags["confidence"],
                "confirmation_level": latest.get("confirmation_level", "Level 1"),
                "subperiod": latest.get("subperiod", "n/a"),
            }
            # Pass through any additional scanner-specific fields used by the
            # chart profile / quality-tier logic (e.g. macd_bars_above_zero,
            # narrowing_bars, rsi_at_signal, prior_swing_bar_offset for
            # Strategy B; volume_ratio for C; swing_high/low for A;
            # resistance_level for D) without hardcoding a strategy-specific
            # allowlist here — new scanner fields flow through automatically.
            for key, value in latest.items():
                if key not in signal_dict:
                    signal_dict[key] = value

            try:
                chart_dir = CHART_OUTPUT_DIR
                chart_path = chart_dir / f"{signal_id}.png"
                generate_setup_chart(ticker, signal_dict, str(chart_path))
            except Exception as e:
                summary["errors"] += 1
                summary["error_details"].append(f"{signal_id} chart generation error: {e}")
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
            })

            if not dry_run:
                dedup.record_published(signal_id, scanner_id, ticker, entry_date, publish_channel)
                summary["posted"] += 1
                time.sleep(2)  # rate limit between posts (US-062 spec)
            else:
                summary["posted"] += 1  # counted as "would post" in dry-run


def main():
    ap = argparse.ArgumentParser(description="HermesForge daily signal scanner -> Discord publisher")
    ap.add_argument("--dry-run", action="store_true", help="Run full pipeline without posting or writing dedup records")
    args = ap.parse_args()

    summary = run_pipeline(dry_run=args.dry_run)

    print(f"\n{'='*60}")
    print(f"SUMMARY: {summary['signals_found']} signals found, "
          f"{summary['posted']} {'would post' if args.dry_run else 'posted'}, "
          f"{summary['skipped_duplicates']} skipped (duplicates), "
          f"{summary['errors']} errors")
    if summary.get("note"):
        print(summary["note"])
    for err in summary.get("error_details", []):
        print(f"  ERROR: {err}")

    print(f"\n--- JSON ---")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
