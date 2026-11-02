"""vrp_paper_store.py — HermesForge US-181: paper-forward accumulation store.

The short-vol / VRP strategy (US-181) is a HYPOTHESIS, not a promotable
strategy: the IV store has ~30d of DVOL + a single ATM-IV snapshot, so
VOV_THRESHOLD cannot be derived and G3 cannot be met yet (§5.4). This store is
the paper-forward accumulation surface — it records, WITHOUT any live money and
WITHOUT any promotion:

  * one ``morning_snapshots`` row per (currency, UTC day): the vol-of-vol level,
    ATM IV, spot, DTE, realized vol, the timing-predicate components, and the
    straddle premium — the inputs that will later let the backtest derive
    VOV_THRESHOLD and run the timed-vs-unconditional dominance test.
  * one ``paper_positions`` row per (currency, entry_ts, expiry): a PAPER short
    straddle, its sizing (1R = 1% capital, MARGIN_CAP_FRAC = 1.0), and — once
    it closes (expiry or vol-spike stop) — the realized |S_T - K| payoff and the
    net PnL.

Every row is labelled ``paper-forward-hypothesis`` (never "proven"/"live"). No
row is ever written to trades.csv / the journal / the strategy registry.

Store location: ~/.hermes/market_data/vol_vrp/vrp_paper.db

Import direction (one-way, acyclic):
  vrp_paper_forward.py -> vrp_paper_store.py (+ iv_store + hl_bar_store
                          + vol_of_vol_gate + vol_vrp)
"""

from __future__ import annotations

import sqlite3
import pathlib

import pandas as pd

STORE_DIR = pathlib.Path.home() / ".hermes" / "market_data" / "vol_vrp"
DB_NAME = "vrp_paper.db"

PRAGMAS = (
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA foreign_keys=ON;",
)

# The only label a US-181 paper row ever carries — no "proven", no "live".
HYPOTHESIS_LABEL = "paper-forward-hypothesis"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS morning_snapshots (
    currency       TEXT    NOT NULL,   -- 'BTC' | 'ETH'
    day            TEXT    NOT NULL,   -- YYYY-MM-DD (UTC)
    snap_ts        INTEGER NOT NULL,   -- DVOL morning-candle ts, ms
    dvol_close     REAL,               -- DVOL index level (%)
    vol_of_vol     REAL,               -- annualized vol-of-vol level
    atm_iv         REAL,               -- ATM IV (%)
    spot           REAL,
    dte            REAL,
    expiry         INTEGER,            -- selected expiry ts, ms
    realized_vol   REAL,               -- annualized 5m realized vol
    straddle_premium REAL,
    vrp_rich       INTEGER,            -- 0/1
    morning        INTEGER,            -- 0/1 (always 1 in this store)
    vov_threshold  REAL,               -- NULL until derived (§2.2)
    vov_calm       INTEGER,            -- NULL until threshold derived
    enter          INTEGER,            -- 0/1 (0 until threshold derived)
    label          TEXT NOT NULL,
    PRIMARY KEY (currency, day)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS paper_positions (
    currency       TEXT    NOT NULL,
    entry_ts       INTEGER NOT NULL,   -- morning snap ts (entry)
    expiry         INTEGER NOT NULL,   -- the straddle's expiry ts
    strike         REAL    NOT NULL,   -- K ~= S0
    premium_collected REAL NOT NULL,
    contracts      REAL    NOT NULL,
    notional       REAL    NOT NULL,
    margin_deployed REAL   NOT NULL,
    risk_usd       REAL    NOT NULL,
    size_capped    INTEGER NOT NULL,   -- 0/1
    cap_reason     TEXT,
    status         TEXT    NOT NULL,   -- 'open' | 'closed'
    entry_dvol     REAL,               -- DVOL at entry (stop reference)
    entry_atm_iv   REAL,               -- ATM IV at entry (stop reference)
    exit_ts        INTEGER,            -- 0 until closed
    exit_reason    TEXT,               -- 'expiry' | 'vol_spike'
    realized_payoff REAL,              -- |S_T - K|
    gross_pnl      REAL,
    execution_cost REAL,
    net_pnl        REAL,
    net_r          REAL,
    label          TEXT NOT NULL,
    PRIMARY KEY (currency, entry_ts, expiry)
) WITHOUT ROWID;
"""


def db_path() -> pathlib.Path:
    return STORE_DIR / DB_NAME


def open_store() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    for pragma in PRAGMAS:
        conn.execute(pragma)
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def _f(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def upsert_snapshot(conn: sqlite3.Connection, snap: dict) -> int:
    """INSERT OR REPLACE a morning snapshot keyed (currency, day). Idempotent;
    re-running the same UTC day overwrites rather than duplicates. Returns the
    rowcount (1)."""
    cur = conn.execute(
        "INSERT OR REPLACE INTO morning_snapshots "
        "(currency, day, snap_ts, dvol_close, vol_of_vol, atm_iv, spot, dte, "
        " expiry, realized_vol, straddle_premium, vrp_rich, morning, "
        " vov_threshold, vov_calm, enter, label) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (str(snap["currency"]), str(snap["day"]), int(snap["snap_ts"]),
         _f(snap.get("dvol_close")), _f(snap.get("vol_of_vol")),
         _f(snap.get("atm_iv")), _f(snap.get("spot")), _f(snap.get("dte")),
         int(snap["expiry"]) if snap.get("expiry") is not None else None,
         _f(snap.get("realized_vol")), _f(snap.get("straddle_premium")),
         int(bool(snap.get("vrp_rich"))), int(bool(snap.get("morning"))),
         _f(snap.get("vov_threshold")),
         None if snap.get("vov_calm") is None else int(bool(snap["vov_calm"])),
         int(bool(snap.get("enter"))), HYPOTHESIS_LABEL),
    )
    conn.commit()
    return cur.rowcount if cur.rowcount is not None else 0


def open_position(conn: sqlite3.Connection, pos: dict) -> int:
    """INSERT OR IGNORE a paper short-straddle position. Returns new-row count
    (0 if the (currency, entry_ts, expiry) key already exists)."""
    cur = conn.execute(
        "INSERT OR IGNORE INTO paper_positions "
        "(currency, entry_ts, expiry, strike, premium_collected, contracts, "
        " notional, margin_deployed, risk_usd, size_capped, cap_reason, status, "
        " entry_dvol, entry_atm_iv, exit_ts, exit_reason, realized_payoff, "
        " gross_pnl, execution_cost, net_pnl, net_r, label) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,0,NULL,NULL,NULL,NULL,NULL,NULL,?)",
        (str(pos["currency"]), int(pos["entry_ts"]), int(pos["expiry"]),
         float(pos["strike"]), float(pos["premium_collected"]),
         float(pos["contracts"]), float(pos["notional"]),
         float(pos["margin_deployed"]), float(pos["risk_usd"]),
         int(bool(pos.get("size_capped"))), pos.get("cap_reason"),
         "open", _f(pos.get("entry_dvol")), _f(pos.get("entry_atm_iv")),
         HYPOTHESIS_LABEL),
    )
    conn.commit()
    return cur.rowcount if cur.rowcount is not None else 0


def close_position(conn: sqlite3.Connection, currency: str, entry_ts: int,
                   expiry: int, exit_ts: int, exit_reason: str,
                   realized_payoff: float, gross_pnl: float,
                   execution_cost: float, net_pnl: float, net_r: float) -> int:
    """Mark an open paper position closed (expiry or vol-spike stop). Only
    updates rows in status='open'; never re-closes. Returns rowcount."""
    cur = conn.execute(
        "UPDATE paper_positions SET status='closed', exit_ts=?, exit_reason=?, "
        "realized_payoff=?, gross_pnl=?, execution_cost=?, net_pnl=?, net_r=? "
        "WHERE currency=? AND entry_ts=? AND expiry=? AND status='open'",
        (int(exit_ts), exit_reason, _f(realized_payoff), _f(gross_pnl),
         _f(execution_cost), _f(net_pnl), _f(net_r),
         currency, int(entry_ts), int(expiry)),
    )
    conn.commit()
    return cur.rowcount if cur.rowcount is not None else 0


def read_open_positions(conn: sqlite3.Connection,
                        currency: str | None = None) -> pd.DataFrame:
    clauses = ["status='open'"]
    params: list = []
    if currency is not None:
        clauses.append("currency=?")
        params.append(currency)
    where = "WHERE " + " AND ".join(clauses)
    return pd.read_sql_query(
        f"SELECT * FROM paper_positions {where} ORDER BY entry_ts ASC",
        conn, params=params)


def read_snapshots(conn: sqlite3.Connection, currency: str | None = None) -> pd.DataFrame:
    where = "" if currency is None else "WHERE currency=?"
    params = [] if currency is None else [currency]
    return pd.read_sql_query(
        f"SELECT * FROM morning_snapshots {where} ORDER BY day ASC",
        conn, params=params)


def read_positions(conn: sqlite3.Connection, currency: str | None = None) -> pd.DataFrame:
    where = "" if currency is None else "WHERE currency=?"
    params = [] if currency is None else [currency]
    return pd.read_sql_query(
        f"SELECT * FROM paper_positions {where} ORDER BY entry_ts ASC",
        conn, params=params)