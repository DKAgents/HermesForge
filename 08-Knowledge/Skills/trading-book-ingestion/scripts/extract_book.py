#!/usr/bin/env python3
"""
Stage 1: Extract text from PDF or EPUB into chunked JSON.
Model tier: T3 (mechanical text extraction — no LLM used here)

Usage:
    python3 extract_book.py /path/to/book.pdf /path/to/output.json
    python3 extract_book.py /path/to/book.epub /path/to/output.json
"""

import sys
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def chunk_text(text: str, chapter: str, page_start: int, page_end: int,
               max_tokens: int = 3000) -> list[dict]:
    """Split a chapter's text into chunks of ~max_tokens (approx 4 chars/token)."""
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
            "text": c
        }
        for i, c in enumerate(chunks)
    ]


def extract_pdf(file_path: Path) -> tuple[dict, list[dict]]:
    """Extract text from a text-layer PDF using pymupdf4llm."""
    import pymupdf4llm
    import fitz

    doc = fitz.open(str(file_path))
    pdf_meta = doc.metadata

    metadata = {
        "title": pdf_meta.get("title") or file_path.stem,
        "author": pdf_meta.get("author") or "Unknown",
        "pages": doc.page_count,
        "source_file": str(file_path),
        "format": "pdf",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    # Check for text layer (warn if likely scanned)
    sample_text = "".join(
        doc[i].get_text() for i in range(min(3, doc.page_count))
    )
    if len(sample_text.strip()) < 100:
        print("WARNING: Very little text found on first 3 pages — this may be a scanned PDF.")
        print("Consider using marker-pdf for OCR. Proceeding anyway...")

    # Extract as markdown (preserves headers)
    md_text = pymupdf4llm.to_markdown(str(file_path))

    # Split by markdown headings into sections
    sections = re.split(r'\n(#{1,3} .+)\n', md_text)
    chunks = []
    chunk_id = 1
    current_chapter = "Front Matter"
    current_text = ""

    for part in sections:
        if re.match(r'^#{1,3} ', part):
            if current_text.strip():
                for c in chunk_text(current_text.strip(), current_chapter, 0, 0):
                    c["chunk_id"] = chunk_id
                    chunks.append(c)
                    chunk_id += 1
            current_chapter = part.strip('# \n')
            current_text = ""
        else:
            current_text += part

    # Flush last section
    if current_text.strip():
        for c in chunk_text(current_text.strip(), current_chapter, 0, 0):
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
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }

    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = False  # keep [image] placeholders
    h.body_width = 0  # no line wrapping

    chunks = []
    chunk_id = 1

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        content = h.handle(item.get_content().decode('utf-8', errors='replace'))
        if len(content.strip()) < 50:
            continue  # skip nav/toc items

        # Try to extract chapter title from first heading
        heading_match = re.search(r'^#{1,3} (.+)$', content, re.MULTILINE)
        chapter = heading_match.group(1).strip() if heading_match else item.get_name()

        for c in chunk_text(content.strip(), chapter, 0, 0):
            c["chunk_id"] = chunk_id
            chunks.append(c)
            chunk_id += 1

    return metadata, chunks


def main():
    if len(sys.argv) < 3:
        print("Usage: extract_book.py <input_file> <output_json>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)

    print(f"Extracting: {file_path.name} ({file_path.stat().st_size / 1024:.0f} KB)")

    ext = file_path.suffix.lower()
    if ext == '.pdf':
        metadata, chunks = extract_pdf(file_path)
    elif ext == '.epub':
        metadata, chunks = extract_epub(file_path)
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

    print(f"✅ Extracted {len(chunks)} chunks ({total_chars:,} chars, ~{total_chars//4:,} tokens)")
    print(f"   Title:  {metadata['title']}")
    print(f"   Author: {metadata['author']}")
    print(f"   Output: {output_path}")


if __name__ == "__main__":
    main()
