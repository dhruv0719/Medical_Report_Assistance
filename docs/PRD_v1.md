# Product Requirements Document (PRD) — Version 1.0
## AI-Powered Medical Report Assistant

### 1. Document Control
*   **Version:** 1.0
*   **Status:** Draft / Complete
*   **Author:** Product & Engineering Team
*   **Last Updated:** May 2026

---

### 2. Executive Summary
Medical laboratory tests are a critical pillar of clinical diagnostics. However, patient-facing lab reports are historically designed for medical professionals. They are filled with dense clinical terminology, confusing abbreviations, scientific units, and reference ranges that are difficult for laypersons to interpret.

This disconnect causes two major issues:
1.  **Patient Anxiety:** Patients often receive their lab results online (via portals) days before their follow-up appointment. Misinterpreting minor abnormalities can lead to unnecessary panic and web-search self-diagnosis.
2.  **Missed Critical Alerts:** Patients may overlook severe abnormalities ("critical values") that require immediate, emergency medical intervention, assuming they can wait until their scheduled doctor visit.

The **Medical Report Assistant (v1)** is an intelligent, secure, patient-centered application designed to bridge this gap. It processes raw medical reports (PDF/TXT), extracts structured lab values, categorizes results based on established clinical guidelines, and utilizes Retrieval-Augmented Generation (RAG) to deliver clear, empathetic, and scientifically grounded explanations.

---

### 3. Target Audience & User Personas

#### 3.1 Target Audience
*   **Primary Users:** Patients who receive laboratory results and want to understand their metrics in plain language before speaking with their primary care physician.
*   **Secondary Users:** Family members or caregivers managing the healthcare of elderly or chronic-disease patients.
*   **Tertiary Beneficiaries:** Healthcare providers who benefit from better-informed patients and a reduction in anxious, routine inquiries regarding completely normal test results.

#### 3.2 User Personas
*   **Persona A: "The Anxious Patient" (Sarah, 34)**
    *   *Need:* Sarah received her annual lipid panel. She has three values marked high in red. She is extremely stressed and wants to know what they mean immediately without waiting five days for her doctor's call.
    *   *App Value:* Provides immediate reassurance, defines "LDL" and "Cholesterol" in simple terms, and lists basic dietary adjustments she can discuss with her doctor.
*   **Persona B: "The Chronic Patient Caregiver" (Robert, 52)**
    *   *Need:* Robert monitors his elderly father's blood tests (CBC, BMP) regularly. Keeping track of fluctuating values like Hemoglobin or Potassium is tiring.
    *   *App Value:* Easily uploads scanned PDFs, parses the numbers into a clean table, highlights which values are outside the normal range, and suggests when to notify the cardiologist.

---

### 4. Core Value Proposition
*   **Accurate Extraction:** Automated digitization of unstructured reports (raw text or scanned PDFs) using OCR and advanced parsing.
*   **Clinical Safety Triage:** Immediate, automated classification of results into *Normal*, *Abnormal*, and *Critical* severity tiers based on guidelines (ARUP, CAP, CLSI).
*   **Grounded Explanations (RAG):** AI-generated text strictly grounded in high-quality reference data (MedlinePlus, StatPearls) to prevent hallucinations.
*   **Privacy & Compliance Audit:** Local database storage of user accounts and encrypted/anonymized system transactions, enabling compliance tracking.

---

### 5. Functional Requirements (v1 Feature Set)

#### 5.1 User Authentication & Authorization
*   **Secure Accounts:** Users must be able to register, log in, request password resets, and verify accounts.
*   **Token Authentication:** Secure stateless session handling via JSON Web Tokens (JWT).
*   **Data Isolation:** Users can only upload and view their own report analysis results.

#### 5.2 Document Ingestion & Extraction (OCR)
*   **Format Support:** Support for plain text (`.txt`) and Portable Document Format (`.pdf`) uploads.
*   **OCR Fallback:** If a PDF is image-based (scanned document) rather than text-based, the system must automatically invoke an Optical Character Recognition (OCR) engine (Tesseract) to extract the text.
*   **Validation:** Files must be restricted to a maximum size (default: 10MB) and validated to ensure security (filename sanitization, MIME-type checks).

#### 5.3 Medical Data Parsing Engine
*   **Regex Extraction:** The system must match text against predefined regular expressions for the top 20 most common laboratory tests (e.g., Hemoglobin, Potassium, Glucose, Sodium, TSH, WBC).
*   **LLM Extraction Fallback:** If regex parsing fails to identify at least three valid tests (often due to messy layout or OCR noise), the system must fall back to an LLM-based parser. The LLM must output a strictly structured JSON object containing patient metadata, tests, values, reference ranges, and clinical impressions.

#### 5.4 Safety Triage & Alerting System
*   **Urgency Evaluation:** Individual tests must be evaluated against established physiological thresholds:
    *   *Normal:* Value lies within the reference range.
    *   *Abnormal:* Value lies outside the reference range but remains within safe limits.
    *   *Critical:* Value is significantly outside normal limits, indicating potential medical emergencies (e.g., Potassium < 2.5 or > 6.5 mEq/L).
*   **Immediate Warning Banner:** If any critical value is found, the system must trigger a high-visibility, non-dismissible critical warning banner directing the user to seek immediate emergency medical care.

#### 5.5 Retrieval-Augmented Generation (RAG)
*   **Medical Knowledge Base:** A vector database (ChromaDB) populated with scraped clinical documentation from trusted public sources (MedlinePlus, StatPearls).
*   **Semantic Retrieval:** For each parsed test, the system must query the vector store using dense embeddings to retrieve the most relevant explanation guidelines.
*   **Similarity Gating:** Retrieved articles must meet a minimum similarity score (default: 0.60) to be included in the generation context.

#### 5.6 Patient-Friendly Explanations
*   **Contextual Explanations:** The LLM must write a 3-4 paragraph summary of the test purpose, result meaning, possible causes (if abnormal), and general next steps, utilizing the retrieved reference texts.
*   **Strict Safety Guardrails:** 
    *   The system *must never* diagnose the user with specific diseases.
    *   The system *must never* suggest medications or therapies.
    *   A mandatory disclaimer must accompany every explanation indicating that the tool is educational and does not replace a doctor.

#### 5.7 Audit Trail & Database Log
*   **Activity Logging:** The system must record detailed, structured logs of all key events in a relational database (SQLite/PostgreSQL) for compliance and debug purposes:
    *   File uploads (filename, file size, hash).
    *   Text extraction parameters (extraction method, time, character length).
    *   Parser statistics (number of tests parsed, abnormal count).
    *   LLM API call stats (tokens, response time, model version).
    *   Critical alerts triggered (test name, level, value).
    *   System error logs.

---

### 6. Non-Functional Requirements

#### 6.1 Performance & Latency
*   **OCR Extraction:** OCR processing on standard 1-page scanned reports must execute in under 10 seconds.
*   **Pipeline Execution:** End-to-end processing (Ingestion → Parsing → Triage → RAG → LLM Explanations) must complete within 15 seconds for a standard report.
*   **Database Queries:** Local database lookups for user auth and audits must resolve in under 100 milliseconds.

#### 6.2 Security & Compliance
*   **Local Storage by Default:** Designed to deploy locally or in private VPCs, keeping sensitive data off public cloud servers unless explicitly configured.
*   **Data Security:** User passwords must be salted and hashed using `bcrypt` before storage. JWTs must expire within 1 hour.
*   **PII Anonymization:** Audit logs must anonymize patient names and only record a unique session ID and user ID hash.

#### 6.3 User Interface & Experience
*   **Web Dashboard:** Responsive web interface optimized for both desktop monitors and mobile screens.
*   **Aesthetic Quality:** Clean, modern, accessible interface utilizing smooth animations (Framer Motion) and clear color codes:
    *   *Green:* Normal/Healthy.
    *   *Yellow/Orange:* Abnormal (Routine follow-up).
    *   *Red (Flashing/Bold):* Critical (Emergency alert).

---

### 7. Success Metrics
*   **Extraction Success Rate:** > 95% of uploaded standard PDF reports successfully digitized.
*   **Parsing Accuracy:** > 90% accuracy in mapping test names, values, and units compared to manual input.
*   **Critical Value Catch Rate:** 100% of defined critical values correctly caught and flagged with zero false negatives.
*   **Average Processing Time:** Under 10 seconds average pipeline duration per report.

---

### 8. Product Roadmap (Future Scope)
*   **v1.5: Historical Trends & Longitudinal Tracking:** Charting test values (e.g., HbA1c, Cholesterol) over time across multiple uploaded reports to show visual health trajectories.
*   **v2.0: Multi-language Support:** Translation of explanations into Spanish, Hindi, French, and other local languages.
*   **v2.1: FHIR/HL7 Integration:** Direct integration with patient portals (Epic MyChart, Cerner) to import lab results automatically.
*   **v2.5: Voice Assistant:** Synthetic read-aloud option summarizing explanations for visually impaired users.
