# 🩺 Medical Report Assistant

An AI-powered medical report analysis system that helps users understand laboratory test results through Retrieval-Augmented Generation (RAG), clinical safety triage, and personalized AI-driven explanations.

## Overview

Medical reports are often difficult for patients to interpret due to complex medical terminology and fragmented information.

Medical Report Assistant bridges this gap by allowing users to upload medical reports and receive clear, contextual explanations of test results, potential concerns, and recommended next steps while maintaining transparency through grounded retrieval.

## Key Features

* 📄 Medical report upload and processing
* 🧠 AI-powered report explanation using LLMs
* 🔍 Retrieval-Augmented Generation (RAG) pipeline
* ⚠️ Clinical safety triage system
* 📚 Grounded responses from trusted medical knowledge
* 🔐 Secure user authentication and report management
* 💬 Conversational health assistant experience
* 🌐 Modern web interface built with Next.js

## System Architecture

```text
Medical Report
       │
       ▼
 Document Processing
       │
       ▼
 Information Extraction
       │
       ▼
 Vector Database (ChromaDB)
       │
       ▼
 Retrieval Pipeline
       │
       ▼
 Large Language Model
       │
       ▼
 Grounded Medical Explanation
```

## Tech Stack

| Layer           | Technologies                       |
| --------------- | ---------------------------------- |
| Frontend        | Next.js, TypeScript                |
| Backend         | FastAPI, Python                    |
| AI/LLM          | Groq, Llama Models                 |
| Embeddings      | Hugging Face Sentence Transformers |
| Vector Database | ChromaDB                           |
| Authentication  | JWT                                |
| Deployment      | Vercel                             |

## Documentation

Detailed project documentation is available inside the `docs/` directory:

* Product Requirements Document (PRD)
* Technical Design Document
* API Reference Documentation

## Live Demo

**Application:** https://medical-report-assistance.vercel.app

## Future Improvements

* Multi-language report analysis
* Doctor-facing clinical dashboard
* Longitudinal health tracking
* Advanced multimodal medical report understanding
* Personalized health recommendations

## Local Setup

### Backend

```bash
python -m venv .venv
pip install -r requirements.txt
python scripts/setup_knowledge_base.py --reset
uvicorn backend.api.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

