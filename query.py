"""Milestone 5 — Grounded generation.

Wires retrieval (build_index.retrieve) to Groq's llama-3.3-70b-versatile and
enforces grounding two ways:

1. Prompt-level: the system prompt *forbids* using training knowledge, gives
   the model an exact refusal sentence to emit when the context is
   insufficient, and the grounding rule is repeated in the user message so it
   survives long context.
2. Structural: source attribution is built programmatically from the
   retrieved chunks' ChromaDB metadata, never left to the LLM. Even if the
   model forgot to cite inline, ask() still returns the true source list.
   Per the Milestone 4 finding in planning.md, when the best cosine distance
   is >= WEAK_RETRIEVAL_DISTANCE the prompt warns the model that the
   documents may not actually cover the question.

  ask(question) -> {"answer": str, "sources": [str, ...], "results": [...]}

Usage:
  python query.py "What do students say about living at 26 West?"
  python query.py --test     # 5 eval questions + 1 out-of-domain probe
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from groq import Groq

from build_index import EVAL_QUERIES, retrieve

load_dotenv()

GROQ_MODEL = "llama-3.3-70b-versatile"
REFUSAL = "I don't have enough information on that in the collected threads."
# planning.md, Milestone 4 findings: best distance >= ~0.4 with scattered
# sources means retrieval is weak — tell the model so it can decline.
WEAK_RETRIEVAL_DISTANCE = 0.40

SYSTEM_PROMPT = f"""\
You answer questions about off-campus housing at UT Austin using ONLY the \
Reddit thread excerpts provided in the user message. These are firsthand \
student opinions, not official information.

Hard rules — these are constraints, not suggestions:
1. Every claim in your answer must be traceable to a specific provided \
excerpt. You must not use any knowledge from outside the excerpts, even if \
you are confident it is true and even if the excerpts seem incomplete.
2. If the excerpts do not contain enough information to answer the question, \
reply with exactly: "{REFUSAL}" — do not guess, do not answer from general \
knowledge, do not pad the refusal with generic advice.
3. Cite as you go: each claim ends with the bracketed excerpt number(s) it \
came from, e.g. [1] or [2][4]. A sentence without a citation is a violation \
of rule 1.
4. Excerpts are individual Reddit comments — they may disagree. Present \
disagreements as such ("one student says X [2], another disagrees [5]") \
instead of merging them into a fake consensus. Comment scores indicate \
community agreement.
5. Threads span 2021–2024. When an excerpt states a price or a condition \
that can change over time, mention the post date from that excerpt's header.
6. Answer the question that was asked, concisely. No preamble, no \
"based on the provided context" boilerplate.\
"""

USER_TEMPLATE = """\
Excerpts retrieved from the r/UTAustin housing corpus:

{context}
{retrieval_warning}
Question: {question}

Answer using only the excerpts above, citing excerpt numbers. If they don't \
contain the answer, reply exactly: "{refusal}"\
"""

_client: Groq | None = None


def get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set — copy .env.example to .env and add your key."
            )
        _client = Groq(api_key=api_key)
    return _client


# ---------------------------------------------------------------- prompt building

def format_context(results: list[dict]) -> str:
    """Number each retrieved chunk and attach its provenance header."""
    blocks = []
    for i, r in enumerate(results, start=1):
        m = r["metadata"]
        blocks.append(
            f"[{i}] {m['filename']} | thread: {m['title']} | "
            f"posted {m['posted']} | comment score {m['score']}\n"
            f"{r['text']}"
        )
    return "\n\n".join(blocks)


def format_sources(results: list[dict]) -> list[str]:
    """Deduplicated source list built from metadata — never from the LLM."""
    sources: list[str] = []
    seen = set()
    for r in results:
        m = r["metadata"]
        if m["filename"] in seen:
            continue
        seen.add(m["filename"])
        sources.append(f"{m['filename']} — {m['title']} (posted {m['posted']}) — {m['source']}")
    return sources


# ---------------------------------------------------------------- end-to-end

def ask(question: str, k: int = 5) -> dict:
    """Retrieve top-k chunks, generate a grounded answer, attach true sources."""
    results = retrieve(question, k=k)

    best = min(r["distance"] for r in results)
    warning = ""
    if best >= WEAK_RETRIEVAL_DISTANCE:
        warning = (
            "\nNote: retrieval similarity is weak for this question — the "
            "excerpts above may not actually cover it. Only answer if they "
            "clearly do.\n"
        )

    response = get_client().chat.completions.create(
        model=GROQ_MODEL,
        temperature=0.2,  # low: grounded summarization, not creative writing
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_TEMPLATE.format(
                    context=format_context(results),
                    retrieval_warning=warning,
                    question=question,
                    refusal=REFUSAL,
                ),
            },
        ],
    )
    answer = (response.choices[0].message.content or "").strip()

    # If the model declined, the excerpts were *searched* but unused — an
    # empty source list makes the refusal unambiguous in the UI.
    refused = REFUSAL.lower() in answer.lower()
    return {
        "answer": answer,
        "sources": [] if refused else format_sources(results),
        "results": results,
    }


# ---------------------------------------------------------------- testing

OUT_OF_DOMAIN_QUERY = "What's the best dining hall on campus?"  # per planning.md


def run_tests():
    for question in [*EVAL_QUERIES, OUT_OF_DOMAIN_QUERY]:
        print("\n" + "=" * 78)
        print(f"QUESTION: {question}")
        print("=" * 78)
        result = ask(question)
        print(result["answer"])
        print("\nSources:")
        if result["sources"]:
            for s in result["sources"]:
                print(f"  - {s}")
        else:
            print("  (none — system declined to answer)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_tests()
    elif len(sys.argv) > 1:
        result = ask(" ".join(sys.argv[1:]))
        print(result["answer"])
        print("\nSources:")
        for s in result["sources"]:
            print(f"  - {s}")
    else:
        print(__doc__)
