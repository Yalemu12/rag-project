# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->

**Off-campus housing experiences at UT Austin** — covering West Campus, Riverside, Hyde Park, and North Campus apartments, plus leasing timelines, pricing tradeoffs, and rental scams. This knowledge is valuable because apartment websites and leasing offices only show marketing material: they won't tell you which buildings have chronic maintenance problems, whether it's actually cheaper to live in Riverside with a car, or that signing a lease in October is usually a mistake. The real answers live scattered across years of r/UTAustin threads, where students share firsthand experiences that no official channel collects in one place.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

All sources are r/UTAustin threads (post + top comments), saved as plain-text files in `documents/` with a metadata header (title, source URL, post date, retrieval date, category) for source attribution. Retrieved 2026-06-11 via the pullpush.io Reddit archive.

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | r/UTAustin thread | West Campus studio/1bd recommendations — students compare buildings, prices, pros/cons | `documents/01_west-campus-studio-1bd-recs.txt` — https://www.reddit.com/r/UTAustin/comments/z9fu0r/ |
| 2 | r/UTAustin thread | Skyloft review — is it a good place to live, firsthand resident experiences | `documents/02_skyloft-review.txt` — https://www.reddit.com/r/UTAustin/comments/sr5c3c/ |
| 3 | r/UTAustin thread | 26 West — what residents wish they'd known before moving in | `documents/03_26-west-what-to-know.txt` — https://www.reddit.com/r/UTAustin/comments/1bgj6yl/ |
| 4 | r/UTAustin thread | Regents West on 26th — detailed negative review warning against signing a lease | `documents/04_regents-west-warning.txt` — https://www.reddit.com/r/UTAustin/comments/1iypq16/ |
| 5 | r/UTAustin thread | The Castilian — whether it's a good option for sophomores | `documents/05_castilian-sophomores.txt` — https://www.reddit.com/r/UTAustin/comments/t7hbqg/ |
| 6 | r/UTAustin thread | Cost comparison: Riverside with a car vs West Campus without one (bus options, parking fees) | `documents/06_riverside-car-vs-west-campus.txt` — https://www.reddit.com/r/UTAustin/comments/qz1kan/ |
| 7 | r/UTAustin thread | Finding housing in West Campus or Hyde Park under $850/month | `documents/07_west-campus-hyde-park-under-850.txt` — https://www.reddit.com/r/UTAustin/comments/kamglp/ |
| 8 | r/UTAustin thread | Broad housing guidance for incoming freshmen (dorms vs apartments, neighborhoods, timing) | `documents/08_freshman-housing-guidance.txt` — https://www.reddit.com/r/UTAustin/comments/180xpk0/ |
| 9 | r/UTAustin thread | Why students sign overpriced high-rise apartments in West Campus — pricing and tradeoff debate | `documents/09_overpriced-high-rises-west-campus.txt` — https://www.reddit.com/r/UTAustin/comments/wam3jy/ |
| 10 | r/UTAustin thread | Leasing timeline advice: why signing a lease too early costs you money | `documents/10_too-early-to-sign-lease.txt` — https://www.reddit.com/r/UTAustin/comments/kvcl8g/ |
| 11 | r/UTAustin thread | Is it necessary to sign a lease this early for next year? (recent take on lease timing) | `documents/11_sign-lease-early-necessary.txt` — https://www.reddit.com/r/UTAustin/comments/1fq7bbv/ |
| 12 | r/UTAustin thread | What to do during the gap between an old lease ending and a new one starting | `documents/12_gap-between-leases.txt` — https://www.reddit.com/r/UTAustin/comments/14irges/ |
| 13 | r/UTAustin thread | West Campus rental scam incident — how a student got scammed and warning signs | `documents/13_roommate-scammed-west-campus.txt` — https://www.reddit.com/r/UTAustin/comments/lx4uxh/ |

**Candidate questions this system should answer** (starting point for the Evaluation Plan):

1. What do students say about living at 26 West before moving in?
2. Is it cheaper to live in Riverside with a car or West Campus without one?
3. When should I sign a lease for the fall semester, and what happens if I sign too early?
4. What rental scams should I watch out for when looking for housing in West Campus?
5. Is the Castilian a good housing option for sophomores?

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1.

2.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
