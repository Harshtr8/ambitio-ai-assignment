# Assumptions and Tradeoffs

## Assumptions

### Documents are PDF Files

The system assumes input documents are provided in PDF format.

### English Language OCR

OCR processing is configured for English-language documents.

### Local Deployment

The solution is intended to run locally without requiring cloud infrastructure.

### Single User Workflow

The current implementation assumes a single operator reviewing generated drafts.

---

## Tradeoffs

### FAISS Instead of Managed Vector Databases

Chosen:

* FAISS

Alternatives:

* Pinecone
* Weaviate
* Chroma Cloud

Reason:
FAISS provides fast local retrieval and avoids external dependencies.

---

### File Storage Instead of Database

Chosen:

* JSON files

Alternatives:

* PostgreSQL
* MongoDB

Reason:
Simplifies setup and is sufficient for assignment scope.

---

### MiniLM Embeddings

Chosen:

* all-MiniLM-L6-v2

Reason:
Provides a strong balance between speed, memory usage, and retrieval quality.

---

### Gemini 2.5 Flash

Chosen:

* Gemini 2.5 Flash

Reason:
Fast response times and strong reasoning performance while remaining cost-effective.

---

## Future Improvements

* Multi-document retrieval
* Database persistence
* User authentication
* Hybrid search (BM25 + Vector Search)
* Production deployment support
