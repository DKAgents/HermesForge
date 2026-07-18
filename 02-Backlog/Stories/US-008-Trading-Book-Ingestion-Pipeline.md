---
id: US-008
type: user-story
epic: EPIC-001
status: backlog
priority: high
effort: L
created: 2026-07-18
updated: 2026-07-18
assigned_to: researcher
tags: [backlog, story, knowledge-ingestion, trading-books, obsidian, pdf, epub]
---

# US-008: Build Trading Book & System Ingestion Pipeline

## Story
**As a** HermesForge Researcher,  
**I want** a repeatable pipeline that ingests trading books and established trading systems into structured knowledge notes in Obsidian,  
**So that** the system can reason from proven trading frameworks, rules, and edge conditions rather than starting from scratch on every research task.

## Acceptance Criteria

### AC1 — PDF & EPUB Processing
- [ ] VPS has `pymupdf` (PDF) and `ebooklib` + `html2text` (EPUB) installed in Hermes venv
- [ ] A Hermes skill (`trading-book-ingestion`) exists that accepts a file path (PDF or EPUB) and extracts clean plaintext
- [ ] Extraction preserves chapter/section structure where detectable
- [ ] Images and charts are noted as `[Figure: description]` placeholders (not silently dropped)

### AC2 — Key Concept & Rule Extraction
- [ ] Extracted text is processed by a **T2 model** (claude-sonnet-4.6) to identify:
  - Core trading rules and criteria stated by the author
  - Entry/exit conditions and filters
  - Risk management guidelines specific to the system
  - Edge conditions and failure modes explicitly noted by the author
  - Key concepts and terminology with definitions
- [ ] T2 is used here (not T3) because extraction quality directly determines what the system learns — errors compound downstream (RISK_RULES.md AI-002 applies)

### AC3 — Atomic Notes in Obsidian
- [ ] Each extracted concept/rule produces one atomic note in `08-Knowledge/Trading-Systems/<BookSlug>/`
- [ ] Atomic note format:
  ```yaml
  ---
  type: atomic-note
  source: <book-title>
  source_id: US-008
  author: <author-name>
  chapter: <chapter or section>
  concept_type: [rule|concept|edge-condition|risk-guideline|entry-criteria|exit-criteria]
  model_tier: T2
  created: YYYY-MM-DD
  tags: [trading-system, <book-slug>, atomic-note]
  ---
  ```
- [ ] Each atomic note is self-contained: readable and useful without the source document
- [ ] Related atomic notes are wikilinked to each other where concepts connect

### AC4 — Literature Note (per book)
- [ ] One literature note created per ingested book at `08-Knowledge/Trading-Systems/<BookSlug>/00-Literature-Note.md`
- [ ] Literature note includes:
  - Book title, author, publication year
  - 3–5 sentence summary of the author's core thesis
  - List of all atomic notes generated from this book (wikilinked)
  - Orchestrator's overall quality/relevance assessment (1–2 sentences)
  - Model tier used for extraction
  - Source file path or reference on VPS

### AC5 — Model Tier Usage During Ingestion
- [ ] **T3 (gemini-2.0-flash-001):** Used for initial text chunking, section detection, and formatting cleanup — mechanical pre-processing
- [ ] **T2 (claude-sonnet-4.6):** Used for concept extraction, rule identification, and atomic note writing — reasoning-heavy steps
- [ ] **T1 (claude-opus-4-5):** Reserved for synthesis across multiple books (e.g. "what do these 5 systems have in common?") — only when explicitly requested
- [ ] Model tier is declared in each atomic note and literature note frontmatter

### AC6 — Source Reference Preservation
- [ ] Every atomic note includes `source:` (book title) and `chapter:` (section) in frontmatter
- [ ] Literature note includes the original file's location on VPS (`/path/to/file.pdf`)
- [ ] If a rule or concept is a direct quote, it is wrapped in blockquote syntax and attributed
- [ ] No paraphrasing without attribution — all extracted content traces back to source

### AC7 — Pipeline Documentation
- [ ] `trading-book-ingestion` skill is documented with:
  - Trigger conditions (when to use it)
  - Step-by-step process (extract → chunk → T3 pre-process → T2 extract → write notes)
  - Pitfalls (OCR-heavy PDFs, DRM-protected EPUBs, tables as text)
  - Example invocation
- [ ] At least one complete book ingested end-to-end as proof of concept before story is marked Done

## Suggested First Books to Ingest
*(prioritised by relevance to swing/position trading)*
1. **"Trading in the Zone"** — Mark Douglas (mindset + rules-based thinking)
2. **"How to Make Money in Stocks"** — William O'Neil (CANSLIM system, entry/exit rules)
3. **"Trend Following"** — Michael Covel (systematic trend trading)
4. **"The New Market Wizards"** — Jack Schwager (multiple systems, risk frameworks)
5. **"Options as a Strategic Investment"** — Lawrence McMillan (options-specific rules)

> User provides PDFs/EPUBs. The pipeline does not download copyrighted books.

## Notes / Context
> This is the first story in the "trading brain" track — building the knowledge base
> that all other agents (Researcher, Backtester, Risk Guardian) will reason from.
>
> The T2/T3 split in AC5 is deliberate: pre-processing is mechanical (T3 appropriate),
> but concept extraction is the core intelligence layer and must use T2 per AI-002.
>
> OCR-heavy scanned PDFs are a known pitfall — `pymupdf` handles text-layer PDFs well
> but degrades on scans. If a book is scan-only, `tesseract` OCR will be needed as an
> additional pre-processing step.
>
> DRM-protected EPUBs (most commercial ebooks) cannot be processed without the user
> stripping DRM first. Document this clearly in the skill.

## Dependencies
- **Blocks:** EPIC-002 Research stories (need knowledge base before research agents can query it)
- **Blocked by:** Nothing — can start immediately once `pymupdf` is installed

## Definition of Done
- [ ] `pymupdf` and `ebooklib` installed and tested on VPS
- [ ] `trading-book-ingestion` Hermes skill created and loadable
- [ ] At least 1 book fully ingested: literature note + minimum 10 atomic notes in vault
- [ ] All notes follow AC3/AC4 format with source references (AC6)
- [ ] Skill documented with pitfalls and example (AC7)
- [ ] Risk Guardian reviewed — no trading-decision content in atomic notes without T2 extraction
- [ ] Story committed to GitHub and BACKLOG_INDEX updated
