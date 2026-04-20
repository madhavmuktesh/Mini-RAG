import os
import re
import uuid
from typing import List


def generate_document_id() -> str:
    return str(uuid.uuid4())


def get_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def chunk_text(text: str, chunk_size_words: int = 500, overlap_words: int = 75) -> List[str]:
    cleaned = re.sub(r"\r\n", "\n", text)
    paragraphs = [p.strip() for p in cleaned.split("\n") if p.strip()]

    chunks = []
    current_words = []

    for para in paragraphs:
        para_words = para.split()

        if len(current_words) + len(para_words) <= chunk_size_words:
            current_words.extend(para_words)
        else:
            if current_words:
                chunks.append(" ".join(current_words))
            overlap = current_words[-overlap_words:] if len(current_words) > overlap_words else current_words
            current_words = overlap + para_words

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks