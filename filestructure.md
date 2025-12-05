medical-report-assistant/
│
├── README.md                          # Project documentation
├── requirements.txt                   # Python dependencies
├── .env                              # Environment variables (API keys)
├── .gitignore                        # Git ignore rules
├── setup.py                          # Package setup (optional)
│
├── config/
│   ├── __init__.py
│   ├── settings.py                   # Centralized configuration (paths, thresholds, API keys)
│   ├── logging_config.py             # Logging setup
│   └── prompts.py                    # LLM system prompts
│
├── backend/
│   ├── __init__.py
│   │
│   ├── ingestion/                    # STEP 1: Document Upload & OCR
│   │   ├── __init__.py
│   │   ├── document_processor.py     # Main: PDF/text extraction
│   │   ├── ocr_handler.py           # Tesseract OCR logic
│   │   └── validators.py            # File type/size validation
│   │
│   ├── parser/                       # STEP 2: Extract structured data
│   │   ├── __init__.py
│   │   ├── medical_parser.py        # Main: Extract tests, values, ranges
│   │   ├── patterns.py              # Regex patterns for lab tests
│   │   ├── normalizer.py            # Clean/normalize text
│   │   └── entities.py              # Data classes (LabTest, ParsedReport)
│   │
│   ├── rag/                          # STEP 3: Knowledge base for grounding
│   │   ├── __init__.py
│   │   ├── knowledge_base.py        # Main: ChromaDB wrapper
│   │   ├── embeddings.py            # Sentence transformer embeddings
│   │   ├── retriever.py             # Query knowledge base
│   │   └── ingestion/               # Populate knowledge base
│   │       ├── __init__.py
│   │       ├── load_medlineplus.py  # Scrape/load MedlinePlus
│   │       └── load_statpearls.py   # Load StatPearls content
│   │
│   ├── llm/                          # STEP 4: LLM explanations
│   │   ├── __init__.py
│   │   ├── explainer.py             # Main: Generate explanations
│   │   ├── groq_client.py           # GROQ API wrapper
│   │   └── prompt_builder.py        # Build prompts from templates
│   │
│   ├── safety/                       # STEP 5: Safety checks & triage
│   │   ├── __init__.py
│   │   ├── triage_engine.py         # Main: Evaluate critical values
│   │   ├── rules.py                 # Critical value thresholds
│   │   ├── alerts.py                # Alert data classes
│   │   └── next_steps.py            # Recommend actions
│   │
│   ├── audit/                        # STEP 6: Logging & compliance
│   │   ├── __init__.py
│   │   ├── audit_logger.py          # Main: Log all interactions
│   │   ├── database.py              # SQLite/PostgreSQL connection
│   │   └── models.py                # SQLAlchemy models
│   │
│   ├── api/                          # STEP 7: FastAPI endpoints
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app initialization
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── upload.py            # POST /upload endpoint
│   │   │   ├── explain.py           # POST /explain endpoint
│   │   │   └── health.py            # GET /health endpoint
│   │   ├── dependencies.py          # Dependency injection
│   │   └── schemas.py               # Pydantic request/response models
│   │
│   └── orchestrator/                 # STEP 8: Main workflow orchestrator
│       ├── __init__.py
│       └── pipeline.py              # Coordinates all steps end-to-end
│
├── frontend/
│   ├── streamlit_app.py             # Main Streamlit UI
│   ├── components/
│   │   ├── __init__.py
│   │   ├── file_uploader.py         # Upload widget
│   │   ├── results_display.py       # Show parsed results
│   │   ├── explanation_display.py   # Show LLM explanations
│   │   └── alerts_display.py        # Show safety alerts
│   └── utils.py                     # Helper functions
│
├── data/
│   ├── synthetic_reports/           # Test data
│   │   ├── manifest.json
│   │   ├── 01_normal.txt
│   │   ├── 02_mild_anemia.txt
│   │   └── ...
│   │
│   ├── knowledge_base/              # Medical reference content
│   │   ├── medlineplus/
│   │   │   ├── hemoglobin.txt
│   │   │   ├── potassium.txt
│   │   │   └── ...
│   │   └── statpearls/
│   │       └── ...
│   │
│   └── embeddings/                  # Cached vector embeddings
│       └── chroma_db/               # ChromaDB storage
│
├── logs/
│   ├── app.log                      # Application logs
│   └── audit.log                    # Audit trail (HIPAA compliance)
│
├── tests/
│   ├── __init__.py
│   ├── unit/                        # Unit tests
│   │   ├── test_parser.py
│   │   ├── test_triage.py
│   │   └── ...
│   ├── integration/                 # Integration tests
│   │   └── test_pipeline.py
│   └── fixtures/                    # Test fixtures
│       └── sample_reports.py
│
└── scripts/
    ├── setup_knowledge_base.py      # One-time: populate vector DB
    ├── generate_synthetic_data.py   # Create test reports
    └── run_tests.py                 # Run test suite