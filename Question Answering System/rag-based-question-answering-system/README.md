# RAG-Based Question Answering System

A lightweight FastAPI-based Retrieval-Augmented Generation (RAG) API that lets users upload documents, index them as embeddings, retrieve relevant chunks with FAISS, and generate grounded answers using an LLM.

This project was built to demonstrate applied AI system design using document ingestion, chunking, embeddings, similarity search, background processing, and API-based answer generation.

---

## Overview

The system supports document-based question answering over uploaded PDF and TXT files. During ingestion, each document is parsed, split into overlapping chunks, embedded using a sentence-transformer model, and stored in a local FAISS vector index with metadata. At query time, the API embeds the user question, retrieves the most relevant chunks, and sends only those chunks to the LLM to generate a grounded answer.

---

## Features

- Upload and ingest PDF and TXT documents
- Background ingestion using FastAPI `BackgroundTasks`
- Full-document parsing followed by chunking with overlap
- Embedding generation using `sentence-transformers/all-MiniLM-L6-v2`
- Local FAISS vector store for semantic retrieval
- Metadata and status persistence using local JSON files
- Grounded answer generation using an LLM
- Pydantic request and response validation
- Basic in-memory rate limiting
- Query latency and similarity score tracking
- Swagger UI support through FastAPI `/docs`

---

## Tech Stack

- **Backend:** FastAPI
- **Validation:** Pydantic
- **Embedding model:** sentence-transformers (`all-MiniLM-L6-v2`)
- **Vector store:** FAISS
- **Document parsing:** pypdf, plain text reader
- **LLM provider:** Groq API or OpenAI-compatible API
- **Background jobs:** FastAPI `BackgroundTasks`

---

## Architecture

The high-level architecture is shown below:

**Upload → Parse → Chunk → Embed → Store in FAISS → Retrieve top-k chunks → LLM answer generation → API response**

Detailed architecture diagrams are available in the `docs/` folder.

---

## Project Structure

```text
rag-based-question-answering-system/
├── app/
│   ├── main.py
│   ├── schemas.py
│   ├── config.py
│   ├── utils.py
│   ├── parsers.py
│   ├── store.py
│   ├── vectorstore.py
│   ├── ingestion.py
│   ├── rate_limit.py
│   └── rag.py
├── data/
│   ├── uploads/
│   └── index/
├── docs/
│   ├── architecture-diagram.md
│   ├── architecture-diagram.txt
│   └── mandatory-explanations.md
├── requirements.txt
├── .env.example
├── README.md
└── .gitignore
```

---

## How It Works

### 1. Document ingestion
A user uploads a PDF or TXT file through the upload endpoint. The file is stored locally, and a background ingestion task begins.

### 2. Parsing and chunking
The document is parsed into raw text and split into overlapping chunks. Chunking is necessary because entire documents are too large and too coarse for effective retrieval [web:368][web:292].

### 3. Embedding and indexing
Each chunk is converted into a dense vector representation using a sentence-transformer model, then stored in a local FAISS index for semantic similarity search.

### 4. Retrieval
When the user asks a question, the question itself is embedded and compared against stored vectors. The API retrieves the top-k most relevant chunks.

### 5. Answer generation
Only the retrieved chunks are sent to the LLM. This keeps responses grounded, reduces irrelevant context, and aligns with standard RAG behavior [web:368][web:292].

---

## Setup

### Clone the repository

```bash
git clone <your-github-repo-link>
cd rag-based-question-answering-system
```

### Create a virtual environment

```bash
python -m venv .venv
```

### Activate the environment

**Linux / macOS**
```bash
source .venv/bin/activate
```

**Windows**
```bash
.venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Create environment file

**Linux / macOS**
```bash
cp .env.example .env
```

**Windows**
```bash
copy .env.example .env
```

---

## Environment Variables

Example `.env` configuration:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RATE_LIMIT_PER_MINUTE=30
TOP_K_DEFAULT=4
```

If you are using another OpenAI-compatible provider, update the API key and model values accordingly.

---

## Run the Project

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

Open the interactive API docs at:

```text
http://127.0.0.1:8000/docs
```

---

## API Endpoints

### Health check
```http
GET /health
```

### Upload document
```http
POST /documents/upload
```

Accepts PDF and TXT files.

### Check document status
```http
GET /documents/{document_id}/status
```

Returns ingestion status such as `queued`, `processing`, `ready`, or `failed`.

### Ask a question
```http
POST /questions/ask
```

Accepts a JSON request body with the user question and optional retrieval settings.

---

## Example Requests

### Upload a document

```bash
curl -X POST "http://127.0.0.1:8000/documents/upload" \
  -F "file=@sample.pdf"
```

### Check ingestion status

```bash
curl "http://127.0.0.1:8000/documents/<document_id>/status"
```

### Ask a question

```bash
curl -X POST "http://127.0.0.1:8000/questions/ask" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"What is the main objective of the document?\",\"top_k\":4}"
```

### Example response

```json
{
  "answer": "The main objective of the project is to build a RAG-based question answering system that allows users to upload documents and ask questions based on them.",
  "sources": [
    {
      "document_id": "example-id",
      "chunk_id": "example-chunk-id",
      "filename": "sample.pdf",
      "score": 0.1971,
      "text": "..."
    }
  ],
  "latency_ms": 729.77,
  "top_score": 0.1971
}
```

---

## Chunking Strategy

This project uses **500-word chunks with 75-word overlap** as a simple and reproducible baseline. The goal was to preserve enough context within each chunk while avoiding chunks so large that they become semantically coarse and reduce retrieval precision [web:292][web:368].

This chunking strategy was selected because:
- small chunks improve precision but may lose context,
- very large chunks preserve context but often reduce retrieval specificity,
- moderate overlap helps avoid losing meaning across chunk boundaries [web:292][web:368].

---

## Retrieval Failure Case

One retrieval failure case observed in this project occurs when the answer is spread across two adjacent chunks, but only one chunk is retrieved in the top-k results. In that situation, the generated answer may be incomplete even though the correct information exists in the document.

Another practical issue is that broad chunks may answer general questions well but can reduce precision for narrow factual questions. This shows why chunking strategy directly affects retrieval quality [web:368][web:381].

---

## Metrics Tracked

The system tracks the following runtime metrics:

- **Latency (ms):** total time taken to process a query and return an answer
- **Top similarity score:** similarity score of the highest-ranked retrieved chunk

Latency helps assess responsiveness, while similarity score offers a rough signal of retrieval confidence. For a more advanced system, additional metrics such as precision@k, recall@k, or human evaluation could also be added [web:292][web:381].

---

## Rate Limiting

A basic in-memory rate limiter is included to prevent excessive requests from a single client in a short time window. This is sufficient for local development and small demos, though a production system would use a distributed backend such as Redis.

---

## Limitations

- In-memory rate limiting is not suitable for multi-instance deployment
- JSON-based metadata persistence is simple but not ideal for large-scale systems
- PDF parsing quality depends on text extractability; scanned PDFs may require OCR
- Retrieval quality depends heavily on chunking strategy and document structure
- Without a valid LLM API key, the system falls back to extractive answering instead of full generative answering

---

## Future Improvements

- Redis-backed rate limiting
- Celery or RQ for scalable background processing
- OCR support for scanned PDFs
- Metadata-based filtering by file type, tag, or source
- Re-ranking for improved retrieval precision
- Better chunking strategies such as semantic or structure-aware chunking [web:368][web:292]
- Automated evaluation with retrieval and answer-quality benchmarks

---

## Author

**Abinaya Lakshmi Emana**