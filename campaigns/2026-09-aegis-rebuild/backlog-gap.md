# Backlog gap

Date: 2026-09-27
02-Backlog/Stories exists. No hook requires a US- id in a commit.
A required id would break /usr/local/sbin/hermes-git-sync, which commits without one.
Gate stays off until the sync writes a story id, or human commits are the only ones checked.
