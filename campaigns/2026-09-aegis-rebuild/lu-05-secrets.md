# LU-05: Secrets — Where They Live and Where They Should Live

**Status**: note-only (no code edits)
**Date**: 2026-09-25
**Campaign**: 2026-09-aegis-rebuild

**Source stories**: US-155 (Secrets Not In History), US-121 (blocked — do not
unblock in this story)

---

## Where Hyperliquid / Broker Secrets Are Read Today

The Hyperliquid testnet credentials are read in exactly one file:

**`scripts/hyperliquid/connection_test.py`**

```python
# line 13-15
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/.hermes/.env"))
```

```python
# line 20-21
address = os.environ.get("HYPERLIQUID_TESTNET_AGENT_ADDRESS")
privkey = os.environ.get("HYPERLIQUID_TESTNET_AGENT_PRIVATE_KEY")
```

The script then checks the two values are present (line 23-25), imports the
Hyperliquid SDK (line 28-32), enforces a testnet-only URL guard (line 34-38),
and queries `info.user_state(address)` (line 46) using only the **public
wallet address** — the private key is loaded but never passed to any API call.

### Other secret reads across the codebase

| Env var | Read where | Purpose |
|---|---|---|
| `HYPERLIQUID_TESTNET_AGENT_ADDRESS` | `scripts/hyperliquid/connection_test.py:20` | Testnet wallet addr |
| `HYPERLIQUID_TESTNET_AGENT_PRIVATE_KEY` | `scripts/hyperliquid/connection_test.py:21` | Testnet wallet key (loaded, unused) |
| `TYPESAFE_API_KEY` | `scripts/gauntlet/jev_client.py` (`_load_api_key`) | Jev System One API |
| `ALPACA_API_KEY` / `ALPACA_API_SECRET` | `scripts/data/intraday_provider.py:191-199` | Stock intraday data |
| `FINNHUB_API_KEY` | `scripts/data/fetch_earnings_calendar.py` | Earnings calendar |
| `LUNARCRUSH_API_KEY` | `scripts/data/fetch_lunarcrush.py:75` | Crypto social data |
| `GITHUB_TOKEN` | repo scripts | Git operations |
| `DISCORD_BOT_TOKEN` | `scripts/discord/*` (multiple) | Discord posting |

OKX, Binance, and Bybit are used for **public market data only** (orderbook,
open interest) in `scripts/data/liquidity_heatmap.py` and
`scripts/data/fetch_intraday_crypto.py` — no API keys involved.

All secrets live in a single file: **`/root/.hermes/.env`** — mode `0600`
(`-rw-------`), owned by root.

---

## No Key Is Echoed

Confirmed by inspection:

- `connection_test.py` references `HYPERLIQUID_TESTNET_AGENT_PRIVATE_KEY`
  only by **name** at line 21 (read into a variable) and line 24 (inside a
  "not set" error string). The value itself is never printed. The only echo
  on the wallet side is the **public address** (line 40), which is not sensitive.
- `jev_client.py` reads `TYPESAFE_API_KEY` from env and passes it into the
  Authorization header; it is never written to stdout, a log, a Discord
  message, or a file.
- A grep for `PRIVATE_KEY` across `scripts/` returns only the two
  `connection_test.py` mentions above — neither leaks the value.
- No script uses `os.environ[...]` for a secret followed by a `print`.
- US-155's own body contains no key material (stub story noting the
  `echo`-on-command-line anti-pattern; the actual key was never pasted into
  the story file).

The shell-history leak described in US-155 was a one-time configuration
mistake (using `echo 'TYPESAFE_API_KEY=...'` interactively), not a property
of the codebase. Runtime reads are all via editor-populated `.env` + env var.

---

## Required End State (do not implement)

1. **Secrets live outside `/root/.hermes/.env`.** The 27KB `.env` file holds
   every credential for the whole system, in a path that any root-level
   process can read. Target: move secrets into a dedicated vault
   (`hermes vault add` or `systemd-creds`) so they are encrypted at rest and
   never on the filesystem in cleartext.

2. **Discord cannot cat them.** The `DISCORD_BOT_TOKEN` and webhook handling
   must not provide a path for a Discord-connected agent to read the secret
   store and echo a key back into a channel. The distinction to enforce:
   an agent posting TO Discord may hold a posting token, but an agent
   responding IN Discord must never be able to retrieve arbitrary secrets
   from the store and print them. At minimum, secret values must be
   accessible only to the specific process that needs them (least-privilege),
   not to any shell that inherits the environment.

3. **Key rotation is part of any exposure story.** If any key is ever
   observed in a channel, shell history, or screenshot, rotation at the
   source console (TypeSafe, Hyperliquid, Alpaca, Discord) is a mandatory
   companion step — not deferred.

---

## Invariants

- **Do NOT** paste `.env` contents.
- **Do NOT** create new key files or write secrets anywhere.
- **Do NOT** unblock US-121 (position-size / STR-Q edit boundary).
- **Do NOT** edit `scripts/hyperliquid/`, Jev, or STR-Q files.
- **Do NOT** create agents or register wallets.
- **Do NOT** post. **Do NOT** trade.

---

## Verified

```bash
$ test -f 02-Backlog/Stories/US-155-Secrets-Not-In-History.md && \
  test -d scripts/hyperliquid && echo "both present"
both present

$ ls -la /root/.hermes/.env
-rw------- 1 root root 27073 Sep 20 21:12 /root/.hermes/.env
```

---

## Key Takeaway

Hyperliquid testnet creds are read only by `connection_test.py` via
`load_dotenv(~/.hermes/.env)` + `os.environ.get()`. The private key is
loaded but never used or echoed. All secrets currently live in one cleartext
file at `/root/.hermes/.env`. The required end state is secrets outside that
file (encrypted vault) with least-privilege access so a Discord-connected
agent cannot read and echo them.