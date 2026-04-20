import os

from app.parsers import parse_pdf, parse_txt
from app.store import update_status
from app.utils import chunk_text
from app.vectorstore import add_chunks


def ingest_document(document_id: str, filename: str, file_path: str):
    update_status(document_id, {
        "document_id": document_id,
        "filename": filename,
        "status": "processing",
        "chunks_indexed": 0,
        "error": None,
    })

    try:
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".txt":
            text = parse_txt(file_path)
        elif ext == ".pdf":
            text = parse_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        chunks = chunk_text(text, chunk_size_words=500, overlap_words=75)

        records = []
        for i, chunk in enumerate(chunks):
            if len(chunk.split()) < 20:
                continue

            records.append({
                "document_id": document_id,
                "chunk_id": f"{document_id}-chunk-{i}",
                "filename": filename,
                "text": chunk,
            })

        if records:
            add_chunks(records)

        update_status(document_id, {
            "document_id": document_id,
            "filename": filename,
            "status": "ready",
            "chunks_indexed": len(records),
            "error": None,
        })

    except Exception as exc:
        update_status(document_id, {
            "document_id": document_id,
            "filename": filename,
            "status": "failed",
            "chunks_indexed": 0,
            "error": str(exc),
        })