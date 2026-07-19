#!/usr/bin/env python3
"""
Murphy Book Synthesis - Stage 2 (v2)
One chunk per API call, resumes from progress file.
Robust JSON extraction with fallback repair.
"""
import json, re, time, sys, os
from pathlib import Path
from openai import OpenAI

EXTRACTED  = Path('/root/HermesForge/Inbox/murphy_extracted.json')
PROGRESS   = Path('/root/HermesForge/Inbox/murphy_synthesis_progress.json')
OUTPUT     = Path('/root/HermesForge/Inbox/murphy_synthesis.json')
KEY_FILE   = Path('/tmp/.orkey')
MODEL      = "anthropic/claude-sonnet-4.6"
MAX_TOKENS=8000  # enough for one chunk's worth of concepts
DELAY      = 1.0    # seconds between calls

if not KEY_FILE.exists():
    sys.exit("ERROR: /tmp/.orkey missing.")

API_KEY = KEY_FILE.read_text().strip()
print(f"API key loaded (prefix={API_KEY[:8]}...)")

SYSTEM_PROMPT = """You are a trading knowledge extraction specialist. Given a chunk of text from a technical analysis trading book, extract ALL trading knowledge into structured JSON.

Return ONLY valid JSON (no markdown, no commentary) with this exact structure:
{
  "chunk_id": <integer>,
  "chapter": "<chapter name>",
  "summary": "<2-3 sentence summary of this chunk>",
  "concepts": [
    {
      "title": "<concise concept name>",
      "concept_type": "<one of: concept|rule|entry-criteria|exit-criteria|risk-guideline|indicator|pattern|edge-condition>",
      "body": "<full explanation, 2-5 sentences>",
      "page_range": "<page reference if mentioned, else null>",
      "quotes": ["<exact quote if present>"]
    }
  ],
  "key_quotes": ["<exact memorable quotes from this chunk>"]
}

Extract EVERY trading rule, signal, pattern, and principle. Be thorough — do not skip minor rules.
If the chunk has no trading content (e.g., table of contents, index), return concepts: [] and key_quotes: [].
CRITICAL: Return ONLY the JSON object. No preamble, no explanation, no markdown fences."""

client = OpenAI(api_key=API_KEY, base_url="https://openrouter.ai/api/v1")

# Load extracted chunks
raw = EXTRACTED.read_text(errors="replace")
raw_clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", raw)
data = json.loads(raw_clean)
chunks = data["chunks"]
meta = data.get("metadata", {})
meta["title"]  = "Technical Analysis of the Financial Markets"
meta["author"] = "John J. Murphy"
print(f"Book: {meta['title']} — {meta['author']}")
print(f"Chunks: {len(chunks)}")

# Load progress
if PROGRESS.exists():
    prog = json.loads(PROGRESS.read_text())
    all_concepts = prog.get("concepts", [])
    all_quotes   = prog.get("key_quotes", [])
    done_ids     = set(prog.get("done_chunk_ids", []))
    summaries    = prog.get("summaries", [])
    print(f"Resuming: {len(done_ids)}/{len(chunks)} chunks done, {len(all_concepts)} concepts")
else:
    all_concepts, all_quotes, done_ids, summaries = [], [], set(), []

def save_progress():
    PROGRESS.write_text(json.dumps({
        "done_chunk_ids": sorted(list(done_ids)),
        "concepts": all_concepts,
        "key_quotes": all_quotes,
        "summaries": summaries,
    }, indent=2, ensure_ascii=False))

def extract_json(text):
    """Try multiple strategies to get valid JSON from response."""
    text = text.strip()
    
    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: strip markdown fences
    cleaned = re.sub(r"^```(?:json)?\s*", "", text)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # Strategy 3: find first { ... } block
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    # Strategy 4: truncated JSON — try to recover by finding last complete concept
    # Find all complete concept objects
    concept_matches = list(re.finditer(r'\{[^{}]*"title"[^{}]*"concept_type"[^{}]*"body"[^{}]*\}', text, re.DOTALL))
    if concept_matches:
        # Build partial result
        concepts = []
        for m in concept_matches:
            try:
                c = json.loads(m.group())
                concepts.append(c)
            except:
                pass
        if concepts:
            # Extract chunk_id and chapter from start of text
            cid_match = re.search(r'"chunk_id"\s*:\s*(\d+)', text)
            chap_match = re.search(r'"chapter"\s*:\s*"([^"]+)"', text)
            summ_match = re.search(r'"summary"\s*:\s*"([^"]+)"', text)
            return {
                "chunk_id": int(cid_match.group(1)) if cid_match else -1,
                "chapter": chap_match.group(1) if chap_match else "Unknown",
                "summary": summ_match.group(1) if summ_match else "",
                "concepts": concepts,
                "key_quotes": [],
                "_recovered": True
            }
    
    return None

def synthesise_chunk(chunk):
    user_msg = (
        f"Extract all trading knowledge from this chunk.\n"
        f"Book: {meta['title']} by {meta['author']}\n"
        f"Chunk ID: {chunk['chunk_id']}\n"
        f"Chapter: {chunk['chapter']}\n\n"
        f"=== CHUNK TEXT ===\n{chunk['text']}"
    )
    
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ],
        temperature=0.1,
        max_tokens=8000,
    )
    
    finish_reason = resp.choices[0].finish_reason
    raw_resp = (resp.choices[0].message.content or "").strip()
    
    if finish_reason == "length":
        print(f"  ⚠️  Response truncated (finish_reason=length) — attempting recovery")
    
    result = extract_json(raw_resp)
    if result is None:
        print(f"  ❌ JSON extraction failed | raw[:200]={raw_resp[:200]}")
        return None, 0
    
    recovered = result.get("_recovered", False)
    concepts = result.get("concepts", [])
    quotes = result.get("key_quotes", [])
    summary = result.get("summary", "")
    
    tag = " [RECOVERED]" if recovered else ""
    print(f"  ✅ {len(concepts)} concepts, {len(quotes)} quotes{tag}")
    return (summary, concepts, quotes), len(concepts)

# Main loop
todo = [c for c in chunks if c["chunk_id"] not in done_ids]
print(f"\nChunks to process: {len(todo)}")
print("=" * 60)

for i, chunk in enumerate(todo):
    cid = chunk["chunk_id"]
    chapter = chunk["chapter"]
    text_len = len(chunk["text"])
    
    print(f"\n[{i+1}/{len(todo)}] Chunk {cid} | {chapter[:50]} | {text_len} chars")
    
    start = time.time()
    try:
        result, n_concepts = synthesise_chunk(chunk)
    except Exception as e:
        print(f"  ❌ API error: {e}")
        time.sleep(5)
        continue
    
    elapsed = time.time() - start
    
    if result is not None:
        summary, concepts, quotes = result
        all_concepts.extend(concepts)
        all_quotes.extend(quotes)
        summaries.append({"chunk_id": cid, "chapter": chapter, "summary": summary})
        done_ids.add(cid)
        save_progress()
        print(f"  Saved. Total: {len(all_concepts)} concepts | {elapsed:.1f}s")
    else:
        print(f"  Skipping chunk {cid} due to parse failure")
    
    if i < len(todo) - 1:
        time.sleep(DELAY)

# Write final output
print(f"\n{'='*60}")
print(f"SYNTHESIS COMPLETE: {len(done_ids)}/{len(chunks)} chunks")
print(f"Total concepts: {len(all_concepts)}")
print(f"Total quotes: {len(all_quotes)}")

OUTPUT.write_text(json.dumps({
    "metadata": meta,
    "total_concepts": len(all_concepts),
    "total_quotes": len(all_quotes),
    "concepts": all_concepts,
    "key_quotes": all_quotes,
    "summaries": summaries,
}, indent=2, ensure_ascii=False))

print(f"Output written to {OUTPUT}")
