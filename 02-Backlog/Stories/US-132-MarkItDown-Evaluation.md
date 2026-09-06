---
id: US-132
epic: EPIC-014
type: story
status: ready
created: 2026-09-06
priority: medium
tags: [backlog, infra, document-ingestion, evaluation, markdown]
campaign: 2026-09-aegis-rebuild
train: 2
owner_profile: coder
model_floor: T3
points: 2
---

# US-132 — Evaluate Microsoft MarkItDown for document ingestion

## Story

As the HermesForge knowledge pipeline, I need to evaluate whether Microsoft's
[MarkItDown](https://github.com/microsoft/markitdown) library can replace or
consolidate the current document-ingestion stack so that trading books, PDFs,
research papers, and Office documents produce higher-quality Markdown for LLM
consumption with fewer dependencies.

## Background

The current ingestion stack uses:

| Tool | Format | Pain point |
|------|--------|-----------|
| `pymupdf` (fitz) | PDF text extraction | Loses structure (headings, tables, lists) |
| `marker-pdf` | PDF → Markdown | Heavy dependency (torch, 2+ GB); slow |
| `python-docx` / `python-pptx` | Office docs | Hand-written conversion logic, no unified path |
| `ebooklib` + custom | EPUB | Fragile; loses chapter structure |

Microsoft's MarkItDown is a lightweight Python utility that converts 20+
formats to Markdown: PDF, DOCX, PPTX, XLSX, HTML, images (via LLM description),
audio (via transcription), EPUB, ZIP, CSV, JSON, XML, and more. It's
specifically built for LLM ingestion pipelines.

## Acceptance

- [ ] Install MarkItDown and test against 5 representative documents from the
      vault ingestion queue (1 PDF paper, 1 trading book EPUB, 1 DOCX report,
      1 PPTX deck, 1 HTML page)
- [ ] Compare Markdown output quality vs current stack for each format:
      heading preservation, table fidelity, list structure, character errors
- [ ] Measure: lines of code that could be removed if MarkItDown replaces
      3+ existing dependencies
- [ ] Measure: dependency weight (MB installed) vs current stack
- [ ] Measure: conversion speed (seconds per page/format) vs current stack
- [ ] Decision recorded as ACCEPT / REJECT / CONDITIONAL in story comments
      with evidence table

## Success criteria

- MarkItDown output is at least as good as current stack for ≥3 of 5 formats
- Replaces ≥2 existing dependencies with measurable code/LoC savings
- No new C dependencies or GPU requirements
- Fits in the existing Python 3.11 venv without conflicts

## Forbidden

- No production data path changes until evaluation is complete
- No deletion of existing ingestion scripts until replacement is verified
- No credentials in story or test output