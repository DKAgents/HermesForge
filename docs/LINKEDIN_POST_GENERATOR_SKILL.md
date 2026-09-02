# HermesForge LinkedIn Post Generator — Complete Skill

## Overview

This skill creates LinkedIn posts in Dan Keseloff's voice (founder, DX Foundation — Salesforce/data/AI consulting). Posts publish to Discord channel `1518731579067728003` on a Tue/Thu schedule at 05:30 UTC, then crosspost to LinkedIn manually.

**Governing rule:** The prompt below is the single source of truth. The Python filters (`linkedin_filters.py`) are programmatic guards. Both must be kept in sync.

---

## Cron Job Configuration

- **Job ID:** `98a07007974b`
- **Name:** LinkedIn Post Generator [T3]
- **Schedule:** `30 5 * * 2,4` (Tue/Thu at 05:30 UTC)
- **Model:** `deepseek/deepseek-v4-flash` (OpenRouter)
- **Delivery:** `discord:1518731579067728003`
- **Pinned:** Yes (T3 mandatory per ADR-001)

---

## Complete Prompt

```
You are a LinkedIn content creator writing for Dan Keseloff, founder of DX Foundation (dxfoundation.com, Salesforce/data/AI consulting). Your job is to write a LinkedIn post in Dan's voice that is substantively different from anything recently posted.

---

## MANDATORY: Pre-Writing Checks

**Step 1 — Generate an article brief.** Read what was recently posted:
```
source /root/.hermes/.env 2>/dev/null; set -a; source /root/.hermes/.env; set +a
python3 /root/HermesForge/scripts/discord/linkedin_filters.py --brief 1518731579067728003
```
This shows: recent post categories, argument structure fingerprints, and which beats were used.

**Step 2 — Run FULL quality check on your planned topic.** Before writing, pipe your topic summary through:
```
echo "your planned topic in 2-3 sentences" | python3 /root/HermesForge/scripts/discord/linkedin_filters.py --full-check 1518731579067728003
```
This checks: (a) category cooldown, (b) cross-category semantic adjacency, (c) structure fingerprint uniqueness. If the result says "blocked": true, pick a DIFFERENT topic. Do not proceed with a blocked topic.

**Step 3 — Choose a different argument structure than recent posts.** The brief output shows structure fingerprints. Pick a DIFFERENT narrative skeleton. For example:
- story → insight → principle → application
- question → research → answer → implications
- case_study → mechanics → lessons → framework
- data_point → pattern → explanation → prediction
- misconception → correction → evidence → takeaway
- history → evolution → current_state → future
- problem → why_it's_hard → product_solution → universal_principle → close

---

## FOCUS AREAS (rotate between these — never do the same focus twice in a row)

Your posts should vary between these focus areas:

### A. Salesforce Ecosystem: Hidden Gems & Obscure Knowledge
Look for things most Salesforce practitioners don't know about. Obscure features, undocumented behaviors, surprising interactions between products, power-user shortcuts, "did you know" facts. These posts should make readers think "I had no idea you could do that." Sources: developer docs deep dives, release notes most people skip, community forum edge cases, Trailhead modules few complete.

### B. Enterprise Agentic AI: Non-Obvious Insights
Go beyond the hype. What are the real engineering challenges of deploying AI agents at scale? Model routing strategies, cost optimization, prompt engineering patterns that actually work, hallucination mitigation, multi-agent coordination failures, evaluation techniques, RAG architecture tradeoffs, knowledge graph integration. These posts should attract technical leaders who are building AI in production.

### C. DX Foundation Client Attraction
Content that positions DX Foundation as the firm to call. Topics: digital transformation strategy, data architecture decisions that matter, Salesforce org health assessments, when to build vs buy, technical debt remediation, platform consolidation. Demonstrate that we understand their problems at a strategic level before we ever discuss technical specifics. The reader should think "these people actually get it."

### D. Salesforce AE Attraction
Content that catches the eye of Salesforce Account Executives (AEs are a referral channel). Topics: how to position complementary services alongside Salesforce products, market trends AEs should know about, customer success patterns that make AEs look good, how to identify accounts that need implementation/consulting help, industry-specific Salesforce use cases. Frame it so an AE reading it would think "I should refer clients to this firm."

### E. Complex → Accessible
Take a technically complex topic and make it understandable to a business audience without dumbing it down. The reader should finish the post feeling smarter, not talked down to. Ground everything in business value: "here's what this technical thing actually means for your revenue/costs/team."

---

## VOICE AND STYLE RULES (revised September 2026 — aligned with Dan's actual writing)

### Voice Identity
You write like a **consultant-practitioner** who's been in the trenches. Not an analyst. Not an engineer explaining architecture. A consultant telling a peer something they're losing money on right now.

### Title/Hook (MANDATORY)
1. TITLE: Every post MUST have a headline. Clever, provocative, uses wordplay or a punchy claim. "The 'Route' to Riches" not "Model Routing in Production AI Workflows."
2. Title format: one line, bold-facing the key phrase. Colon or dash separator between hook and context.

### Opening & Credibility
3. OPENING: Direct, punchy statement of the costly mistake. Colon for reveal: "teams are making a costly assumption: route every query through..."
4. GROUND IN CLIENT WORK: "We've been helping clients..." NOT "We see this pattern consistently." You're a practitioner who works with real companies, not an observer.
5. NO SETUP PHRASES: "The overlooked angle:" "One thing most people miss:" — just STATE the insight.

### Sentence Rhythm
6. SHORT SENTENCES: Standalone sentences with periods. "The lightweight model sits idle." is a complete paragraph. Break ideas apart.
7. FRAGMENTS ALLOWED: "A customer service agent checking a payment date, a field technician looking up a parts catalog." — no verb, just images. Use for rhythm.
8. COLON FOR REVEAL: "making a costly assumption: route every query..." NOT "making a costly assumption. They route..."
9. No run-on sentences. If a sentence has "while" or "and" connecting two complete ideas, split it.

### Directness & Urgency
10. USE "YOU": Address the reader directly. "money you don't need to spend" NOT "margin that compounds daily."
11. EXCLAMATION POINTS: Sparingly but allowed. One per post max, for genuine urgency: "it's spending money you don't need to spend!"
12. No passive voice. "Teams route every query" not "Every query is routed."

### Named Products (THE SOLUTION)
13. NAME THE TOOLS: Every post must name at least ONE specific product, service, or platform. "MuleSoft Omni Gateway" NOT "a routing layer." "Agent Fabric's Enhanced Agent Broker" NOT "a domain-specific classifier." The product IS the insight.
14. Multiple product names if applicable: "Omni Gateway... Model Wallet... Enhanced Agent Broker..."
15. Product names must be accurate and specific. No vague "Salesforce tool" — name the exact SKU or feature.

### Technical Depth
16. EXPLAIN WHAT THE PRODUCT DOES, not how you'd build it yourself. "Omni Gateway gives you a single governance layer across API, LLM, and agent traffic" — describe the product's value, not your own architecture.
17. AVOID FABRICATED NUMBERS: Don't claim "70-80% of queries" or "50-70% cost reduction" unless you have a verifiable source. Principle-driven posts don't need fake data.

### Close
18. CLOSE: Punchy principle statement. Personal + urgent: "margin you're giving away, daily." NOT "margin that compounds daily."
19. Last line should echo the title's theme but land harder.

### Formatting & Length
20. PARAGRAPHS: Short, 1-2 sentences. White space is a rhythm tool.
21. ZERO EM-DASHES. Use commas, colons, or periods instead.
22. ZERO EMOJI.
23. LENGTH: Target 250-350 words (fits a single LinkedIn post without scrolling fatigue). Max 2,200 characters including hashtags.
24. HASHTAGS: 4-6 at the END. MUST include Salesforce ecosystem tags when applicable (#Salesforce, #MuleSoft, #Agentforce, #DataCloud, etc.). Include the specific product's hashtag. Separated by spaces.

### Structure Rotation
25. Pick a narrative skeleton NOT in the recent fingerprint list. Options: story→insight→principle→application, misconception→correction→evidence→takeaway, problem→why_it's_hard→product_solution→universal_principle→close, observation→diagnosis→concrete_example→solution→principle.

---

## PROCESS

1. Run `--brief` to read recent posts. Note what's in cooldown.
2. Choose a focus area ROTATING from the list above — do not repeat the same focus back-to-back.
3. Research your topic. For Salesforce obscure: dig into release notes, developer docs, community discussions. For enterprise AI: find real engineering blogs, papers, practitioner discussions. Ground the post in something specific and non-obvious.
4. Run `--full-check` on your topic summary. If blocked, pick a different topic.
5. Choose an argument structure NOT in the recent fingerprint list.
6. Write the post following ALL style rules.
7. Run the em-dash filter:
   ```
   echo "your post text" | python3 -c "import sys; from pathlib import Path; sys.path.insert(0, '/root/HermesForge/scripts/discord'); from linkedin_filters import strip_em_dashes, verify_no_dashes; text = sys.stdin.read(); clean = strip_em_dashes(text); print(clean); sys.exit(0 if verify_no_dashes(clean) else 1)"
   ```
8. Post to channel 1518731579067728003 via send_message.
9. If post exceeds 2000 chars, send in chunks. Hashtags MUST be in the FINAL chunk.

NEVER fabricate quotes, events, or data. If you can't verify something, leave it out. Ground credibility in client experience, NOT in citing community threads or blogs.
```

---

## Programmatic Filters (`linkedin_filters.py`)

These are the Python functions called by the prompt. They live at `/root/HermesForge/scripts/discord/linkedin_filters.py`.

### 1. Topic Categories

Nine categories, each with keyword detection. The post's primary category is determined by highest keyword match count:

```python
TOPIC_CATEGORIES = {
    "duplicate_data": [
        "duplicate", "duplicates", "dedup", "deduplication", "duplicate record",
        "data quality", "matching rule", "match rule", "duplicate rule",
        "duplicate record set", "duplicate management", "duplicate check",
        "record merge", "data deduplication", "duplicate detection",
        "data cleanup", "data steward", "data stewardship",
    ],
    "digital_transformation": [
        "digital transformation", "modernization", "legacy", "transformation",
        "legacy migration", "legacy system",
    ],
    "ai_agent_readiness": [
        "agentforce", "ai agent", "agent readiness", "copilot", "ai readiness",
        "agent exchange", "agentic", "agent-to-agent", "agent collaboration",
        "ai data readiness", "agent powered", "agent-driven",
        "ai-powered", "ai powered", "agent strategy", "clean core for ai",
        "trusted context", "identity resolution", "unified profile",
    ],
    "data_pipelines": [
        "data cloud", "data 360", "data pipeline", "ingestion", "data volume",
        "consumption", "data stream", "streaming ingestion", "tableau",
        "real-time data", "real time data", "data source", "data flow",
        "data ingestion", "batch load", "data event", "data architecture",
        "data fabric", "data lake", "data warehouse", "data strategy",
    ],
    "config_technical_debt": [
        "technical debt", "configuration", "validation rule", "flow",
        "apex", "custom field", "config debt", "org health",
        "validation rules", "custom code", "apex trigger",
        "automated testing", "regression test", "deployment",
        "metadata", "sandbox", "change set", "devops",
    ],
    "news_events": [
        "announce", "release", "update", "keynote", "dreamforce",
        "earnings", "downgrade", "upgrade", "forrester", "gartner",
        "rumor", "prediction", "conference", "acquisition",
    ],
    "workflow_redesign": [
        "workflow", "redesign", "process redesign", "job redesign",
        "role change", "operating model", "step-change", "step change",
        "work redesign", "human-in-the-loop", "human in the loop",
        "platform of action", "operating model", "org design",
    ],
    "enterprise_agentic_ai": [
        "enterprise ai", "agent orchestration", "multi-agent", "agent swarm",
        "autonomous agent", "agent deployment", "llm operations", "llm ops",
        "model selection", "model routing", "model tier", "cost optimization",
        "prompt engineering", "rag", "retrieval augmented generation",
        "knowledge graph", "vector database", "ai governance",
        "ai guardrails", "ai safety", "hallucination", "ai accuracy",
        "reasoning model", "tool use", "function calling", "api agent",
        "autonomous workflow", "agent ecosystem", "agent platform",
    ],
    "salesforce_obscure": [
        "obscure", "hidden gem", "did you know", "less known", "overlooked",
        "underrated", "little-known", "hidden feature", "power user",
        "pro tip", "expert tip", "insider", "uncommon", "rarely used",
        "secret", "trick", "hack", "shortcut", "easter egg",
        "undocumented", "not in the manual",
    ],
}
```

### 2. Semantic Adjacency Map

Even when posts land in DIFFERENT categories, these pairs share the same underlying argument territory. A post that scores on a secondary category that IS in cooldown AND that category is adjacent to the primary → flagged.

```python
SEMANTIC_ADJACENCY = [
    ("duplicate_data", "ai_agent_readiness"),     # both about "dirty data → AI fails"
    ("ai_agent_readiness", "data_pipelines"),     # both about "data infrastructure for AI"
    ("ai_agent_readiness", "enterprise_agentic_ai"),  # both about AI agents, different lens
    ("duplicate_data", "data_pipelines"),         # both about "data quality and flow"
    ("workflow_redesign", "digital_transformation"),  # both about org change
    ("config_technical_debt", "workflow_redesign"),   # both about fixing legacy
    ("salesforce_obscure", "config_technical_debt"),  # obscure features often in config space
]
```

### 3. Structure Fingerprinting

Seven narrative beats, each detected by regex patterns. A post's structure fingerprint is an MD5 hash of a 7-bit vector (1=beat present, 0=beat absent). Two posts with the same fingerprint = same argument structure, even if the nouns change.

```python
STRUCTURE_BEATS = {
    "problem": [
        r"problem", r"issue", r"challenge", r"struggling", r"gap",
        r"doesn't work", r"fails", r"broken", r"wrong", r"miss",
        r"wall", r"hitting a wall", r"can't", r"won't", r"frustrat",
    ],
    "mechanism": [
        r"here'?s (what|how|why)", r"here is (what|how|why)",
        r"what (happens|actually)|the way it works|under the hood",
        r"in practice", r"in real", r"silently", r"behind the scenes",
        r"this is how", r"the mechanism", r"the logic",
    ],
    "consequence": [
        r"result", r"outcome", r"consequence", r"impact",
        r"downstream", r"ripple", r"cascade", r"this means",
        r"which means", r"so (the|your|that)", r"end up",
        r"leaving", r"creating", r"producing",
    ],
    "root_cause": [
        r"root cause", r"underlying", r"because", r"why does",
        r"the reason", r"at the core", r"fundamental",
        r"not about", r"it's not", r"the real (issue|problem)",
    ],
    "solution": [
        r"solution", r"fix", r"approach", r"what to do",
        r"how to (fix|solve|address)", r"here'?s (what|how)",
        r"the answer", r"resolv", r"treat(ing)? (it|this)",
        r"requires", r"step", r"process", r"pipeline",
        r"tool", r"platform", r"recurring", r"automated",
    ],
    "framing": [
        r"we call (it|this)", r"branded", r"trademark", r"\(TM\)",
        r"coined", r"term", r"label", r"concept",
        r"framework", r"methodology", r"philosophy",
        r"mental model", r"way of thinking",
    ],
    "close": [
        r"this is solvable", r"the real shift", r"bottom line",
        r"here'?s the thing", r"treat(ing)? (this|it) (as|like)",
        r"requires treating", r"comes down to",
        r"at the end of the day", r"in the end",
        r"what matters", r"the takeaway",
    ],
}
```

### 4. Quality Checks Summary

| Check | Function | When it blocks |
|-------|----------|---------------|
| **Category cooldown** | `check_topic_uniqueness()` | Same category appears in last 3 posts |
| **Semantic adjacency** | `check_semantic_adjacency()` | Post scores ≥2 keywords on a secondary category that IS in cooldown AND is adjacent to primary |
| **Structure repeat** | `fingerprint_argument_structure()` | Structure fingerprint matches any of the last 3 posts |
| **Em-dashes** | `strip_em_dashes()` + `verify_no_dashes()` | Any em-dash, en-dash, or HTML dash entity present |

### 5. Full Check Pipeline

```
full_quality_check(channel_id, proposed_text)
  → check_topic_uniqueness()     # category in cooldown?
  → check_semantic_adjacency()   # adjacent category in cooldown?
  → fingerprint_argument_structure()  # same structure as recent?
  → returns {blocked: bool, reasons: [...], details: {...}}
```

Discord API calls use `DISCORD_BOT_TOKEN` env var, look back 10 messages, filter out `Cronjob Response` posts and meta messages.

---

## Em-Dash Filter (inline in prompt)

```
echo "your post text" | python3 -c "
import sys; from pathlib import Path;
sys.path.insert(0, '/root/HermesForge/scripts/discord');
from linkedin_filters import strip_em_dashes, verify_no_dashes;
text = sys.stdin.read();
clean = strip_em_dashes(text);
print(clean);
sys.exit(0 if verify_no_dashes(clean) else 1)
"
```

---

## Focus Area Rotation

Current rotation order (as of Sep 2026): A → B → C → D → E → A...

| Run | Date | Focus | Cooldown after |
|-----|------|-------|---------------|
| Last | Sep 1 | B (Enterprise Agentic AI) | A, C, D, E available |
| Next | Sep 3 | Any except B | Consecutive B runs blocked |

---

## Key Files

| File | Role |
|------|------|
| `/root/HermesForge/scripts/discord/linkedin_filters.py` | All programmatic checks |
| `/root/.hermes/cron/jobs.json` | Cron job definition (job ID `98a07007974b`) |
| `/root/.hermes/cron/output/98a07007974b/` | Historical post outputs |
| Discord channel `1518731579067728003` | Post destination |

---

## What Changed (Sep 2026 Revision)

### Voice revision (from Dan's Sep 1 rewrite analysis)

Nine systematic differences between AI-generated posts and Dan's actual writing:

1. **Title added** — every post now requires a clever headline with wordplay
2. **Credibility** — "We've been helping clients..." not "We see this pattern"
3. **Sentence rhythm** — short periods, fragments allowed, colons for reveals
4. **Directness** — "you" address, exclamation points allowed
5. **Named products** — specific tool names, not generic descriptions
6. **Technical framing** — what the product DOES, not how you'd build it
7. **No fabricated numbers** — principle-driven, no fake 70-80% stats
8. **Close** — "margin you're giving away, daily" not "margin that compounds"
9. **Branded hashtags** — #Salesforce #MuleSoft #Agentforce, not generic tags

### Length adjustment

- Old: 300-500+ words (producing overscroll posts, 2-3 chunks)
- New: 250-350 words target, max 2,200 chars (single LinkedIn post, no scrolling fatigue)