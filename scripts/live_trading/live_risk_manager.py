#!/usr/bin/env python3
"""
live_risk_manager.py — Live trading risk safeguards.

Hard limits that CANNOT be overridden by JEV, position manager, or any signal.

Rules (checked BEFORE every live trade):
1. Max position size: $500 USD (notional) per trade
2. Daily loss limit: $200 — if hit, pause live trading for the day
3. Max concurrent live positions: 3
4. Max total live exposure: $1,500 USD
5. Circuit breaker: 3 consecutive stop-outs → 4h cooldown
6. Kill switch: /root/HermesForge/.live_kill_switch with PAUSED=true

All limits are HARD — no override path exists in this module.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass, field

# ═══════════════════════════════════════════════════════════════════════════
# Hard Limits (conservative — increase after proven live performance)
# ═══════════════════════════════════════════════════════════════════════════
MAX_POSITION_SIZE_USD = 500.0      # Max notional per trade
MAX_DAILY_LOSS_USD = 200.0         # Hard daily loss stop
MAX_CONCURRENT_POSITIONS = 3       # Max open live positions
MAX_TOTAL_EXPOSURE_USD = 1500.0    # Max total notional exposure
CIRCUIT_BREAKER_STOPS = 3          # Consecutive stop-outs trigger breaker
CIRCUIT_BREAKER_HOURS = 4          # Cooldown after breaker trips

STATE_FILE = Path(os.environ.get(
    "LIVE_RISK_STATE_FILE",
    str(Path.home() / ".hermes" / "live_risk_state.json")
))
KILL_SWITCH_FILE = Path("/root/HermesForge/.live_kill_switch")


@dataclass
class RiskCheck:
    allowed: bool
    reason: str = ""
    current_exposure: float = 0.0
    daily_loss: float = 0.0
    daily_stops: int = 0
    open_positions: int = 0


class LiveRiskManager:
    """Live trading risk safeguard."""

    def __init__(self):
        self._state = self._load_state()

    # ── State ──────────────────────────────────────────────────────────
    def _load_state(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "daily_loss": 0.0,
            "daily_stops": 0,
            "date": "",
            "consecutive_stops": 0,
            "circuit_breaker_until": "",
        }

    def _save_state(self):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self._state, indent=2))

    def _reset_daily(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self._state.get("date") != today:
            self._state = {
                "daily_loss": 0.0,
                "daily_stops": 0,
                "date": today,
                "consecutive_stops": self._state.get("consecutive_stops", 0),
                "circuit_breaker_until": self._state.get("circuit_breaker_until", ""),
            }
            self._save_state()

    # ── Checks ─────────────────────────────────────────────────────────
    def check_kill_switch(self) -> bool:
        """Return True if kill switch is blocking live trades."""
        if not KILL_SWITCH_FILE.exists():
            return False
        content = KILL_SWITCH_FILE.read_text().strip().lower()
        return "paused=true" in content or "true" in content

    def check_circuit_breaker(self) -> bool:
        """Return True if circuit breaker is active."""
        until = self._state.get("circuit_breaker_until", "")
        if not until:
            return False
        try:
            until_dt = datetime.fromisoformat(until)
            if datetime.now(timezone.utc) < until_dt:
                return True
            # Breaker expired — reset
            self._state["circuit_breaker_until"] = ""
            self._state["consecutive_stops"] = 0
            self._save_state()
            return False
        except (ValueError, TypeError):
            return False

    def check_trade(
        self,
        size_usd: float,
        open_positions: list[dict],
        current_exposure_usd: float,
    ) -> RiskCheck:
        """
        Check if a new live trade is allowed.

        Args:
            size_usd: proposed position size in USD
            open_positions: current live positions [{coin, size_usd, ...}]
            current_exposure_usd: total current notional exposure

        Returns:
            RiskCheck with allowed=True/False and reason
        """
        self._reset_daily()

        # 1. Kill switch
        if self.check_kill_switch():
            return RiskCheck(allowed=False, reason="Kill switch active")

        # 2. Circuit breaker
        if self.check_circuit_breaker():
            until = self._state.get("circuit_breaker_until", "?")
            return RiskCheck(allowed=False, reason=f"Circuit breaker active until {until}")

        # 3. Daily loss limit
        daily_loss = self._state.get("daily_loss", 0.0)
        if daily_loss >= MAX_DAILY_LOSS_USD:
            return RiskCheck(
                allowed=False,
                reason=f"Daily loss limit reached (${daily_loss:.0f} >= ${MAX_DAILY_LOSS_USD})",
                daily_loss=daily_loss,
            )

        # 4. Max position size
        if size_usd > MAX_POSITION_SIZE_USD:
            return RiskCheck(
                allowed=False,
                reason=f"Position size ${size_usd:.0f} exceeds max ${MAX_POSITION_SIZE_USD:.0f}",
            )

        # 5. Max concurrent positions
        if len(open_positions) >= MAX_CONCURRENT_POSITIONS:
            return RiskCheck(
                allowed=False,
                reason=f"Max concurrent positions ({len(open_positions)}/{MAX_CONCURRENT_POSITIONS})",
                open_positions=len(open_positions),
            )

        # 6. Max total exposure
        new_exposure = current_exposure_usd + size_usd
        if new_exposure > MAX_TOTAL_EXPOSURE_USD:
            return RiskCheck(
                allowed=False,
                reason=f"Total exposure ${new_exposure:.0f} exceeds max ${MAX_TOTAL_EXPOSURE_USD:.0f}",
                current_exposure=current_exposure_usd,
            )

        return RiskCheck(
            allowed=True,
            reason="Passed all risk checks",
            current_exposure=current_exposure_usd,
            daily_loss=daily_loss,
            open_positions=len(open_positions),
        )

    # ── Recording ──────────────────────────────────────────────────────
    def record_trade_open(self, coin: str, size_usd: float):
        """Record that a trade was opened (no state change needed)."""
        pass

    def record_trade_close(self, pnl_usd: float, was_stop: bool = False):
        """Record trade result. Updates daily loss and stop counter."""
        self._reset_daily()

        if pnl_usd < 0:
            self._state["daily_loss"] = self._state.get("daily_loss", 0.0) + abs(pnl_usd)
            self._state["daily_stops"] = self._state.get("daily_stops", 0) + (1 if was_stop else 0)

        if was_stop:
            self._state["consecutive_stops"] = self._state.get("consecutive_stops", 0) + 1
            if self._state["consecutive_stops"] >= CIRCUIT_BREAKER_STOPS:
                until = (datetime.now(timezone.utc) + timedelta(hours=CIRCUIT_BREAKER_HOURS)).isoformat()
                self._state["circuit_breaker_until"] = until
                self._state["consecutive_stops"] = 0
        else:
            self._state["consecutive_stops"] = 0

        self._save_state()

    def status(self) -> dict:
        """Get current risk status."""
        self._reset_daily()
        return {
            "daily_loss": self._state.get("daily_loss", 0.0),
            "daily_loss_limit": MAX_DAILY_LOSS_USD,
            "daily_stops": self._state.get("daily_stops", 0),
            "consecutive_stops": self._state.get("consecutive_stops", 0),
            "circuit_breaker_until": self._state.get("circuit_breaker_until", ""),
            "circuit_breaker_active": self.check_circuit_breaker(),
            "kill_switch_active": self.check_kill_switch(),
            "max_position": MAX_POSITION_SIZE_USD,
            "max_concurrent": MAX_CONCURRENT_POSITIONS,
            "max_exposure": MAX_TOTAL_EXPOSURE_USD,
        }


# ── Quick test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    rm = LiveRiskManager()
    print("=== Live Risk Manager ===\n")
    status = rm.status()
    for k, v in status.items():
        print(f"  {k}: {v}")

    # Test check
    check = rm.check_trade(size_usd=500.0, open_positions=[], current_exposure_usd=0.0)
    print(f"\n  Trade check ($500 long, 0 open): allowed={check.allowed} reason={check.reason}")

    check2 = rm.check_trade(size_usd=600.0, open_positions=[], current_exposure_usd=0.0)
    print(f"  Trade check ($600 long, 0 open): allowed={check2.allowed} reason={check2.reason}")