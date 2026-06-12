"""Milestone 4 — Embedding, vector store, and retrieval.

Implements the spec in planning.md (Retrieval Approach + Architecture):

  build_index()        -> embed every chunk from ingest.load_chunks() with
                          all-MiniLM-L6-v2 and upsert into a persistent
                          ChromaDB collection (cosine space) with full
                          source metadata for attribution.
  retrieve(query, k=5) -> top-k chunks for a query string, each with its
                          text, metadata (source URL, filename, date,
                          score, ...), and cosine distance.

Usage:
  python build_index.py                  # (re)build the index
  python build_index.py --test           # run the 5 evaluation-plan queries
  python build_index.py "free text..."   # retrieve for an ad-hoc query
"""

from __future__ import annotations

import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from ingest import load_chunks

CHROMA_DIR = Path(__file__).parent / "chroma_db"
COLLECTION_NAME = "ut_housing"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # per planning.md: local, free, 256-token cap
TOP_K = 5                              # per planning.md Retrieval Approach

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it (it's slow to initialize)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # Cosine distance, not the default L2 — planning.md specifies cosine, and
    # it makes the "distance < 0.5" sanity threshold meaningful.
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------- indexing

def build_index() -> chromadb.Collection:
    """Embed all chunks and load them into ChromaDB. Safe to re-run (rebuilds)."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)   # rebuild from scratch
    except Exception:
        pass
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    chunks = load_chunks()
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    # Deterministic, human-readable IDs: file + comment index + split part.
    ids = [
        f"{m['filename']}::{m['kind']}-{m['unit']}-{m['part']}"
        for m in metadatas
    ]

    print(f"Embedding {len(texts)} chunks with {EMBEDDING_MODEL} ...")
    embeddings = get_model().encode(texts, show_progress_bar=True)

    collection.add(
        ids=ids,
        embeddings=embeddings.tolist(),
        documents=texts,
        metadatas=metadatas,
    )
    print(f"Indexed {collection.count()} chunks into {CHROMA_DIR.name}/ "
          f"(collection '{COLLECTION_NAME}')")
    return collection


# ---------------------------------------------------------------- retrieval

def retrieve(query: str, k: int = TOP_K) -> list[dict]:
    """Return the top-k chunks for a query.

    Each result: {"text": str, "metadata": dict, "distance": float}
    (cosine distance: 0 = identical, lower = more similar).
    """
    query_embedding = get_model().encode([query])
    results = get_collection().query(
        query_embeddings=query_embedding.tolist(),
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    return [
        {"text": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


# ---------------------------------------------------------------- testing

EVAL_QUERIES = [
    "What do students say about living at 26 West?",
    "Is it cheaper to live in Riverside with a car or West Campus without one?",
    "When should I sign a lease for the fall semester, and what happens if I sign too early?",
    "What parking scams should students watch out for near West Campus?",
    "Is the Castilian a good housing option for sophomores?",
]


def run_eval_queries():
    for query in EVAL_QUERIES:
        print("\n" + "=" * 78)
        print(f"QUERY: {query}")
        print("=" * 78)
        for rank, r in enumerate(retrieve(query), start=1):
            m = r["metadata"]
            print(f"\n[{rank}] distance={r['distance']:.3f}  "
                  f"{m['filename']}  ({m['kind']} #{m['unit']}, score {m['score']})")
            print(f"    posted {m['posted']} | {m['source']}")
            text = r["text"]
            print("    " + text.replace("\n", "\n    "))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        run_eval_queries()
    elif len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        for rank, r in enumerate(retrieve(query), start=1):
            m = r["metadata"]
            print(f"\n[{rank}] distance={r['distance']:.3f}  {m['filename']}")
            print(r["text"])
    else:
        build_index()
