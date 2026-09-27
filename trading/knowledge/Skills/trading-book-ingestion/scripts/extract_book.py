#!/usr/bin/env python3
"""
Stage 1: Extract text from PDF or EPUB into chunked JSON.
Model tier: T3 (mechanical text extraction — no LLM used here)

Extraction strategy:
  - PDF (text layer detected) → pymupdf4llm  (fast, no models)
  - PDF (scanned / image-based) → marker-pdf  (OCR, ML models, ~1st run downloads ~2.5GB)
  - EPUB                        → ebooklib + html2text

Usage:
    python3 extract_book.py /path/to/book.pdf /path/to/output.json
    python3 extract_book.py /path/to/book.epub /path/to/output.json
    python3 extract_book.py /path/to/book.pdf /path/to/output.json --force-ocr
    python3 extract_book.py /path/to/book.pdf /path/to/output.json --force-text
"""

import sys
import json
import re
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Minimum chars per page to consider the PDF text-layer viable
TEXT_LAYER_THRESHOLD = 100


def chunk_text(text: str, chapter: str, page_start: int, page_end: int,
               max_tokens: int = 3000) -> list[dict]:
    """Split a section's text into chunks of ~max_tokens (approx 4 chars/token)."""
    max_chars = max_tokens * 4
    chunks = []
    while len(text) > max_chars:
        split_at = text.rfind('\n\n', 0, max_chars)
        if split_at == -1:
            split_at = max_chars
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)

    return [
        {
            "chapter": chapter,
            "page_start": page_start,
            "page_end": page_end,
            "part": i + 1,
            "parts_total": len(chunks),
            "text": c,
        }
        for i, c in enumerate(chunks)
    ]


def has_text_layer(file_path: Path, sample_pages: int = 5) -> bool:
    """Return True if the PDF has a usable text layer."""
    import fitz
    doc = fitz.open(str(file_path))
    pages_to_check = min(sample_pages, doc.page_count)
    total_chars = sum(len(doc[i].get_text().strip()) for i in range(pages_to_check))
    doc.close()
    avg_chars = total_chars / pages_to_check
    return avg_chars >= TEXT_LAYER_THRESHOLD


def sections_from_markdown(md_text: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, body) tuples."""
    parts = re.split(r'\n(#{1,3} .+)\n', md_text)
    sections = []
    current_heading = "Front Matter"
    current_body = ""
    for part in parts:
        if re.match(r'^#{1,3} ', part):
            if current_body.strip():
                sections.append((current_heading, current_body.strip()))
            current_heading = part.strip('# \n')
            current_body = ""
        else:
            current_body += part
    if current_body.strip():
        sections.append((current_heading, current_body.strip()))
    return sections


def extract_pdf_text_layer(file_path: Path) -> tuple[dict, list[dict]]:
    """Fast path: text-based PDF via pymupdf4llm."""
    import fitz
    import pymupdf4llm

    doc = fitz.open(str(file_path))
    pdf_meta = doc.metadata
    metadata = {
        "title": pdf_meta.get("title") or file_path.stem,
        "author": pdf_meta.get("author") or "Unknown",
        "pages": doc.page_count,
        "source_file": str(file_path),
        "format": "pdf",
        "extraction_method": "pymupdf4llm (text layer)",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }
    doc.close()

    md_text = pymupdf4llm.to_markdown(str(file_path))
    sections = sections_from_markdown(md_text)

    chunks = []
    chunk_id = 1
    for heading, body in sections:
        for c in chunk_text(body, heading, 0, 0):
            c["chunk_id"] = chunk_id
            chunks.append(c)
            chunk_id += 1

    return metadata, chunks


def extract_pdf_ocr(file_path: Path) -> tuple[dict, list[dict]]:
    """OCR path: scanned PDF via marker-pdf. Downloads models on first run (~2.5GB)."""
    import fitz
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered

    print("  Loading marker-pdf models (first run downloads ~2.5GB to ~/.cache/huggingface/)...")
    print("  This may take 5-15 minutes on first run, ~30s on subsequent runs.")

    doc = fitz.open(str(file_path))
    page_count = doc.page_count
    pdf_meta = doc.metadata
    doc.close()

    metadata = {
        "title": pdf_meta.get("title") or file_path.stem,
        "author": pdf_meta.get("author") or "Unknown",
        "pages": page_count,
        "source_file": str(file_path),
        "format": "pdf",
        "extraction_method": "marker-pdf (OCR)",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    # Run marker OCR
    converter = PdfConverter(artifact_dict=create_model_dict())
    rendered = converter(str(file_path))
    md_text, _, _ = text_from_rendered(rendered)

    sections = sections_from_markdown(md_text)

    chunks = []
    chunk_id = 1
    for heading, body in sections:
        for c in chunk_text(body, heading, 0, 0):
            c["chunk_id"] = chunk_id
            chunks.append(c)
            chunk_id += 1

    return metadata, chunks


def extract_epub(file_path: Path) -> tuple[dict, list[dict]]:
    """Extract text from an EPUB using ebooklib + html2text."""
    from ebooklib import epub, ITEM_DOCUMENT
    import html2text

    book = epub.read_epub(str(file_path))

    metadata = {
        "title": (book.get_metadata('DC', 'title') or [[file_path.stem]])[0][0],
        "author": (book.get_metadata('DC', 'creator') or [["Unknown"]])[0][0],
        "pages": None,
        "source_file": str(file_path),
        "format": "epub",
        "extraction_method": "ebooklib + html2text",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = False
    h.body_width = 0

    chunks = []
    chunk_id = 1

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        content = h.handle(item.get_content().decode('utf-8', errors='replace'))
        if len(content.strip()) < 50:
            continue

        heading_match = re.search(r'^#{1,3} (.+)$', content, re.MULTILINE)
        chapter = heading_match.group(1).strip() if heading_match else item.get_name()

        for c in chunk_text(content.strip(), chapter, 0, 0):
            c["chunk_id"] = chunk_id
            chunks.append(c)
            chunk_id += 1

    return metadata, chunks


def main():
    parser = argparse.ArgumentParser(description="Extract trading book text to chunked JSON.")
    parser.add_argument("input_file", help="Path to PDF or EPUB file")
    parser.add_argument("output_json", help="Path to output JSON file")
    parser.add_argument("--force-ocr", action="store_true",
                        help="Force marker-pdf OCR even if text layer detected")
    parser.add_argument("--force-text", action="store_true",
                        help="Force pymupdf text extraction even if text layer looks thin")
    args = parser.parse_args()

    file_path = Path(args.input_file)
    output_path = Path(args.output_json)

    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    size_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"Extracting: {file_path.name} ({size_mb:.1f} MB)")

    ext = file_path.suffix.lower()

    if ext == '.epub':
        metadata, chunks = extract_epub(file_path)

    elif ext == '.pdf':
        if args.force_ocr:
            print("  Mode: marker-pdf OCR (forced)")
            metadata, chunks = extract_pdf_ocr(file_path)
        elif args.force_text:
            print("  Mode: pymupdf text layer (forced)")
            metadata, chunks = extract_pdf_text_layer(file_path)
        else:
            print("  Checking for text layer...")
            if has_text_layer(file_path):
                print("  Text layer detected → using pymupdf4llm (fast)")
                metadata, chunks = extract_pdf_text_layer(file_path)
            else:
                print("  No text layer detected → using marker-pdf OCR")
                metadata, chunks = extract_pdf_ocr(file_path)
    else:
        print(f"ERROR: Unsupported format '{ext}'. Use .pdf or .epub")
        sys.exit(1)

    total_chars = sum(len(c['text']) for c in chunks)
    metadata['total_chunks'] = len(chunks)
    metadata['total_chars'] = total_chars
    metadata['est_tokens'] = total_chars // 4

    output = {"metadata": metadata, "chunks": chunks}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))

    print(f"\n✅ Extracted {len(chunks)} chunks ({total_chars:,} chars, ~{total_chars//4:,} tokens)")
    print(f"   Title:            {metadata['title']}")
    print(f"   Author:           {metadata['author']}")
    print(f"   Extraction method: {metadata['extraction_method']}")
    print(f"   Output:           {output_path}")


if __name__ == "__main__":
    main()
