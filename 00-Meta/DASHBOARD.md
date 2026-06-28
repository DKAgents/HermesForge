---
type: dashboard
created: 2026-06-27
updated: 2026-06-27
tags: [meta, dashboard]
---

# 🏭 HermesForge Dashboard

## 🔥 Active Stories
```dataview
TABLE priority, assigned_to, epic
FROM "02-Backlog/Stories"
WHERE status = "in-progress"
SORT priority DESC
```

## 📋 Ready to Pull (Top Priority)
```dataview
TABLE priority, effort, epic
FROM "02-Backlog/Stories"
WHERE status = "ready"
SORT priority DESC
```

## 📦 Backlog
```dataview
TABLE status, priority, epic
FROM "02-Backlog/Stories"
WHERE status = "backlog"
SORT priority DESC
```

## ✅ Recently Completed
```dataview
TABLE updated, epic
FROM "02-Backlog/Stories"
WHERE status = "done"
SORT updated DESC
LIMIT 10
```

## 📐 Architecture Decisions
```dataview
TABLE status, created, deciders
FROM "03-ADRs"
WHERE type = "adr"
SORT created DESC
```

## 🤖 Agent Roster
```dataview
TABLE file.name AS Agent, status
FROM "01-Agents/Profiles"
SORT file.name ASC
```

## 📓 Recent Journal Entries
```dataview
TABLE date
FROM "09-Journal"
WHERE type = "journal"
SORT date DESC
LIMIT 7
```
