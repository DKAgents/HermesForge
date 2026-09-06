]633;E;echo "# hermes-version";a7f96ce1-10cf-4a30-9f9d-9654dd49fc45]633;C# hermes-version
Hermes Agent v0.20.6 (2026.8.27) · upstream 26350357
Install directory: /usr/local/lib/hermes-agent
Install method: git
Python: 3.11.15
OpenAI SDK: 2.24.0
Update available: 5917 commits behind — run 'hermes update'

# profiles

 Profile          Model                        Gateway      Alias        Distribution
 ───────────────    ───────────────────────────    ───────────    ───────────    ────────────────────
 ◆default         deepseek/deepseek-v4-pro     running      —            —
  aegis-auditor   anthropic/claude-opus-4.8    stopped      aegis-auditor —
  architect       —                            stopped      architect    —
  backtester      —                            stopped      backtester   —
  coder           —                            stopped      coder        —
  consulting      —                            stopped      consulting   —
  documenter      —                            stopped      documenter   —
  orchestrator    —                            stopped      orchestrator —
  product-owner   —                            stopped      product-owner —
  publisher       —                            stopped      —            —
  red-team        deepseek/deepseek-v4-flash   stopped      —            —
  researcher      —                            stopped      researcher   —
  risk-guardian   —                            stopped      risk-guardian —
  trading         —                            stopped      trading      —


# aegis model
5:  default: anthropic/claude-opus-4.8
6:  provider: openrouter
47:#   provider: openrouter

# crons

┌─────────────────────────────────────────────────────────────────────────┐
│                         Scheduled Jobs                                  │
└─────────────────────────────────────────────────────────────────────────┘

  98a07007974b [active]
    Name:      LinkedIn Post Generator [T3]
    Schedule:  30 5 * * 2,4
    Repeat:    ∞
    Next run:  2026-09-08T05:30:00+00:00
    Deliver:   discord:1518731579067728003
    Last run:  2026-09-03T05:36:05.890547+00:00  ok

  79c465c541f2 [active]
    Name:      CRON-001-Market-Intelligence [T3]
    Schedule:  0 13 * * 1-5
    Repeat:    ∞
    Next run:  2026-09-07T13:00:00+00:00
    Deliver:   discord:1532020053548208328
    Last run:  2026-09-04T13:02:25.985090+00:00  ok

  9d77b5c75db7 [active]
    Name:      HermesForge Vault Maintenance [T3]
    Schedule:  0 2 * * *
    Repeat:    ∞
    Next run:  2026-09-07T02:00:00+00:00
    Deliver:   origin
    Last run:  2026-09-06T02:01:19.368418+00:00  ok
    Execution: completed  492a466303174b399ea67525eca5453b

  232975d5fc83 [active]
    Name:      HermesForge Connection Discovery [T3]
    Schedule:  0 4 * * *
    Repeat:    ∞
    Next run:  2026-09-07T04:00:00+00:00
    Deliver:   origin
    Script:    discover_connections_wrapper.sh
    Last run:  2026-09-06T04:09:13.605557+00:00  ok
    Execution: completed  c9b4302175874ddfa5c57373ddb0c2d5

  07149d6b05cc [active]
    Name:      Weekly Model Assignment Review [T3]
    Schedule:  0 9 * * 1
    Repeat:    6/52
    Next run:  2026-09-07T09:00:00+00:00
    Deliver:   discord:1528549094157586543
    Script:    model_review.py
    Last run:  2026-08-31T09:03:46.666422+00:00  ok

  3f49a07a2f04 [active]
    Name:      Daily Signal Scanner → Discord Publisher
    Schedule:  45 14 * * *
    Repeat:    ∞
    Next run:  2026-09-07T14:45:00+00:00
    Deliver:   local
    Script:    daily_publish_wrapper.sh
    Mode:      no-agent (script stdout delivered directly)
    Last run:  2026-09-06T14:45:32.482720+00:00  ok
    Execution: completed  8086886e44b2403cb1e0f779a8e0c372

  a76bfb516675 [active]
    Name:      ADR-005 Rollout Readiness Check
    Schedule:  0 14 * * 1
    Repeat:    ∞
    Next run:  2026-09-07T14:00:00+00:00
    Deliver:   origin
    Last run:  2026-08-31T14:01:44.451994+00:00  ok

  4b178ecc02cd [active]
    Name:      Paper Trading Capture (A/B/D)
    Schedule:  50 14 * * *
    Repeat:    ∞
    Next run:  2026-09-07T14:50:00+00:00
    Deliver:   origin
    Script:    capture_signals_wrapper.sh
    Mode:      no-agent (script stdout delivered directly)
    Last run:  2026-09-06T14:50:53.802824+00:00  ok
    Execution: completed  fb3612cc9f714331aa041cc46fa68f01

  356f3c4fb973 [active]
    Name:      Auto-Crosspost Daily Briefing
    Schedule:  5 13 * * 1-5
    Repeat:    ∞
    Next run:  2026-09-07T13:05:00+00:00
    Deliver:   local
    Script:    webhook_crosspost.sh
    Mode:      no-agent (script stdout delivered directly)
    Last run:  2026-09-04T13:05:09.223496+00:00  ok

  d1e07c3f4543 [active]
    Name:      HermesForge Trade Monitor [T3]
    Schedule:  every 60m
    Repeat:    ∞
    Next run:  2026-09-06T20:25:31.999901+00:00
    Deliver:   origin
    Last run:  2026-09-06T19:25:31.999901+00:00  ok
    Execution: completed  de626bf46186457ba683597e1f3be09c

  9202661b7823 [active]
    Name:      HermesForge Weekly Research Pipeline [T3]
    Schedule:  0 12 * * 0
    Repeat:    ∞
    Next run:  2026-09-13T12:00:00+00:00
    Deliver:   discord:1534834809451450409
    Last run:  2026-09-06T12:18:43.335550+00:00  ok
    Execution: completed  08382ddfd35e45dd9945a3c21c7b85ff

  cb22b038a6d6 [active]
    Name:      HermesForge Paper Trading Performance Report [T3]
    Schedule:  0 13 * * *
    Repeat:    ∞
    Next run:  2026-09-07T13:00:00+00:00
    Deliver:   origin
    Last run:  2026-09-06T13:00:38.379844+00:00  ok
    Execution: completed  d9eb39daa4b94dd2a766f44c86aa8f8b

  e214a9d8f348 [active]
    Name:      HermesForge External Edge Discovery [T3]
    Schedule:  0 16 * * 2,4,0
    Repeat:    ∞
    Next run:  2026-09-08T16:00:00+00:00
    Deliver:   discord:1534834809451450409
    Last run:  2026-09-06T16:07:07.746548+00:00  ok
    Execution: completed  5d4b947dbd0f4f5c8f814c5fe94efb5e

  2d8dff498d1f [active]
    Name:      HermesForge Autonomous Strategy Pipeline [T3]
    Schedule:  0 17 * * 2,4,0
    Repeat:    ∞
    Next run:  2026-09-08T17:00:00+00:00
    Deliver:   discord:1534834809451450409
    Last run:  2026-09-06T17:10:23.102737+00:00  ok
    Execution: completed  612db59ee24b45449a9f0018b3351459

  b9fb0afb1e29 [active]
    Name:      STR-Q Intraday Sweep Capture [T3]
    Schedule:  */5 * * * *
    Repeat:    ∞
    Next run:  2026-09-06T20:05:00+00:00
    Deliver:   local
    Script:    capture_sweep_wrapper.sh
    Mode:      no-agent (script stdout delivered directly)
    Last run:  2026-09-06T20:00:38.167833+00:00  ok
    Execution: completed  f080c0c59195491e8f7a0ecd3d149493

  98edbe73d115 [active]
    Name:      Vault Connection Weaver
    Schedule:  every 240m
    Repeat:    ∞
    Next run:  2026-09-06T23:50:37.082872+00:00
    Deliver:   local
    Last run:  2026-09-06T19:50:37.082872+00:00  ok
    Execution: completed  ea20c28f8bc54576a8c416a66eb65359

  23471396797f [active]
    Name:      STR-Q Position Size Re-eval Check [T3]
    Schedule:  every monday 9am
    Repeat:    ∞
    Next run:  2026-09-07T09:00:00+00:00
    Deliver:   origin
    Last run:  2026-08-31T09:00:49.660142+00:00  ok

  df2caa178eaa [active]
    Name:      Daily Git Push to GitHub
    Schedule:  every day at 3am
    Repeat:    ∞
    Next run:  2026-09-07T03:00:00+00:00
    Deliver:   local
    Script:    daily_git_push.sh
    Mode:      no-agent (script stdout delivered directly)
    Last run:  2026-09-06T03:00:13.702554+00:00  ok
    Execution: completed  a326ce2265324a51bb92e71cbdadf466

  61cccd31ed5c [active]
    Name:      Webhook Crosspost All Channels
    Schedule:  */5 * * * *
    Repeat:    ∞
    Next run:  2026-09-06T20:05:00+00:00
    Deliver:   local
    Script:    crosspost_webhook_all.sh
    Mode:      no-agent (script stdout delivered directly)
    Last run:  2026-09-06T20:00:28.281149+00:00  ok
    Execution: completed  c117872377014538aac98b56b56f8f30

  65dfc591efad [active]
    Name:      Cron Watchdog (no-agent)
    Schedule:  */15 * * * *
    Repeat:    ∞
    Next run:  2026-09-06T20:15:00+00:00
    Deliver:   local
    Script:    cron_watchdog.py
    Mode:      no-agent (script stdout delivered directly)
    Last run:  2026-09-06T20:00:24.769380+00:00  ok
    Execution: completed  370b48e1ae3a41398ae03a05e9e98585


# skills (aegis)
│ aegis-rebuild │ governance           │ local   │ local   │ enabled │
