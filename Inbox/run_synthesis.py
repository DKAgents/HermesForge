#!/usr/bin/env python3
import json, re, time, sys
from pathlib import Path
from openai import OpenAI

EXTRACTED  = Path('/root/HermesForge/Inbox/murphy_extracted.json')
PROGRESS   = Path('/root/HermesForge/Inbox/murphy_synthesis_progress.json')
OUTPUT     = Path('/root/HermesForge/Inbox/murphy_synthesis.json')
KEY_FILE   = Path('/tmp/.orkey')
BATCH_SIZE = 3
MODEL      = "anthropic/claude-sonnet-4.6"

if not KEY_FILE.exists():
    sys.exit("ERROR: /tmp/.orkey missing. Run: python3 /tmp/getkey.py > /tmp/.orkey")

API_KEY = KEY_FILE.read_text().strip()
print(f"API key loaded (len={len(API_KEY)}, prefix={API_KEY[:8]}...)")

SYSTEM_PROMPT = Path(
    "/root/.hermes/skills/research/trading-book-ingestion/scripts/synthesis_prompt.txt"
).read_text()

client = OpenAI(api_key=API_KEY, base_url="https://openrouter.ai/api/v1")

# load extraction
raw = Path(EXTRACTED).read_text(errors="replace")
raw_clean = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", raw)
data = json.loads(raw_clean)
chunks = data["chunks"]
meta   = data["metadata"]
meta["title"]  = "Technical Analysis of the Financial Markets"
meta["author"] = "John J. Murphy"
print(f"Book: {meta['title']} — {meta['author']}")
print(f"Chunks: {len(chunks)}")

# load progress
if PROGRESS.exists():
    prog = json.loads(PROGRESS.read_text())
    all_concepts = prog["concepts"]
    all_quotes   = prog["key_quotes"]
    done_ids     = set(prog["done_chunk_ids"])
    summaries    = prog.get("summaries", [])
    print(f"Resuming: {len(done_ids)}/{len(chunks)} chunks already done")
else:
    all_concepts, all_quotes, done_ids, summaries = [], [], set(), []

def save_progress():
    PROGRESS.write_text(json.dumps({
        "done_chunk_ids": list(done_ids),
        "concepts": all_concepts,
        "key_quotes": all_quotes,
        "summaries": summaries,
    }, indent=2, ensure_ascii=False))

def synthesise_batch(batch_chunks):
    user_msg = ""
    for c in batch_chunks:
        user_msg += f"\n\n=== CHUNK {c['chunk_id']} | {c['chapter']} ===\n{c['text']}"
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content":
                f"Extract all trading knowledge from {len(batch_chunks)} chunk(s) from "
                f"\'{meta['title']}\" by {meta['author']}.\n"
                "Return a JSON ARRAY — one object per chunk. No markdown, just JSON.\n"
                + user_msg}
        ],
        temperature=0.1,
        max_tokens=4096,
    )
    raw_resp = (resp.choices[0].message.content or "").strip()
    raw_resp = re.sub(r"^```(?:json)?\s*", "", raw_resp)
    raw_resp = re.sub(r"\s*```$", "", raw_resp)
    try:
        result = json.loads(raw_resp)
        return result if isinstance(result, list) else [result]
    except json.JSONDecodeError as e:
        print(f"  WARNING JSON parse: {e} | raw[:300]={raw_resp[:300]}")
        return []

remaining = [c for c in chunks if c["chunk_id"] not in done_ids]
batches   = [remaining[i:i+BATCH_SIZE] for i in range(0, len(remaining), BATCH_SIZE)]
print(f"Batches remaining: {len(batches)} (model={MODEL})\n")

for bi, batch in enumerate(batches, 1):
    ids = [c["chunk_id"] for c in batch]
    print(f"Batch {bi}/{len(batches)} chunks={ids} ...", end=" ", flush=True)
    t0 = time.time()
    results = synthesise_batch(batch)
    n = 0
    for res in results:
        if not isinstance(res, dict): continue
        cid = res.get("chunk_id")
        ch  = res.get("chapter", "")
        for concept in res.get("concepts", []):
            concept["chapter"] = ch
            concept.setdefault("source_book",   meta["title"])
            concept.setdefault("source_author", meta["author"])
            all_concepts.append(concept); n += 1
        for q in res.get("key_quotes", []):
            q["chapter"] = ch; all_quotes.append(q)
        if res.get("summary"):
            summaries.append({"chunk_id": cid, "chapter": ch, "summary": res["summary"]})
        if cid: done_ids.add(cid)
    print(f"{n} concepts ({len(all_concepts)} total) [{time.time()-t0:.1f}s]")
    save_progress()
    time.sleep(0.5)

print(f"\nGenerating book-level summary (T2)...")
chunk_summaries = "\n".join(
    f"- Chunk {s['chunk_id']} ({s['chapter']}): {s['summary']}"
    for s in summaries[:40]
)
sr = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content":
            "Given chunk summaries from a trading book, write a 4-5 sentence summary and "
            "2-3 sentence core thesis. Return JSON only: {\"summary\": \"...\", \"core_thesis\": \"...\"}"},
        {"role": "user", "content":
            f"Book: \'{meta['title']}\" by {meta['author']}\n\n{chunk_summaries}"}
    ],
    temperature=0.2, max_tokens=600,
)
raw_s = (sr.choices[0].message.content or "").strip()
raw_s = re.sub(r"^```(?:json)?\s*", "", raw_s)
raw_s = re.sub(r"\s*```$", "", raw_s)
try:    book_syn = json.loads(raw_s)
except: book_syn = {"summary": raw_s, "core_thesis": ""}

final = {
    "metadata": meta,
    "synthesis": {"summary": book_syn.get("summary",""), "core_thesis": book_syn.get("core_thesis",""), "key_quotes": all_quotes[:20]},
    "concepts": all_concepts,
}
OUTPUT.write_text(json.dumps(final, indent=2, ensure_ascii=False))
print(f"\n✅ Stage 2 complete — {len(all_concepts)} concepts, {len(all_quotes)} quotes")
print(f"   Output: {OUTPUT}")
