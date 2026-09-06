# Campaign Brief builder notes

Create `campaigns/<id>/` before invoking `aegis-rebuild`. Prefer a no-agent script. Do not put secrets in these files.

## GOALS.md

Restate HermesForge goals and the numeric meaning of “more effective / robust / efficient” for this campaign.

## inventory.yaml

```yaml
campaign_id: 2026-09-aegis-rebuild
hermes_version: "0.20.6"
profiles: []          # name, model_floor, toolsets, always_load_skills, writable_paths
crons: []             # name, schedule, agent|no-agent, model, deliver, writes
repos: []
data_roots: []        # read-only descriptions, not copied into git
discord_channels: []  # names only, not webhook URLs
publisher_owned_files: []
```

## hermes-version.md

Installed version, last `hermes update --plan` receipt if any, notable features vs previous campaign.

## context-budgets.md

Paste `/context` dumps for orchestrator, researcher, trade monitor, weaver, strategy pipeline.

## cost-30d.md

Tokens and estimated $ by job for the last 30 days. No API keys.

## data-manifest.md

```text
trades_rows:
last_signal_id:
last_trade_ts_pt:
snapshot_last_ok:
offbox_last_ok:
restore_drill_last_ok:
fear_greed_last_ok:
crosspost_state_bytes:
```

## failure-log.md

Incidents and class of defect (e.g. truncate-write, split exit path, 0% pipeline ship).

## constraints.md

RAM, disk, paper-only, 1% cap, publisher monopoly, vault-on-VPS.

## current-adrs.md

Links or copies of ADR-001 and any persist / campaign ADRs.
