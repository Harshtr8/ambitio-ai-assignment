# Architecture Overview

## System Architecture

The Ambitio Document Intelligence Pipeline follows a Retrieval-Augmented Generation (RAG) architecture designed for processing legal-style documents.

### Flow

PDF Document
↓
Text Extraction (PyMuPDF)
↓
OCR Fallback (Tesseract)
↓
Text Cleaning & Normalization
↓
Sentence-Aware Chunking
↓
Embedding Generation (Sentence Transformers)
↓
FAISS Vector Storage
↓
Grounded Retrieval
↓
Gemini Draft Generation
↓
Operator Feedback
↓
Pattern Learning

## Components

### Document Processing

Responsible for:

* Extracting text from PDFs
* Running OCR on scanned pages
* Cleaning noisy content
* Splitting content into chunks

### Retrieval Layer

Responsible for:

* Creating embeddings
* Indexing chunks using FAISS
* Retrieving relevant evidence for drafting

### Draft Generation

Responsible for:

* Generating structured drafts
* Grounding outputs in retrieved evidence
* Producing source traceability

### Feedback Learning

Responsible for:

* Capturing operator edits
* Learning reusable terminology preferences
* Persisting patterns for future drafts

## Design Goals

* Grounded outputs
* Explainable retrieval
* Human-in-the-loop improvement
* Modular architecture
* Easy local deployment
