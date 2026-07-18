---
name: trading-book-ingestion
description: "Ingest trading books (PDF/EPUB) into structured Obsidian atomic notes under 08-Knowledge/Trading-Systems. Extracts rules, concepts, edge conditions, and key quotes using T3 for text extraction and T2 for reasoning-heavy synthesis."
version: 1.0.0
author: HermesForge Orchestrator
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [trading, knowledge, ingestion, pdf, epub, obsidian, atomic-notes, US-008]
    related_skills: [ocr-and-documents, obsidian]
---

# Trading Book & System Ingestion

Use this skill to ingest trading books (PDF or EPUB) into structured Obsidian knowledge notes.
Follows the US-008 design approved 2026-07-18.

## When to Use
- User provides a path to a PDF or EPUB trading book on the VPS
- Triggered manually: user says "ingest /path/to/book.pdf" or similar
- Do NOT auto-run without a confirmed file path — always verify the file exists first

---

## Pipeline Overview

```
## Stage 1: EXTRACT    [T3 — mechanical]   scripts/extract_book.py
##           Auto-detects text layer → pymupdf4llm (fast)
##           No text layer (scanned) → marker-pdf OCR (~2.5GB models, slow first run)
Stage 2: SYNTHESIZE [T2 — reasoning]    LLM chunk-by-chunk extraction
Stage 3: WRITE      [T3 — formatting]   scripts/write_notes.py
Stage 4: REPORT     [T3]               Discord summary + runlog entry
```

---

## Step-by-Step Instructions

### Step 0 — Confirm Prerequisites
```bash
python3 -c "import fitz, pymupdf4llm, ebooklib, html2text; print('pymupdf/epub OK')"
python3 -c "from marker.converters.pdf import PdfConverter; print('marker-pdf OK')"
```
If pymupdf missing: `pip install pymupdf pymupdf4llm ebooklib html2text`
If marker-pdf missing: `pip install marker-pdf`
Note: marker-pdf downloads ~2.5GB of models to `~/.cache/huggingface/` on **first run only**.

Confirm the file exists:
```bash
ls -lh /path/to/book.pdf
```

### Step 1 — Extract Text (T3 — mechanical)

Run `scripts/extract_book.py` with the file path. The script **auto-detects** whether the PDF has a text layer:
- **Text layer present** → fast `pymupdf4llm` path (seconds)
- **Scanned / image-only PDF** → `marker-pdf` OCR path (downloads ~2.5GB models on first run, then ~1-5 min/book)

```bash
python3 ~/.hermes/skills/research/trading-book-ingestion/scripts/extract_book.py \
  /root/HermesForge/Inbox/book.pdf \
  /root/HermesForge/Inbox/book_extracted.json
```

Force flags (if auto-detection is wrong):
```bash
# Force OCR even if text layer detected
python3 extract_book.py book.pdf out.json --force-ocr

# Force text layer even if thin
python3 extract_book.py book.pdf out.json --force-text
```
```json
{
  "metadata": {
    "title": "...", "author": "...", "pages": 123,
    "source_file": "/path/to/book.pdf", "format": "pdf",
    "extracted_at": "2026-07-18T12:00:00Z"
  },
  "chunks": [
    {
      "chunk_id": 1,
      "chapter": "Chapter 1 — ...",
      "page_start": 1, "page_end": 8,
      "text": "..."
    }
  ]
}
```

Review the output briefly — check chapter detection looks reasonable.

### Step 2 — Synthesize Concepts (T2 — reasoning)

For each chunk, call the T2 model (claude-sonnet-4.6) with the synthesis prompt.
Use `execute_code` to loop over chunks and accumulate results.

Per-chunk prompt template (in `scripts/synthesis_prompt.txt`):
- Extract: trading rules, key concepts, entry/exit conditions, risk guidelines,
  edge conditions, direct quotes
- Return structured JSON per chunk (schema in `references/synthesis-schema.json`)

**Important:** Use T2 here — this step determines note quality. Per RISK_RULES.md AI-002,
anything that feeds trading decisions must use T2 minimum.

Practical loop (pseudocode — use execute_code):
```python
for chunk in chunks:
    response = llm_call(model="anthropic/claude-sonnet-4.6",
                        system=synthesis_system_prompt,
                        user=chunk_prompt(chunk))
    results.append(parse_json(response))
```

Batch 3-5 chunks per call if they are short (< 1,500 tokens each) to reduce latency.
Do NOT batch more than 5 — synthesis quality degrades with too much context.

### Step 3 — Write Notes (T3 — formatting)

Run `scripts/write_notes.py` with the synthesis JSON:

```bash
python3 ~/.hermes/skills/research/trading-book-ingestion/scripts/write_notes.py \
  /root/HermesForge/Inbox/book_synthesis.json \
  /root/HermesForge/08-Knowledge/Trading-Systems/
```

This creates:
```
08-Knowledge/Trading-Systems/<BookSlug>/
├── metadata.json                    ← Dataview-queryable metadata
├── 00-Literature-Note.md            ← Summary, index, key quotes
├── rules/
│   ├── R001-<ConceptSlug>.md
│   └── ...
├── concepts/
│   ├── C001-<ConceptSlug>.md
│   └── ...
└── edge-conditions/
    ├── E001-<ConceptSlug>.md
    └── ...
```

### Step 4 — Report

Post a Discord summary:
- How many notes created (rules / concepts / edge-conditions)
- Top 3 concepts extracted
- Any quality flags (e.g. chunks where extraction was thin)
- Path to literature note in vault

Add a ForgeLoop runlog entry.
Commit vault changes to GitHub.

---

## Folder Structure (per book)

```
08-Knowledge/Trading-Systems/<BookSlug>/
├── metadata.json                    ← Title, author, file, ingestion date, model tiers
├── 00-Literature-Note.md            ← Summary + Key Quotes + index of all notes
├── rules/                           ← Explicit trading rules (concept_type: rule)
├── concepts/                        ← Key ideas and definitions (concept_type: concept)
├── edge-conditions/                 ← When system fails / limits (concept_type: edge-condition)
└── risk-guidelines/                 ← Risk management from the book (concept_type: risk-guideline)
```

## Atomic Note Frontmatter (required fields)
```yaml
---
type: atomic-note
concept_type: rule | concept | edge-condition | risk-guideline | entry-criteria | exit-criteria
source_book: "Title Here"
source_author: "Author Name"
source_file: "/root/HermesForge/Inbox/filename.pdf"
source_chapter: "Chapter N — Title"
source_page_range: "pp. X–Y"
model_tier: T2
model: anthropic/claude-sonnet-4.6
ingested_at: YYYY-MM-DD
tags: [trading-system, <book-slug>, atomic-note, <concept_type>]
---
```

## Literature Note Structure (00-Literature-Note.md)
```yaml
---
type: literature-note
source_book: "Title"
source_author: "Author"
source_file: "/path/to/file"
ingested_at: YYYY-MM-DD
model_extraction: T2 (anthropic/claude-sonnet-4.6)
model_preprocessing: T3 (google/gemini-2.0-flash-001)
tags: [literature-note, trading-system, <book-slug>]
---
```
Sections: Summary | Core Thesis | Key Quotes | All Notes Index

---

## Pitfalls

- **Scanned PDFs (no text layer):** `pymupdf` returns empty text — auto-detected and routed to `marker-pdf`. If auto-detection fails, use `--force-ocr`.
- **marker-pdf first run is slow:** Downloads ~2.5GB of models to `~/.cache/huggingface/` on first run. Subsequent runs use cached models (~30-60s/book). Do not interrupt the first run.
- **marker-pdf / Hermes openai version conflict:** marker-pdf requires `openai<2.0.0` but Hermes needs `openai==2.24.0`. After installing marker-pdf, always restore: `pip install "openai==2.24.0" "Pillow==12.2.0"`. marker-pdf still works with warnings.
- **Scanned PDFs (OCR quality):** marker-pdf handles most printed books well. Handwritten notes, low-resolution scans (<150 DPI), or heavy watermarks will degrade quality. Flag these in the report.
- **DRM-protected EPUBs:** ebooklib will open the file but chapters will be empty or encrypted.
  User must strip DRM first (Calibre + DeDRM plugin).
- **Chapter detection on PDFs:** pymupdf4llm detects headers by font size — works on most
  commercial ebooks but fails on plain-text PDFs. Fall back to page-range chunking (~15 pages).
- **T2 hallucination on paraphrases:** Always instruct T2 to label paraphrases with `[Paraphrase]`
  and direct quotes with the page number. Check a sample before writing all notes.
- **Duplicate concepts across chunks:** Step 3 deduplication uses title similarity — review the
  literature note index for obvious duplicates after first run.
- **Very long books (> 400 pages):** Process in two sessions (Part 1, Part 2) to avoid token limits.
  Each session appends to the same book folder.

---

## References
- `references/synthesis-schema.json` — JSON schema for T2 extraction output
- `references/book-slug-convention.md` — How to derive folder/slug names from book titles
- `scripts/extract_book.py` — Stage 1: PDF/EPUB → chunked JSON
- `scripts/write_notes.py` — Stage 3: synthesis JSON → Obsidian .md files
- `scripts/synthesis_prompt.txt` — T2 system prompt for concept extraction
