# Ambitio Document Intelligence Pipeline

This project is part of the **Ambitio Internship Assignment**.

It is a **FastAPI-based Document Intelligence System** that processes legal-style PDF documents, performs OCR and semantic retrieval, generates grounded legal drafts using Google Gemini 2.5 Flash, and continuously improves through a human feedback learning loop.

---

## Features

### Document Processing
- PDF text extraction using PyMuPDF
- OCR fallback using Tesseract OCR
- Text cleaning and normalization
- Sentence-aware chunking
- Structured metadata generation

### Grounded Retrieval
- Semantic search using Sentence Transformers
- FAISS vector indexing
- Evidence-based retrieval
- Traceable source chunks

### Draft Generation
Supported draft types:
- Case Fact Summary
- Title Review Summary
- Internal Memo
- Document Checklist

Features:
- Grounded generation using retrieved evidence
- Source citations
- Confidence scoring
- Gemini-powered draft generation

### Feedback Learning Loop
- Capture operator edits
- Extract reusable patterns
- Learn preferred terminology
- Persist learned patterns
- Track learning statistics

---

## Project Structure

```text
ambitio-doc-pipeline/
│
├── app/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── prompts.py
│   ├── retriever.py
│   ├── drafter.py
│   ├── feedback.py
│   ├── utils.py
│   │
│   └── processing/
│       ├── __init__.py
│       ├── extractor.py
│       ├── cleaner.py
│       └── chunker.py
│
├── data/
│   ├── sample_docs/
│   ├── processed/
│   ├── sample_outputs/
│   ├── edit_store.json
│   └── learned_patterns.json
│
├── storage/
│   └── faiss_index/
│
├── frontend/
│   └── index.html
│
├── tests/
│   ├── test_processing.py
│   ├── test_retrieval.py
│   └── test_feedback.py
│
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### Clone Repository

```bash
git clone <your-github-repository-url>
cd ambitio-doc-pipeline
```

### Create Virtual Environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key

MODEL_NAME=gemini-2.5-flash
MAX_OUTPUT_TOKENS=2048

EMBEDDING_MODEL=all-MiniLM-L6-v2

TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

CHUNK_SIZE=500
CHUNK_OVERLAP=50

TOP_K_CHUNKS=5
```

### Run Application

```bash
uvicorn app.main:app --reload
```

Swagger UI:
![HomePage](<Screenshot (527).png>)
```text
http://127.0.0.1:8000/docs
```

---

## API Endpoints

### Health Check

```http
GET /health
```

### Process Document
![Process Doc](<Screenshot (528).png>)
```http
POST /process
```

### Generate Draft
![Draft Post](<Screenshot (529).png>)
```http
POST /draft
```

### Submit Feedback
![Feedback Post](<Screenshot (530).png>)
```http
POST /feedback
```

### Retrieval Statistics

```http
GET /stats/index
```

### Learning Statistics

```http
GET /stats/learning
```

---

## Demo Workflow

1. Place a PDF in `data/sample_docs/`
2. Call `POST /process`
3. Generate a draft using `POST /draft`
4. Review and edit draft
5. Submit edits via `POST /feedback`
6. System learns reusable patterns

---

## Requirements Coverage

- OCR and text extraction
- Grounded retrieval
- Evidence-based drafting
- Human feedback loop
- Pattern learning
- Learning analytics
- FastAPI APIs
- Swagger documentation

---

## Tech Stack

- Python
- FastAPI
- Google Gemini 2.5 Flash
- Sentence Transformers
- FAISS
- PyMuPDF
- Tesseract OCR
- Pydantic

---

## Status

✅ Document Processing

✅ OCR Extraction

✅ Grounded Retrieval

✅ Draft Generation

✅ Feedback Learning

✅ Pattern Persistence

✅ FastAPI APIs

✅ Swagger Documentation
