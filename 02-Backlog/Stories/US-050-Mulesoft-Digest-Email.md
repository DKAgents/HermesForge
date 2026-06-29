---
id: US-050-Mulesoft-Digest-Email
type: user-story
epic: "[[Epics/EPIC-006-General-Automations]]"
status: backlog
priority: low
effort: M
created: 2026-06-27
updated: 2026-06-27
assigned_to: ""
tags: [backlog, story, email, automation, mulesoft]
---

# US-050: Weekly Mulesoft Feature Digest Email to Stalin

## Story
**As a** developer,  
**I want** an automated weekly email sent to Stalin every Friday,  
**So that** he stays up to date on new Mulesoft features launched that week without any manual effort.

## Acceptance Criteria
- [ ] Every Friday, Hermes researches Mulesoft feature releases from that week (official blog, release notes, Anypoint changelog)
- [ ] Email is written in a clear, human-sounding summary (not AI-like or hype-y)
- [ ] Email is sent to Stalin's email address from the configured sending account
- [ ] Email includes links to original sources
- [ ] If the job fails, an alert is delivered to Discord

## Notes / Context
- Mulesoft sources: official blog, MuleSoft Anypoint Platform changelog, release notes page
- Sending via himalaya CLI (IMAP/SMTP)
- **Do not paste SMTP credentials in Discord** — configure via VPS terminal or `~/.hermes/.env`
- Still need: Stalin's email, your sending email + provider, app password

## Dependencies
- Blocked by: himalaya CLI installed + SMTP credentials configured on VPS

## Definition of Done
- [ ] himalaya installed and SMTP configured
- [ ] Cron job created and tested
- [ ] First email sent and confirmed received
- [ ] Story documented in vault
