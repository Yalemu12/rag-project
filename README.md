# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

**Off-campus housing experiences at UT Austin** — West Campus, Riverside, Hyde Park, and North Campus apartments, plus leasing timelines, pricing tradeoffs, and scams targeting students. This knowledge is valuable because apartment websites and leasing offices only show marketing material: they won't tell you which buildings have thin walls or broken elevators, whether Riverside's cheaper rent survives the cost of a car and a campus parking pass, or that leasing offices pressure students into signing in October when better deals appear in spring. The real answers live scattered across years of r/UTAustin threads, where students share firsthand experiences no official channel collects in one place.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

All 13 sources are r/UTAustin threads (post + top comments) retrieved 2026-06-11 via the pullpush.io Reddit archive, saved as plain text in `documents/` with a metadata header (title, source URL, post date, retrieval date, category) used for source attribution.

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | West Campus studio/1bd recommendations | Reddit thread | `documents/01_west-campus-studio-1bd-recs.txt` — https://www.reddit.com/r/UTAustin/comments/z9fu0r/ |
| 2 | Skyloft resident review | Reddit thread | `documents/02_skyloft-review.txt` — https://www.reddit.com/r/UTAustin/comments/sr5c3c/ |
| 3 | 26 West — what residents wish they'd known | Reddit thread | `documents/03_26-west-what-to-know.txt` — https://www.reddit.com/r/UTAustin/comments/1bgj6yl/ |
| 4 | Regents West on 26th — warning review | Reddit thread | `documents/04_regents-west-warning.txt` — https://www.reddit.com/r/UTAustin/comments/1iypq16/ |
| 5 | The Castilian for sophomores | Reddit thread | `documents/05_castilian-sophomores.txt` — https://www.reddit.com/r/UTAustin/comments/t7hbqg/ |
| 6 | Riverside w/ car vs West Campus w/o car cost comparison | Reddit thread | `documents/06_riverside-car-vs-west-campus.txt` — https://www.reddit.com/r/UTAustin/comments/qz1kan/ |
| 7 | West Campus / Hyde Park under $850/month | Reddit thread | `documents/07_west-campus-hyde-park-under-850.txt` — https://www.reddit.com/r/UTAustin/comments/kamglp/ |
| 8 | Freshman housing guidance (dorms vs apartments) | Reddit thread | `documents/08_freshman-housing-guidance.txt` — https://www.reddit.com/r/UTAustin/comments/180xpk0/ |
| 9 | Why students sign overpriced West Campus high-rises | Reddit thread | `documents/09_overpriced-high-rises-west-campus.txt` — https://www.reddit.com/r/UTAustin/comments/wam3jy/ |
| 10 | Leasing timeline: why signing too early costs money | Reddit thread | `documents/10_too-early-to-sign-lease.txt` — https://www.reddit.com/r/UTAustin/comments/kvcl8g/ |
| 11 | Is it necessary to sign a lease this early? | Reddit thread | `documents/11_sign-lease-early-necessary.txt` — https://www.reddit.com/r/UTAustin/comments/1fq7bbv/ |
| 12 | Gap between an old lease ending and a new one starting | Reddit thread | `documents/12_gap-between-leases.txt` — https://www.reddit.com/r/UTAustin/comments/14irges/ |
| 13 | West Campus parking-boot scam incident | Reddit thread | `documents/13_roommate-scammed-west-campus.txt` — https://www.reddit.com/r/UTAustin/comments/lx4uxh/ |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** Structure-aware — one chunk per comment (and one per post body), capped at 1,000 characters. Comments over the cap are split at sentence boundaries.

**Overlap:** 100 characters, applied *only* when a single long comment/body is split across chunks. There is deliberately no overlap between separate comments: each comment is an independent opinion from a different person, and blending them would pollute both embeddings.

**Why these choices fit your documents:** Reddit threads aren't continuous prose — each comment is a self-contained opinion delimited by `[score N]` markers, so those markers are the natural split points (a fixed window would glue the tail of one person's opinion to the head of another's). Every chunk is prefixed with its thread title and category (e.g. `[Is the Castilian good for sophomores | review]`) because the most informative comments never name the building they're about — "walls are thin as f***" only makes sense under the 26 West title. The 1,000-char cap exists because all-MiniLM-L6-v2 truncates input at 256 tokens (~1,000 chars); anything past it would be invisible to search. Preprocessing: Reddit-markdown artifacts are stripped (`\-` escapes, `[text](url)` links, collapsed whitespace), the metadata header is moved out of the chunk text into vector-store metadata, and comments under 50 cleaned characters ("Thank you!", emoji replies) are dropped — the threshold was lowered from a planned 80 after inspection showed 80 discarded eval-critical facts like "Castilian is 98% Freshman, don't live there if you're a sophomore" (65 chars).

**Final chunk count:** 222 chunks across 13 documents (237 comments parsed, 39 dropped by the length filter; min 104 / avg 336 / max 983 chars). Reproduce with `python ingest.py`.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`, with embeddings stored in a persistent ChromaDB collection configured for **cosine** distance (ChromaDB defaults to squared L2, which would make distance thresholds hard to interpret). Chosen because the chunks are short, conversational English — exactly what MiniLM is trained on — and it runs locally with no API key or rate limits; the full 222-chunk corpus embeds in ~3 seconds. Retrieval is top-k = 5 (`retrieve()` in `build_index.py`), enough to surface multiple independent opinions on comparison questions without diluting context. Tested against all 5 evaluation queries before any LLM was wired in: each returns its expected source document at rank 1 with top distances of 0.12–0.40.

**Production tradeoff reflection:** If this served real users and cost weren't a constraint, I'd weigh:

- **Accuracy on domain text:** `all-mpnet-base-v2` or an API model (OpenAI `text-embedding-3-small`, Cohere embed-v3) scores meaningfully higher on retrieval benchmarks. Student slang and building nicknames ("wampus", censored names like "skyl*ft") are where small models are most likely to miss — and Milestone 4 testing showed MiniLM is sensitive to query vocabulary (a query mentioning "rental scams" missed the parking-scam thread until the wording matched the corpus).
- **Context length:** API models accept 8K+ tokens, which would let long multi-paragraph comments stay whole instead of being split at the 256-token truncation limit.
- **Latency and hosting:** a local model has no per-query network hop and no per-token cost; an API model shifts ops burden off me. At ~250 chunks, latency is negligible either way; at 100K+ chunks index/query speed would start to matter.
- **Multilingual support:** irrelevant here — the corpus is entirely English Reddit posts — so I'd deliberately not pay for it.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

The system prompt in `query.py` frames grounding as hard constraints, not suggestions ("Hard rules — these are constraints, not suggestions"). The two load-bearing rules, verbatim:

> 1. Every claim in your answer must be traceable to a specific provided excerpt. You must not use any knowledge from outside the excerpts, even if you are confident it is true and even if the excerpts seem incomplete.
> 2. If the excerpts do not contain enough information to answer the question, reply with exactly: "I don't have enough information on that in the collected threads." — do not guess, do not answer from general knowledge, do not pad the refusal with generic advice.

Three structural choices back the instruction up: (a) the grounding rule and the exact refusal string are **repeated in the user message** after the context block, because instructions only stated once at the top of a long prompt get diluted; (b) each retrieved chunk is passed as a numbered excerpt with a provenance header (filename, thread title, post date, comment score) and the model must end each claim with the excerpt number(s) it came from — an uncited sentence is defined as a rule violation; (c) when the best retrieval distance is ≥ 0.40 (the weak-retrieval threshold measured in Milestone 4), the prompt injects a warning that the excerpts may not actually cover the question, nudging the model toward refusal instead of stretching marginal context. Generation runs at temperature 0.2. Tested with the out-of-domain probe "What's the best dining hall on campus?" — the system returns the exact refusal sentence and no sources.

**How source attribution is surfaced in the response:**

Attribution is guaranteed programmatically, not delegated to the LLM. `ask()` returns a `sources` list built from the retrieved chunks' ChromaDB metadata — deduplicated `filename — thread title (posted date) — source URL` entries — which the Gradio UI displays in its own "Retrieved from" panel. The model is *additionally* instructed to cite excerpt numbers inline (so individual claims are traceable to specific comments), but even if it ignored that instruction entirely, the true source list would still appear. The one LLM-dependent piece: when the model refuses, `ask()` detects the refusal sentence and returns an empty source list, so a refusal is never decorated with sources it didn't use.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1 — ingestion and chunking (Milestone 3)**

- *What I gave the AI:* The **Documents** and **Chunking Strategy** sections of `planning.md`, plus one real sample document (`04_regents-west-warning.txt`) so it could see the actual header / `--- COMMENTS ---` / `[score N]` format.
- *What it produced:* `ingest.py` with `parse_document()`, `chunk_document()`, and `load_chunks()` — per-comment chunks with the thread-title prefix, 1,000-char cap, and 100-char overlap on splits, exactly per spec.
- *What I changed or overrode:* The minimum-comment-length filter. The plan said ~80 characters, but inspecting the dropped-comment list showed 80 was discarding eval-critical facts ("Castilian is 98% Freshman, don't live there if you're a sophomore" — 65 chars), so it was lowered to 50, which still cuts pure phatic replies ("Thank you!").

**Instance 2 — embedding and retrieval (Milestone 4)**

- *What I gave the AI:* The **Retrieval Approach** section and the Mermaid architecture diagram from `planning.md`, plus the `load_chunks()` interface from Milestone 3.
- *What it produced:* `build_index.py` — embeds all 222 chunks with `all-MiniLM-L6-v2` into a persistent ChromaDB collection (explicitly configured for cosine distance rather than ChromaDB's default L2) with full source metadata, and a `retrieve(query, k=5)` function returning chunks with metadata and distances.
- *What I changed or overrode:* Retrieval testing before generation caught a bad evaluation question, not bad code: "What **rental** or parking scams…" retrieved generic West Campus apartment chunks because the corpus contains no rental-scam content. After verifying the index was healthy (focused phrasings returned the scam thread at distance ~0.27), the eval question was corrected to "What parking scams…", which its expected answer had described all along. Findings are documented in `planning.md` → "Milestone 4 findings".
