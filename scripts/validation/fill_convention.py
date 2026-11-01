#!/usr/bin/env python3
"""
fill_convention.py — single owner of the discovery-backtest fill convention
(US-173).

US-173 fixed the look-ahead close-entry bug: a daily-bar signal is only
actionable at the NEXT bar's open (open[signal_idx + 1]), never the
signal-bar close (the latter leaked a full bar of information into the fill
price). This module is the single place where:

  1. the fill-convention CONSTANT and CSV version discriminator live, so
     walk_forward.py / walk_forward_us114.py / the discovery runners all agree
     on the same `fill_convention` tag and `-v4` filename bump (no literal
     strings scattered across call sites);

  2. the legacy-CSV backward-compatibility shim `apply_next_open_entry` lives,
     which re-rates a close-entry signal dict to a next-open entry. This is used
     ONLY on legacy (pre-US-173) phase1a CSVs via `walk_forward_us114.py
     --shim-legacy-close-entry` — freshly-scanned output is already next-open
     and must never pass through the shim (single-pass guard below).

This module has zero coupling to trade_log / trade_journal / scanners; it is
pure pandas + arithmetic and stays unit-testable in isolation (mirrors how
pnl_accounting.py unified the hostile-fill helpers).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# The one true fill convention for daily-bar discovery backtests (US-173).
FILL_CONVENTION = "next_open"

# CSV version discriminator. US-114 used v1->v2, US-115 used v3; US-173's
# fill-semantics change is the next bump. Never overwrite a legacy close-entry
# CSV in place ("no silent data loss" hard rule).
PHASE1A_VERSION = "v4"

# Signal-dict key that marks a signal already re-rated by the shim, so a
# double-application (which would charge the adverse drift twice) is refused.
_SHIMMED_KEY = "_fill_convention_shim_applied"


def add_fill_convention(df: pd.DataFrame) -> pd.DataFrame:
    """Add the fill-convention columns to an emitted phase1a results frame.

    Auditors can then tell a next-open backtest from a legacy close-entry one by
    inspection, not inference (§1.4 pt2).
    """
    if df is None or len(df) == 0:
        return df
    df = df.copy()
    df["fill_convention"] = FILL_CONVENTION
    df["signal_bar_close_entry"] = False
    return df


def versioned_phase1a_name(strategy_id: str, asset_class: str = "stocks") -> str:
    """Canonical versioned results filename, e.g. 'STR-T-stocks-phase1a-v4.csv'."""
    return f"{strategy_id}-{asset_class}-phase1a-{PHASE1A_VERSION}.csv"


def write_phase1a(results_df: pd.DataFrame, results_dir, strategy_id: str,
                  asset_class: str = "stocks"):
    """Stamp fill-convention columns and write a versioned phase1a CSV.

    Single owner of the next-open CSV emission used by every scanner's
    __main__/run_phase1a block and the master runner. Never overwrites a legacy
    close-entry CSV in place (§1.4 pt1 "no silent data loss").
    Returns the written Path.
    """
    import pathlib
    out_dir = pathlib.Path(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamped = add_fill_convention(results_df)
    out_path = out_dir / versioned_phase1a_name(strategy_id, asset_class)
    stamped.to_csv(out_path, index=False)
    return out_path


def apply_next_open_entry(signal: dict, df: pd.DataFrame, direction: str) -> dict:
    """Legacy-CSV shim (US-173 §1.3.3): re-rate a close-entry signal to next-open.

    Given a signal dict whose `entry_price` is the signal-bar CLOSE (legacy
    pre-US-173), locate the signal bar by `signal["date"]` and overwrite the
    entry to `open[signal_bar + 1]`, charging the adverse-selection drift against
    `r_multiple`.

    Drift sign (realized-R correct):
        long : drift_r = (new_entry - old_entry) / risk   # gap up  => adverse >= 0
        short: drift_r = (old_entry - new_entry) / risk   # gap down => adverse >= 0
        new_r  = old_r - drift_r                          # adverse reduces R

    Guard: if the signal bar is the last bar (no next-open to fill), returns the
    signal unchanged (cannot realistically fill). If the signal was already
    shimmed, returns it unchanged (single-pass guard against double charging).

    Adds keys on the (copied) returned dict:
        fill_convention = "next_open"
        lookahead_shim  = True
        entry_drift_r   = drift_r (signed as adverse; 0.0 if degenerate)
        entry_fill      = "next_open"
    """
    sig = dict(signal)
    if sig.get(_SHIMMED_KEY):
        return sig  # already re-rated — never double-apply

    old_entry = float(sig.get("entry_price", 0))
    stop_price = float(sig.get("stop_price", 0))
    risk = abs(old_entry - stop_price)
    if risk <= 0:
        return sig  # degenerate stop: cannot re-rate meaningfully

    date_val = sig.get("date", "")
    try:
        ts = pd.Timestamp(date_val)
    except (ValueError, TypeError):
        return sig

    # Locate the signal bar (the legacy CSV stores entry "date" = signal bar).
    mask = df.index == ts
    if not mask.any():
        return sig
    pos = df.index.get_loc(df.index[mask][0])
    if isinstance(pos, slice):
        pos = pos.start
    if isinstance(pos, (list, np.ndarray)):
        pos = int(pos[0])
    pos = int(pos)

    if pos + 1 >= len(df):
        return sig  # signal on last bar -> no next-open fill

    new_entry = float(df["open"].iloc[pos + 1])

    if direction == "long":
        drift_r = (new_entry - old_entry) / risk
    else:
        drift_r = (old_entry - new_entry) / risk

    old_r = float(sig.get("r_multiple", 0))
    new_r = old_r - drift_r

    sig["entry_price"] = round(new_entry, 6)
    sig["r_multiple"] = round(new_r, 4)
    sig["fill_convention"] = FILL_CONVENTION
    sig["lookahead_shim"] = True
    sig["entry_drift_r"] = round(drift_r, 4)
    sig["entry_fill"] = FILL_CONVENTION
    sig[_SHIMMED_KEY] = True
    return sig