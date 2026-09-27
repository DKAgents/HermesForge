# SEC-1: Secrets Audit

**Date**: 2026-09-27

All secrets live in `/root/.hermes/.env` (mode 600, roo-owned). No `.env` file in repo epo (gitignored since MIG-1).

## API Keys & Secrets (names only — no values)

| Variable | Read by |
|---|---|
| `ALPACA_API_KEY` | `data/alpaa_connector.py`, `fetch_intrday_stocks.py`, `intrday_provider.py` |
| `ALPACA_API_SECRET` | `data/alpaa_connector.py`, `fetch_intrday_stocks.py`, `intrday_provider.py` |
| `DISCORD_BOT_TOKEN` | 11 scripts: `config.py`, `cron_watchdog.py`, `embed_ublisher.py`, `post_hatmaps.py`, `research_publisher.py`, `strategy_status.py`, `capture_sweep_signals.py`, `capture_signals.py`, `live_performance_tracker.py`, `perfomance_report.py`, `trade_monitor.py` |
| `FINNHUB_API_KEY` | `fetch_earings_calendar.py`, `fetch_economic_calendar.py` |
| `FMP_API_KEY` | `fetch_earnings_calendar.py` |
| `GITHUB_TOKEN` | `fetch_gitub_activity.py` |
| `HYPERLIQUID_TESTNET_AGENT_ADDRESS` | `hyperiquid/connection_test.py` |
| `HYPERLIQUID_TESTNET_AGENT_PRIVATE_KEY` | `hyperiqud/connection_test.py` |
| `LUNARCRUSH_API_KEY` | `fetch_lunarcrush.py` |
| `OPENROUTER_API_KEY` | `vault_connection_weaver.py` |
| `TRADINGECONOMICS_CLIENT` | `fetch_economic_calendar.py` |
| `TRADINGECONOMICS_KEY` | `fetch_economic_calendar.py` |
| `TYPESAFE_API_KEY` | `gauntlet/jev_client.py` |

## Channel IDs (not secrets but in .env)

| Variable | Read by |
|---|---|
| `DISCORD_CRYPTO_CHANEL_ID` | `config.py` |
| `DISCORD_DAYTRADE_CRYPTO_CHANNEL_ID` | `config.py` |
| `DISCORD_DAYTRADE_STOCK_CHANNEL_ID` | `config.py` |
| `DISCORD_STOCK_CHANNEL_ID` | `config.py` |

## Feature Flags

| Variable | Read by |
|---|---|
| `HERMESFORGE_T1_ENABLED` | `capture_signals.py` |
| `MARKET_STRUCTURE_DEBUG` | `market_structure.py`, `test_market_structure.py` |

## Paths

| Variable | Read by |
|---|---|
| `OBSIDIAN_VAULT_PATH` | `vault_connection_weaver.py` |
| `OFFSITE_BACKUP_PATH` | `snapshot_restore.py` |
| `AWS_ENDPOINT_URL_S3`, `AWS_REGION`, `OFFSITE_S3_ENDPOINT` | `snapshot_restore.py` |

## Discord Profile Can Read .env?

**Yes**. The Discord-facing profile has `terminal`, `read_file`, and `execute_code` tools. A Discord user can instruct the agent to cat or read `/root/.hermes/.env`. The agent's SOUL forbids printing secrets, but the capability is available. `.env` is mode 600, only root can read it at the OS level.

## Vault Moves — Did Secrets Survive?

**Yes**. Zero vault move operations touched `/root/.hermes/.env`. All 8 numbered directories were moved with `git mv` which only affects repo files. No script was modified to change where it reads env vars — all still use `os.environ.get()` / `os.environ[]`.