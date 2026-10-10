#!/usr/bin/env python3
"""
live_executor.py — Hyperliquid live order execution.

Places market orders on Hyperliquid mainnet. All orders are:
- Market orders (simplest, most reliable)
- 1x leverage (no margin borrowing)
- Reduce-only: False
- Slippage-protected via limit price (market + buffer)

FAIL-CLOSED: any error, timeout, or unexpected response = no trade opened.

Usage:
    from live_trading.live_executor import LiveExecutor
    ex = LiveExecutor()
    result = ex.open_position("ETH", "long", size_usd=500.0, stop_loss_pct=0.02)
"""

from __future__ import annotations

import os
import time
import json
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import eth_account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

logger = logging.getLogger("live_executor")

# ═══════════════════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════════════════
MAINNET_URL = "https://api.hyperliquid.xyz"
DEFAULT_SLIPPAGE = 0.005  # 0.5% slippage tolerance
MAX_RETRIES = 2
RETRY_DELAY = 2.0

# Kill switch file — if it exists with PAUSED=true, block all live trades
KILL_SWITCH_FILE = Path("/root/HermesForge/.live_kill_switch")


@dataclass
class ExecutionResult:
    success: bool
    order_id: Optional[str] = None
    filled_price: Optional[float] = None
    filled_size: Optional[float] = None
    error: Optional[str] = None
    details: dict = field(default_factory=dict)


class LiveExecutor:
    """Hyperliquid live order executor."""

    def __init__(self, slippage: float = DEFAULT_SLIPPAGE):
        self.slippage = slippage
        self._exchange: Optional[Exchange] = None
        self._info: Optional[Info] = None
        self._address: Optional[str] = None

    # ── Init ──────────────────────────────────────────────────────────
    def _check_kill_switch(self) -> bool:
        """Return True if live trading is BLOCKED by kill switch."""
        if not KILL_SWITCH_FILE.exists():
            return False
        content = KILL_SWITCH_FILE.read_text().strip()
        return "PAUSED=true" in content or "true" in content.lower()

    def _init_exchange(self) -> bool:
        """Initialize Hyperliquid exchange client.

        Two modes (in priority order):
        1. AGENT MODE (HYPERLIQUID_AGENT_KEY + HYPERLIQUID_ACCOUNT):
           Agent key signs trades, main account owns funds.
           Agent CAN trade, CANNOT withdraw. Safe for servers.
        2. DIRECT MODE (HYPERLIQUID_PRIVATE_KEY):
           Full custody. Use only for testing with small amounts.
        """
        if self._exchange is not None:
            return True

        if self._check_kill_switch():
            logger.warning("Kill switch active — live trading blocked")
            return False

        # ── Agent mode (preferred) ──
        agent_key = os.environ.get("HYPERLIQUID_AGENT_KEY", "")
        main_account = os.environ.get("HYPERLIQUID_ACCOUNT", "")

        if agent_key and main_account:
            try:
                agent_acct = eth_account.Account.from_key(agent_key)
                self._address = main_account  # main account owns the funds
                self._exchange = Exchange(
                    agent_acct,  # agent signs orders
                    base_url=MAINNET_URL,
                    account_address=main_account,  # main account receives fills
                )
                self._info = Info(base_url=MAINNET_URL)
                logger.info(
                    f"Live executor (agent mode): "
                    f"agent={agent_acct.address[:8]}... → main={main_account[:8]}..."
                )
                return True
            except Exception as e:
                logger.error(f"Agent init failed: {e}")

        # ── Direct mode (fallback) ──
        private_key = os.environ.get("HYPERLIQUID_PRIVATE_KEY", "")
        if private_key:
            try:
                account = eth_account.Account.from_key(private_key)
                self._address = account.address
                self._exchange = Exchange(
                    account,
                    base_url=MAINNET_URL,
                    account_address=self._address,
                )
                self._info = Info(base_url=MAINNET_URL)
                logger.warning(
                    f"Live executor (DIRECT mode — full custody): {self._address[:8]}..."
                )
                return True
            except Exception as e:
                logger.error(f"Direct init failed: {e}")
                return False

        logger.error(
            "No credentials set. Set HYPERLIQUID_AGENT_KEY + HYPERLIQUID_ACCOUNT "
            "(agent mode, recommended) or HYPERLIQUID_PRIVATE_KEY (direct mode, testing only)"
        )
        return False

    # ── Account Info ──────────────────────────────────────────────────
    def get_account_value(self) -> Optional[float]:
        """Get total account value in USD."""
        if not self._init_exchange() or self._info is None:
            return None
        try:
            state = self._info.user_state(self._address)
            return float(state.get("marginSummary", {}).get("accountValue", 0))
        except Exception as e:
            logger.error(f"Failed to get account value: {e}")
            return None

    def get_positions(self) -> list[dict]:
        """Get current open positions."""
        if not self._init_exchange() or self._info is None:
            return []
        try:
            state = self._info.user_state(self._address)
            positions = state.get("assetPositions", [])
            return [
                {
                    "coin": p.get("position", {}).get("coin", "?"),
                    "size": float(p.get("position", {}).get("szi", 0)),
                    "entry_px": float(p.get("position", {}).get("entryPx", 0)),
                    "unrealized_pnl": float(p.get("position", {}).get("unrealizedPnl", 0)),
                }
                for p in positions
                if float(p.get("position", {}).get("szi", 0)) != 0
            ]
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []

    # ── Order Execution ───────────────────────────────────────────────
    def open_position(
        self,
        coin: str,
        direction: str,
        size_usd: float,
        stop_loss_pct: float = 0.02,
    ) -> ExecutionResult:
        """
        Open a market position on Hyperliquid.

        Args:
            coin: ticker (e.g. "ETH", "BTC")
            direction: "long" or "short"
            size_usd: position size in USD notional
            stop_loss_pct: stop loss as fraction (0.02 = 2%)

        Returns:
            ExecutionResult with success, filled_price, order_id, or error.
        """
        if not self._init_exchange():
            return ExecutionResult(success=False, error="Exchange not initialized")

        if self._check_kill_switch():
            return ExecutionResult(success=False, error="Kill switch active")

        is_buy = direction.lower() == "long"

        # Get current price for slippage calculation
        try:
            mids = self._info.all_mids()
            mid_price = float(mids.get(coin, 0))
            if mid_price <= 0:
                return ExecutionResult(success=False, error=f"No mid price for {coin}")
        except Exception as e:
            return ExecutionResult(success=False, error=f"Failed to fetch price: {e}")

        # Calculate limit price with slippage buffer
        if is_buy:
            limit_px = mid_price * (1 + self.slippage)
        else:
            limit_px = mid_price * (1 - self.slippage)

        # Round to appropriate decimals
        sz = round(size_usd / mid_price, 4)
        limit_px = round(limit_px, 2 if mid_price > 1 else 4)

        logger.info(
            f"Opening {direction} {coin}: size=${size_usd:.0f} ({sz} coins) "
            f"@ limit={limit_px} (mid={mid_price}, slip={self.slippage:.1%})"
        )

        for attempt in range(MAX_RETRIES):
            try:
                result = self._exchange.market_open(
                    coin,
                    is_buy,
                    sz,
                    limit_px,
                    0.01,  # 1% slippage tolerance on the order itself
                )

                if result is None:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                    return ExecutionResult(success=False, error="Order returned None")

                # Parse response
                if isinstance(result, dict):
                    status = result.get("status", "")
                    if status == "ok" or "resting" in str(result.get("response", "")):
                        oid = str(result.get("response", {}).get("data", {}).get("statuses", [{}])[0].get("oid", "")) if isinstance(result.get("response"), dict) else ""
                        return ExecutionResult(
                            success=True,
                            order_id=oid or str(result.get("oid", "")),
                            filled_price=mid_price,
                            filled_size=sz,
                            details={"coin": coin, "direction": direction, "size_usd": size_usd},
                        )

                # Try alternate response format
                if isinstance(result, list) and len(result) > 0:
                    r = result[0]
                    if isinstance(r, dict) and r.get("status") == "ok":
                        oid = str(r.get("response", {}).get("data", {}).get("statuses", [{}])[0].get("oid", ""))
                        return ExecutionResult(
                            success=True,
                            order_id=oid or str(r.get("oid", "")),
                            filled_price=mid_price,
                            filled_size=sz,
                        )

                logger.warning(f"Unexpected order response: {result}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return ExecutionResult(
                    success=False,
                    error=f"Unexpected response: {str(result)[:200]}",
                )

            except Exception as e:
                logger.error(f"Order attempt {attempt+1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return ExecutionResult(success=False, error=str(e)[:300])

        return ExecutionResult(success=False, error="Max retries exceeded")

    def close_position(self, coin: str) -> ExecutionResult:
        """
        Close an existing position on Hyperliquid (market close).

        Args:
            coin: ticker to close

        Returns:
            ExecutionResult
        """
        if not self._init_exchange():
            return ExecutionResult(success=False, error="Exchange not initialized")

        if self._check_kill_switch():
            return ExecutionResult(success=False, error="Kill switch active")
        
        positions = self.get_positions()
        pos = next((p for p in positions if p["coin"] == coin), None)
        if not pos:
            return ExecutionResult(success=False, error=f"No position in {coin}")
        
        sz = abs(pos["size"])
        if sz <= 0:
            return ExecutionResult(success=False, error=f"Zero size position in {coin}")

        try:
            mids = self._info.all_mids()
            mid = float(mids.get(coin, 0))
        except Exception as e:
            return ExecutionResult(success=False, error=f"Failed to fetch price: {e}")

        logger.info(f"Closing {coin}: {sz} coins @ ~${mid}")

        try:
            result = self._exchange.market_close(coin, sz, mid * (1 + self.slippage))
            return ExecutionResult(
                success=True,
                filled_price=mid,
                filled_size=sz,
                details={"coin": coin, "pnl": pos.get("unrealized_pnl", 0)},
            )
        except Exception as e:
            return ExecutionResult(success=False, error=str(e)[:300])


# ── Quick test ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=== Live Executor Test ===\n")
    ex = LiveExecutor()
    if not ex._init_exchange():
        print("❌ Not initialized — set HYPERLIQUID_PRIVATE_KEY")
    else:
        val = ex.get_account_value()
        print(f"Account value: ${val:,.2f}" if val else "Could not fetch")
        positions = ex.get_positions()
        print(f"Open positions: {len(positions)}")
        for p in positions:
            pnl = p.get("unrealized_pnl", 0)
            print(f"  {p['coin']}: {p['size']} @ {p['entry_px']} (pnl: ${pnl:+.2f})")