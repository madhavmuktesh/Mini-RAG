import os
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.config import ALLOWED_EXTENSIONS, UPLOAD_DIR
from app.ingestion import ingest_document
from app.rate_limit import check_rate_limit
from app.rag import generate_answer
from app.schemas import AskRequest, AskResponse, DocumentStatusResponse, UploadResponse
from app.store import get_status, update_status
from app.utils import generate_document_id, get_extension

app = FastAPI(title="RAG-Based Question Answering System", version="1.0.0")

os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def root():
    return {"message": "RAG API is running. Open /docs to test the API."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/documents/upload", response_model=UploadResponse, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    _: None = Depends(check_rate_limit),
):
    ext = get_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported.")

    document_id = generate_document_id()
    stored_filename = f"{document_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    update_status(document_id, {
        "document_id": document_id,
        "filename": file.filename,
        "status": "queued",
        "chunks_indexed": 0,
        "error": None,
    })

    background_tasks.add_task(ingest_document, document_id, file.filename, file_path)

    return UploadResponse(
        document_id=document_id,
        filename=file.filename,
        status="queued",
        message="File uploaded successfully and ingestion started in background."
    )


@app.get("/documents/{document_id}/status", response_model=DocumentStatusResponse)
def document_status(document_id: str, _: None = Depends(check_rate_limit)):
    status = get_status(document_id)
    if not status:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentStatusResponse(**status)


@app.post("/questions/ask", response_model=AskResponse)
def ask_question(payload: AskRequest, _: None = Depends(check_rate_limit)):
    result = generate_answer(
        question=payload.question,
        document_ids=payload.document_ids,
        top_k=payload.top_k,
    )
    return AskResponse(**result)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})