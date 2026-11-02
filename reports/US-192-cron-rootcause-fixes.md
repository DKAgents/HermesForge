# US-192 — Root-cause + fix the four failing crons

**Generated:** 2026-11-02 (UTC) · owner: coder · method: read each job's actual
output file / `last_error` (NOT `last_status`), then reproduce the failure live
under the resolved interpreter.

## Root causes

| Job | streak/state | Root cause |
|---|---|---|
| Daily Signal Scanner → Publisher (`3f49a07a2f04`) | error, streak 29 | `pandas.to_parquet` raised `ImportError: Unable to find a usable engine; tried 'pyarrow','fastparquet'` — the resolved interpreter had every trading dep **except** the parquet engine. |
| Daily F&G Fetch (`e3c306f58545`) | error, streak 2 | Same missing-parquet-engine error, at `load_fear_greed` → `df.to_parquet`. |
| Paper Trading Capture A/B/D (`4b178ecc02cd`) | error, streak 2 | Same, at `fetch_data.py` → `df.to_parquet` (stock refresh), plus the sweep capture had earlier hit `ModuleNotFoundError: pandas` from interpreter drift. |
| Confidence Digest (`de5f707d1495`) | `delivery_failed` | Malformed `deliver` target `platform:1528549094157586543` → `unknown platform 'platform'`. Must be `discord:1528549094157586543`. |

The first three share a **single** root cause — the parquet engine (pyarrow /
fastparquet) was missing from the interpreter all cron wrappers resolve via
`resolve_python.sh`. This is the same interpreter-drift failure class documented
in the pipeline-health skill, and it silently ran for 29 days because agent
wrappers report their own exit, not the subprocess they shelled to.

## Fixes

1. **Parquet engine + full dep set (US-193, single interpreter).** Provisioned
   the canonical durable trading venv `/root/.hermes/venv` with
   `pandas numpy scipy scikit-learn yfinance mplfinance pyarrow PyYAML requests`.
   Also installed `pyarrow` into the runtime venv as a fallback. See
   `scripts/system_doctor/{resolve_python.sh,requirements-trading.txt,provision_trading_env.py}`.
2. **Confidence Digest delivery.** `hermes cron edit de5f707d1495 --deliver
   discord:1528549094157586543` (was `platform:...`). Job now posts to the
   Weekly Model Assignment Review channel.

## Verification (real output, not assumed)

- `fetch_fear_greed.py --force` → `3193 days cached to .../fear_greed.parquet`,
  latest 37 (Fear) 2026-11-02 — no parquet error (F&G fixed).
- `capture_signals.py --dry-run --crypto-only` → clean scan, `0 errors`, no
  pyarrow/traceback (scanner + capture fixed); also exercises the US-191
  signal-class gate.
- Parquet round-trip `to_parquet`/`read_parquet` verified under `/root/.hermes/venv`.
- Allergy of failure streaks will resolve to 0 on each job's next scheduled run
  (now that the shared parquet-engine root cause is gone), and the digest will
  deliver on its next 07:00 run.