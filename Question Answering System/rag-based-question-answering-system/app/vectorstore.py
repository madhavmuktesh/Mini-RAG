import os
from typing import List, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL, INDEX_DIR
from app.store import append_metadata, load_metadata

INDEX_PATH = os.path.join(INDEX_DIR, "faiss.index")

_model = None


def get_embedder():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed_texts(texts: List[str]) -> np.ndarray:
    model = get_embedder()
    vectors = model.encode(texts, normalize_embeddings=True)
    return np.asarray(vectors, dtype="float32")


def _load_or_create_index(dim: int):
    if os.path.exists(INDEX_PATH):
        return faiss.read_index(INDEX_PATH)
    return faiss.IndexFlatIP(dim)


def add_chunks(records: List[dict]):
    texts = [r["text"] for r in records]
    embeddings = embed_texts(texts)
    index = _load_or_create_index(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, INDEX_PATH)
    append_metadata(records)


def search(query: str, top_k: int = 4, document_ids: List[str] | None = None) -> List[Tuple[dict, float]]:
    if not os.path.exists(INDEX_PATH):
        return []

    index = faiss.read_index(INDEX_PATH)
    metadata = load_metadata()
    if not metadata:
        return []

    query_vector = embed_texts([query])
    scores, indices = index.search(query_vector, min(top_k * 5, len(metadata)))

    results = []
    seen_texts = set()

    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue

        if score < 0.10:
            continue

        record = metadata[idx]

        if document_ids and record["document_id"] not in document_ids:
            continue

        text_key = record["text"][:200].strip()
        if text_key in seen_texts:
            continue
        seen_texts.add(text_key)

        results.append((record, float(score)))

        if len(results) >= top_k:
            break

    return results