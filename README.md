# Medical Report Assistant

An AI-powered web application designed to help patients understand their medical laboratory test results through secure digitization, clinical safety triage, and retrieval-augmented generation (RAG).

---

## 📚 Project Documentation

We have compiled a professional set of documentation covering the product requirements, system design, and API endpoints of the system. You can access these files in the `docs/` folder:

1.  **[Product Requirements Document (PRD_v1.md)](file:///d:/Medical_Assitance/docs/PRD_v1.md)**
    *   Outlines the product vision, core target audience, user personas, functional specifications, safety triage tiers, and the future product roadmap.
2.  **[Technical Design Document (TECH.md)](file:///d:/Medical_Assitance/docs/TECH.md)**
    *   Detailing the technical stack (FastAPI, Next.js, ChromaDB, Hugging Face, Groq), system architecture flow diagram, detailed pipeline steps, database schema design, and step-by-step developer environment setup instructions.
3.  **[API Reference Manual (API.md)](file:///d:/Medical_Assitance/docs/API.md)**
    *   Providing full specifications for all backend endpoints (Auth, User Management, Health, and Analysis), including HTTP methods, paths, request headers/bodies, and example JSON responses.

---

## 🚀 Quick Start Guide

### Backend Setup
1.  **Configure environment:** Create a `.env` file in the root directory following the parameters described in `docs/TECH.md`.
2.  **Install dependencies:**
    ```bash
    python -m venv .venv
    # Activate virtual environment:
    # Windows: .venv\Scripts\activate
    # macOS/Linux: source .venv/bin/activate
    pip install -r requirements.txt
    ```
3.  **Prepare the Vector Database:**
    ```bash
    python scripts/setup_knowledge_base.py --reset
    ```
4.  **Run the API:**
    ```bash
    uvicorn backend.api.main:app --reload
    ```

### Frontend Setup
1.  **Configure local settings:** Create a `frontend/.env.local` file setting `NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1`.
2.  **Run Development Server:**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
    Access the application at `http://localhost:3000`.
