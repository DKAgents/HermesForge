"""hl_assetctx_listener.py — US-199 (EPIC-017 Phase 1) persistent assetCtxs listener.

Replaces the HOURLY snapshot with a PERSISTENT websocket listener so mark/oracle
basis + open interest + funding accrue continuously (minute-level or finer).

CHANNEL (verified live 2026-11-02): Hyperliquid's ``assetCtxs`` websocket
channel. NOTE: the architect spec's assumed name ``activeAssetCtx`` is REJECTED
by HL's websocket (it returns an ``error`` channel, exactly like ``liquidation``).
The correct, working channel is ``assetCtxs``, which pushes
``{"channel":"assetCtxs","data":{"dex":"","ctxs":[{...per-coin ctx...}]}}``
every ~2–5 seconds. The ``ctxs`` array carries NO coin name and NO timestamp; it
is INDEX-ALIGNED with ``meta.universe`` (verified 235 == 235), so the listener
maps ``ctxs[i]`` -> ``universe[i].name`` and skips ``isDelisted`` coins. Receipt
time is assigned as the ``time`` (ms epoch).

Fallback (fail-open transport, fail-closed data): if the push channel is
unavailable, the listener degrades to a 60s POLL of the REST ``metaAndAssetCtxs``
endpoint — correct-but-slower, never a fabricated bar.

Design invariants (architect_us199_metaassetctx_websocket_spec.md):
  * source provenance ``ws`` / ``poll`` / ``backfill`` on every row.
  * Reconnect with exponential backoff (1s..30s cap), forever (daemon, not cron).
  * On reconnect, backfill the gap via ONE REST snapshot (source='backfill')
    BEFORE resuming stream appends; ``INSERT OR IGNORE`` makes overlap harmless.
  * If BOTH stream and REST backfill fail for a window (> GAP_THRESHOLD_SEC), a
    gap is recorded in ``assetctx_gaps`` — NEVER interpolated / last-known-good.
  * Fail-closed: malformed / truncated / length-mismatched frames are dropped
    and logged, never partially parsed into fabricated rows. A ws ``ctxs`` array
    whose length does not match the cached universe is SKIPPED (a stale universe
    must be refreshed first) to avoid silent index mislabeling.
  * Single connection, single process, no unbounded queue.

Usage:
    python3 hl_assetctx_listener.py --probe                  # verify channel only
    python3 hl_assetctx_listener.py --max-messages 3          # bounded soak
    python3 hl_assetctx_listener.py --soak-seconds 60         # bounded soak
    python3 hl_assetctx_listener.py --once                    # single REST poll
    python3 hl_assetctx_listener.py                           # run forever (daemon)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time

import hl_assetctx_store as store

try:
    from ingest_hl_assetctx import fetch_assetctxs  # REST metaAndAssetCtxs
except ImportError:  # pragma: no cover
    fetch_assetctxs = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("hl_assetctx_listener")

WS_URL = "wss://api.hyperliquid.xyz/ws"
CHANNEL = "assetCtxs"  # verified; NOT 'activeAssetCtx' (rejected)

POLL_INTERVAL_SEC = 60            # REST fallback cadence
COIN_MAP_REFRESH_SEC = 6 * 3600   # refresh universe (new listings) every 6h
GAP_THRESHOLD_SEC = 300           # 5 min silence = a gap (spec §2.2.3)
RECONNECT_BACKOFF = (1, 2, 4, 8, 16, 30)  # seconds, capped at 30
WS_READ_TIMEOUT_SEC = 90          # recv timeout -> forced reconnect/backfill


def _now_ms() -> int:
    return int(time.time() * 1000)


def _f(v):
    """float-or-None, never raises (fail-closed on non-numeric)."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def build_coin_map(meta: dict) -> list:
    """[(name, isDelisted), ...] aligned with meta.universe (and the ws ctxs)."""
    universe = meta.get("universe", []) or []
    return [
        {"name": u.get("name"), "isDelisted": bool(u.get("isDelisted"))}
        for u in universe
    ]


def _ctx_row(coin: str, ctx: dict, ts_ms: int) -> dict:
    return {
        "coin": coin,
        "time": ts_ms,
        "mark_px": _f(ctx.get("markPx")),
        "oracle_px": _f(ctx.get("oraclePx")),
        "funding": _f(ctx.get("funding")),
        "premium": _f(ctx.get("premium")),
        "open_interest": _f(ctx.get("openInterest")),
        "day_ntl_vlm": _f(ctx.get("dayNtlVlm")),
        "day_base_vlm": _f(ctx.get("dayBaseVlm")),
        "prev_day_px": _f(ctx.get("prevDayPx")),
    }


class AssetCtxListener:
    def __init__(self):
        self.universe: list = []      # [{name, isDelisted}] index-aligned
        self.universe_ts: float = 0.0
        self.last_frame_ts: int = 0   # wall ms of last processed ws frame
        self.conn = None

    # -- store / universe ------------------------------------------------

    def open(self) -> None:
        self.conn = store.open_store()

    def close(self) -> None:
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def refresh_universe(self) -> None:
        meta, _ = fetch_assetctxs()
        self.universe = build_coin_map(meta)
        self.universe_ts = time.time()
        log.info("universe refreshed: %d assets", len(self.universe))

    def universe_stale(self) -> bool:
        return not self.universe or time.time() - self.universe_ts > COIN_MAP_REFRESH_SEC

    # -- parsing ---------------------------------------------------------

    def _parse_ws(self, data: dict, ts_ms: int):
        ctxs = data.get("ctxs")
        if not isinstance(ctxs, list):
            log.warning("ws frame malformed (no ctxs list): dropped")
            return None
        # Length-safety: a stale cached universe would silently mislabel coins.
        # If lengths diverge (e.g. a new listing), skip this frame — never write
        # a possibly-misaligned row — and force a universe refresh.
        if len(ctxs) != len(self.universe):
            log.warning(
                "ws ctxs length %d != universe %d — refreshing universe, "
                "skipping frame (no mislabeled writes)", len(ctxs), len(self.universe)
            )
            try:
                self.refresh_universe()
            except Exception:
                pass
            # Re-check; if STILL mismatched, drop (fail-closed).
            if len(ctxs) != len(self.universe):
                return None
        rows = []
        for i, ctx in enumerate(ctxs):
            if not isinstance(ctx, dict):
                continue
            cfg = self.universe[i]
            if cfg["isDelisted"] or not cfg["name"]:
                continue
            rows.append(_ctx_row(str(cfg["name"]), ctx, ts_ms))
        return rows

    def _parse_rest(self, ctxs: list, ts_ms: int):
        """Parse REST metaAndAssetCtxs ctxs (index-aligned with self.universe)."""
        rows = []
        for i, ctx in enumerate(ctxs):
            if not isinstance(ctx, dict):
                continue
            cfg = self.universe[i] if i < len(self.universe) else None
            if cfg is None or cfg["isDelisted"] or not cfg["name"]:
                continue
            rows.append(_ctx_row(str(cfg["name"]), ctx, ts_ms))
        return rows

    # -- write -----------------------------------------------------------

    def write_rows(self, rows: list, source: str) -> int:
        if not rows:
            return 0
        return store.append_snapshot(self.conn, rows, source=source)

    def last_persisted_ms(self) -> int | None:
        row = self.conn.execute("SELECT MAX(time) FROM asset_ctx").fetchone()
        return row[0] if row and row[0] is not None else None

    # -- transports ------------------------------------------------------

    def poll_once(self, source: str = "poll") -> bool:
        """One REST metaAndAssetCtxs fetch -> refresh universe + append rows.

        Returns True on success. Used for both the 60s poll fallback
        (source='poll') and gap backfill (source='backfill')."""
        if fetch_assetctxs is None:
            return False
        try:
            meta, ctxs = fetch_assetctxs()
            self.universe = build_coin_map(meta)
            self.universe_ts = time.time()
        except Exception as e:
            log.error("REST fetch failed (%s): %s", source, e)
            return False
        rows = self._parse_rest(ctxs, _now_ms())
        try:
            self.write_rows(rows, source=source)
        except Exception as e:
            log.error("write failed (%s): %s", source, e)
            return False
        return True

    def record_gap_window(self, gap_start: int, gap_end: int) -> None:
        """Record a gap for every non-delisted coin (both transports failed)."""
        coins = [cfg["name"] for cfg in self.universe
                 if cfg["name"] and not cfg["isDelisted"]]
        for c in coins:
            try:
                store.record_gap(self.conn, c, gap_start, gap_end)
            except Exception as e:
                log.error("gap record failed for %s: %s", c, e)
        log.warning("gap recorded for %d coins: %d -> %d",
                    len(coins), gap_start, gap_end)

    def backfill(self) -> bool:
        """On reconnect: backfill the gap via one REST snapshot (source='backfill').

        Returns True if the REST backfill succeeded (gap covered by a current
        point); False if it also failed (-> record gap ledger)."""
        last = self.last_persisted_ms()
        now = _now_ms()
        if last is not None and now - last >= GAP_THRESHOLD_SEC * 1000:
            log.info("backfill: covering gap %d -> %d", last, now)
        ok = self.poll_once(source="backfill")
        if not ok and last is not None and now - last >= GAP_THRESHOLD_SEC * 1000:
            self.record_gap_window(last, now)
        return ok

    # -- websocket -------------------------------------------------------

    async def _stream(self, max_messages: int | None,
                      soak_seconds: int | None) -> int:
        import websockets
        started = time.time()
        received = 0
        try:
            async with websockets.connect(
                WS_URL, ping_interval=20, close_timeout=5
            ) as ws:
                await ws.send(json.dumps(
                    {"method": "subscribe", "subscription": {"type": CHANNEL}}
                ))
                log.info("subscribed to channel=%r", CHANNEL)
                while True:
                    try:
                        raw = await asyncio.wait_for(
                            ws.recv(), timeout=WS_READ_TIMEOUT_SEC)
                    except asyncio.TimeoutError:
                        log.warning("ws read timeout -> forcing reconnect/backfill")
                        return received  # triggers reconnect + backfill
                    received += 1
                    self._handle_frame(raw)
                    if max_messages is not None and received >= max_messages:
                        return received
                    if soak_seconds is not None \
                            and time.time() - started >= soak_seconds:
                        return received
        except websockets.exceptions.ConnectionClosed as e:
            log.warning("ws closed: %s", e)
            return received
        except Exception as e:
            log.warning("ws stream error: %s", e)
            return received

    def _handle_frame(self, raw: str) -> None:
        try:
            d = json.loads(raw)
        except (ValueError, TypeError):
            log.warning("ws frame not JSON — dropped (fail-closed)")
            return
        ch = d.get("channel")
        if ch == "assetCtxs":
            data = d.get("data")
            if not isinstance(data, dict):
                log.warning("assetCtxs frame with non-dict data — dropped")
                return
            rows = self._parse_ws(data, _now_ms())
            if rows is None:
                return  # malformed / length-mismatch: dropped by design
            try:
                self.write_rows(rows, source="ws")
            except Exception as e:
                log.error("ws write failed: %s", e)
                return
            self.last_frame_ts = _now_ms()
        elif ch == "error":
            log.error("ws error channel: %s", d)
        elif ch == "subscriptionResponse":
            pass  # ignore ack
        # any other channel is ignored

    # -- main loops ------------------------------------------------------

    async def run(self, max_messages: int | None = None,
                  soak_seconds: int | None = None) -> None:
        self.open()
        try:
            if self.universe_stale():
                try:
                    self.refresh_universe()
                except Exception as e:
                    log.error("initial universe fetch failed: %s", e)

            backoff_i = 0
            while True:
                # Reconnect loop with exponential backoff, forever.
                try:
                    n = await self._stream(max_messages, soak_seconds)
                    if max_messages is not None and n >= max_messages:
                        return
                    if soak_seconds is not None:
                        return
                    # disconnected -> backfill the gap before reconnecting
                    self.backfill()
                except Exception as e:
                    log.error("listener loop error: %s", e)
                    self.backfill()

                # (re)connect backoff
                delay = RECONNECT_BACKOFF[min(backoff_i, len(RECONNECT_BACKOFF) - 1)]
                backoff_i += 1
                log.info("reconnect in %ds", delay)
                await asyncio.sleep(delay)

                if backoff_i % 3 == 0 and self.universe_stale():
                    try:
                        self.refresh_universe()
                    except Exception:
                        pass
        finally:
            self.close()

    def run_poll_forever(self, max_messages: int | None = None) -> None:
        """60s poll fallback (used when the push channel is unavailable)."""
        self.open()
        try:
            while True:
                self.poll_once(source="poll")
                if max_messages is not None:
                    return
                time.sleep(POLL_INTERVAL_SEC)
        finally:
            self.close()


async def _probe() -> int:
    """Read-only channel probe: subscribe and report the first message shape."""
    import websockets
    print(f"probe: connecting {WS_URL} subscribing channel={CHANNEL!r}")
    async with websockets.connect(WS_URL, ping_interval=20, close_timeout=5) as ws:
        await ws.send(json.dumps(
            {"method": "subscribe", "subscription": {"type": CHANNEL}}))
        t0 = time.time()
        while time.time() - t0 < 30:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=8)
            except asyncio.TimeoutError:
                continue
            d = json.loads(raw)
            ch = d.get("channel")
            if ch == "error":
                print(f"probe: channel={CHANNEL!r} REJECTED: {d.get('data')}")
                return 1
            if ch == CHANNEL:
                data = d.get("data")
                nctx = len(data.get("ctxs", [])) if isinstance(data, dict) else 0
                keys = sorted(data["ctxs"][0].keys()) if (isinstance(data, dict)
                        and data.get("ctxs")) else []
                print(f"probe: channel={CHANNEL!r} OK — {nctx} ctxs, "
                      f"first-ctx keys={keys}")
                return 0
        print(f"probe: channel={CHANNEL!r} no message in 30s")
        return 2


def main() -> int:
    p = argparse.ArgumentParser(description="Persistent HL assetCtxs listener (US-199)")
    p.add_argument("--probe", action="store_true", help="read-only channel probe")
    p.add_argument("--once", action="store_true", help="single REST poll append")
    p.add_argument("--poll", action="store_true", help="run 60s poll fallback forever")
    p.add_argument("--max-messages", type=int, default=None,
                   help="exit after N ws frames (bounded soak)")
    p.add_argument("--soak-seconds", type=int, default=None,
                   help="exit after N seconds (bounded soak)")
    args = p.parse_args()

    if args.probe:
        return asyncio.run(_probe())
    if args.once:
        lst = AssetCtxListener()
        lst.open()
        try:
            ok = lst.poll_once(source="poll")
        finally:
            lst.close()
        print(f"once: ok={ok}")
        return 0 if ok else 1
    if args.poll:
        AssetCtxListener().run_poll_forever(max_messages=args.max_messages)
        return 0

    asyncio.run(AssetCtxListener().run(
        max_messages=args.max_messages, soak_seconds=args.soak_seconds))
    return 0


if __name__ == "__main__":
    sys.exit(main())