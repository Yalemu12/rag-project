"""Milestone 3 — Document ingestion and chunking.

Implements the spec in planning.md (Documents + Chunking Strategy):

  parse_document(path) -> {"metadata": {...}, "body": str, "comments": [{"score": int, "text": str}]}
  chunk_document(doc)  -> list of chunks: {"text": str, "metadata": {...}}
  load_chunks(dir)     -> all chunks across documents/ (used by Milestone 4)

Strategy: one chunk per comment (and one per post body), prefixed with
"[<thread title> | <category>]", capped at MAX_CHUNK_CHARS with
OVERLAP_CHARS of overlap only when a single long comment/body is split.
Comments shorter than MIN_COMMENT_CHARS (contextless one-liners like
"Thank you!") are dropped — see planning.md "Anticipated Challenges" #1.

Run directly for an inspection report:
  python ingest.py
"""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

DOCUMENTS_DIR = Path(__file__).parent / "documents"

MAX_CHUNK_CHARS = 1000   # all-MiniLM-L6-v2 truncates at ~256 tokens (~1000 chars)
OVERLAP_CHARS = 100      # only applied when one comment/body is split
# Drop contextless one-liners ("Thank you!", "12"). 80 (the original plan)
# proved too aggressive: it dropped eval-critical facts like "Castilian is 98%
# Freshman, don't live there if you're a sophomore" (65 chars).
MIN_COMMENT_CHARS = 50

COMMENT_DELIMITER = "--- COMMENTS ---"
SCORE_RE = re.compile(r"^\[score (-?\d+)\]\s*")
EMPTY_BODY_PLACEHOLDER = "(post body removed; see comments)"


# ---------------------------------------------------------------- parsing

def parse_document(path: Path) -> dict:
    """Split a documents/*.txt file into metadata header, post body, comments."""
    raw = path.read_text(encoding="utf-8")

    header, _, rest = raw.partition("\n---\n")
    metadata = {}
    for line in header.splitlines():
        key, _, value = line.partition(":")
        if value:
            metadata[key.strip().lower()] = value.strip()
    metadata["filename"] = path.name

    body_part, _, comments_part = rest.partition(COMMENT_DELIMITER)

    comments = []
    current_score: int | None = None
    current_lines: list[str] = []

    def flush():
        if current_score is not None:
            text = "\n".join(current_lines).strip()
            if text:
                comments.append({"score": current_score, "text": text})

    for line in comments_part.splitlines():
        m = SCORE_RE.match(line)
        if m:
            flush()
            current_score = int(m.group(1))
            current_lines = [line[m.end():]]
        elif current_score is not None:
            current_lines.append(line)
    flush()

    return {"metadata": metadata, "body": body_part.strip(), "comments": comments}


# ---------------------------------------------------------------- cleaning

MD_ESCAPE_RE = re.compile(r"\\([\\\-*_.\[\]()#&~>!])")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
WHITESPACE_RE = re.compile(r"[ \t]+")
BLANK_LINES_RE = re.compile(r"\n\s*\n+")


def clean_text(text: str) -> str:
    """Strip Reddit-markdown artifacts; keep the substantive content."""
    if text == EMPTY_BODY_PLACEHOLDER:
        return ""
    text = MD_ESCAPE_RE.sub(r"\1", text)          # \- escapes -> -
    text = MD_LINK_RE.sub(r"\1 (\2)", text)        # [text](url) -> text (url)
    text = WHITESPACE_RE.sub(" ", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


# ---------------------------------------------------------------- chunking

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _split_long_text(text: str, limit: int) -> list[str]:
    """Split text > limit at sentence boundaries with OVERLAP_CHARS overlap."""
    sentences = SENTENCE_RE.split(text)
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= limit or not current:
            current = candidate
        else:
            pieces.append(current)
            overlap = current[-OVERLAP_CHARS:]
            space = overlap.find(" ")              # snap overlap to a word boundary
            if space != -1:
                overlap = overlap[space + 1:]
            current = f"{overlap} {sentence}".strip()
    if current:
        pieces.append(current)

    # A single sentence can exceed the limit (run-on Reddit prose): hard-split it.
    final: list[str] = []
    for piece in pieces:
        while len(piece) > limit:
            cut = piece.rfind(" ", 0, limit)
            cut = cut if cut > 0 else limit
            final.append(piece[:cut])
            piece = piece[max(cut - OVERLAP_CHARS, 0):].strip()
        final.append(piece)
    return final


def chunk_document(doc: dict) -> list[dict]:
    """One chunk per comment + one per post body, title-prefixed, capped."""
    meta = doc["metadata"]
    prefix = f"[{meta['title']} | {meta.get('category', 'thread')}] "
    body_limit = MAX_CHUNK_CHARS - len(prefix)

    chunks = []

    def add(text: str, kind: str, score: int | None, unit_index: int):
        for part_index, piece in enumerate(_split_long_text(text, body_limit)):
            chunks.append({
                "text": prefix + piece,
                "metadata": {
                    "source": meta["source"],
                    "title": meta["title"],
                    "posted": meta.get("posted", ""),
                    "category": meta.get("category", ""),
                    "filename": meta["filename"],
                    "kind": kind,                  # "post" or "comment"
                    "score": score if score is not None else 0,
                    "unit": unit_index,            # which comment within the thread
                    "part": part_index,            # split index within one comment
                },
            })

    body = clean_text(doc["body"])
    if body:
        add(body, "post", None, 0)

    for i, comment in enumerate(doc["comments"], start=1):
        text = clean_text(comment["text"])
        if len(text) < MIN_COMMENT_CHARS:
            continue
        add(text, "comment", comment["score"], i)

    return chunks


def load_chunks(documents_dir: Path = DOCUMENTS_DIR) -> list[dict]:
    """Parse + clean + chunk every document. Entry point for Milestone 4."""
    chunks = []
    for path in sorted(documents_dir.glob("*.txt")):
        chunks.extend(chunk_document(parse_document(path)))
    return chunks


# ---------------------------------------------------------------- inspection

def report(seed: int | None = None):
    paths = sorted(DOCUMENTS_DIR.glob("*.txt"))
    print(f"Loaded {len(paths)} documents from {DOCUMENTS_DIR}/\n")

    print(f"{'file':<45} {'comments':>8} {'chunks':>7} {'dropped':>8}")
    all_chunks = []
    total_comments = 0
    total_dropped = 0
    for path in paths:
        doc = parse_document(path)
        chunks = chunk_document(doc)
        kept_units = {c["metadata"]["unit"] for c in chunks if c["metadata"]["kind"] == "comment"}
        dropped = len(doc["comments"]) - len(kept_units)
        total_comments += len(doc["comments"])
        total_dropped += dropped
        all_chunks.extend(chunks)
        print(f"{path.name:<45} {len(doc['comments']):>8} {len(chunks):>7} {dropped:>8}")

    lengths = [len(c["text"]) for c in all_chunks]
    print(f"\nTotal comments parsed: {total_comments}")
    print(f"Comments dropped (< {MIN_COMMENT_CHARS} chars): {total_dropped}")
    print(f"TOTAL CHUNKS: {len(all_chunks)}")
    print(f"Chunk length (chars): min={min(lengths)} avg={sum(lengths)//len(lengths)} max={max(lengths)}")

    assert all(len(c["text"]) > 0 for c in all_chunks), "empty chunk produced"
    assert all(len(c["text"]) <= MAX_CHUNK_CHARS for c in all_chunks), "chunk over cap"

    rng = random.Random(seed)
    print("\n" + "=" * 70)
    print("5 RANDOM CHUNKS FOR INSPECTION")
    print("=" * 70)
    for chunk in rng.sample(all_chunks, 5):
        m = chunk["metadata"]
        print(f"\n--- {m['filename']} | {m['kind']} #{m['unit']} part {m['part']} | "
              f"score {m['score']} | {len(chunk['text'])} chars ---")
        print(chunk["text"])

    out = Path(__file__).parent / "chunks.json"
    out.write_text(json.dumps(all_chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {len(all_chunks)} chunks to {out.name}")


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else None
    report(seed)
