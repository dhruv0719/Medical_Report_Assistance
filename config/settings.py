# config/settings.py
"""Central configuration file for the Medical Report Assistant.
All paths, API keys, model configurations, and constants are defined here."""

import os
from pathlib import Path
from typing import List, Dict
try:
    from pydantic_settings import BaseSettings
except Exception:  # pragma: no cover - fallback when pydantic-settings isn't available
    # Minimal fallback so the rest of the code can import in lightweight/dev
    class BaseSettings:  # type: ignore
        def __init__(self, *args, **kwargs):
            # no-op initializer; many modules in tests read class attributes
            return None
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
BACKEND_DIR = BASE_DIR / "backend"

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/audit.db")
    
    # GROQ / LLM keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    # Pydantic v2 compatible settings to ignore extra environment variables
    # which can cause validation errors when unrelated env vars are present.
    model_config = {
        "extra": "ignore",
        "env_file": ".env",
        "case_sensitive": True,
    }
    
    # Note: pydantic v2 uses `model_config`. We intentionally do not define
    # a `Config` inner class to avoid the "Config and model_config cannot be
    # used together" error when pydantic v2 is installed.

# Initialize settings
settings = Settings()

# =============================================================================
# PATH CONFIGURATION
# =============================================================================

class Paths:
    """All file system paths used in the application"""
    
    # Base directories
    BASE = BASE_DIR
    DATA = DATA_DIR
    LOGS = LOGS_DIR
    BACKEND = BACKEND_DIR
    
    # Data subdirectories
    SYNTHETIC_REPORTS = DATA_DIR / "synthetic_reports"
    KNOWLEDGE_BASE = DATA_DIR / "knowledge_base"
    EMBEDDINGS = DATA_DIR / "embeddings"
    CHROMA_DB = DATA_DIR / "embeddings" / "chroma_db"
    
    # Knowledge sources
    MEDLINEPLUS_DATA = KNOWLEDGE_BASE / "medlineplus"
    STATPEARLS_DATA = KNOWLEDGE_BASE / "statpearls"
    
    # Log files
    APP_LOG = LOGS_DIR / "app.log"
    AUDIT_LOG = LOGS_DIR / "audit.log"
    ERROR_LOG = LOGS_DIR / "error.log"
    
    # Database
    AUDIT_DB = BASE_DIR / "audit.db"
    
    @classmethod
    def ensure_directories(cls):
        """Create all necessary directories if they don't exist"""
        directories = [
            cls.DATA,
            cls.LOGS,
            cls.SYNTHETIC_REPORTS,
            cls.KNOWLEDGE_BASE,
            cls.EMBEDDINGS,
            cls.CHROMA_DB,
            cls.MEDLINEPLUS_DATA,
            cls.STATPEARLS_DATA,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

class ModelConfig:
    """Configuration for AI models"""
    
    # Embedding Model
    EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384
    EMBEDDING_DEVICE = "cpu"  # Change to "cuda" if GPU available
    
    # LLM Configuration
    LLM_PROVIDER = "groq"  
    LLM_MODEL = "qwen/qwen3-32b" 
    LLM_TEMPERATURE = 0.3  # Low temperature for consistency
    LLM_MAX_TOKENS = 4000
    LLM_TOP_P = 0.9
    
    # Alternative models for future
    PRODUCTION_LLM_MODEL = "llama-3.3-70b-versatile"
    FALLBACK_LLM_MODEL = "llama-3.1-8b-instant"

# =============================================================================
# RAG CONFIGURATION
# =============================================================================

class RAGConfig:
    """Configuration for Retrieval-Augmented Generation"""
    
    # Vector Database
    VECTOR_DB_TYPE = "chromadb"
    COLLECTION_NAME = "medical_knowledge"
    
    # Retrieval parameters
    TOP_K_RESULTS = 5
    SIMILARITY_THRESHOLD = 0.60
    
    # Chunking parameters for knowledge ingestion
    CHUNK_SIZE = 2500  # characters
    CHUNK_OVERLAP = 100


# =============================================================================
# FILE UPLOAD CONFIGURATION
# =============================================================================

class UploadConfig:
    """Configuration for file uploads"""
    
    # File size limits
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    
    # File types
    ALLOWED_EXTENSIONS = ["pdf", "txt"]
    ALLOWED_MIME_TYPES = [
        "application/pdf",
        "text/plain",
    ]
    
    # OCR settings
    OCR_LANGUAGE = "eng"
    OCR_DPI = 300
    MIN_TEXT_LENGTH = 50  # Minimum characters to consider valid extraction


# =============================================================================
# PARSING CONFIGURATION
# =============================================================================

class ParserConfig:
    """Configuration for medical report parsing"""
    
    # Common lab test name variations
    TEST_NAME_ALIASES: Dict[str, List[str]] = {
        "hemoglobin": ["hgb", "hb", "hemoglobin"],
        "hematocrit": ["hct", "hematocrit"],
        "wbc": ["white blood cell", "wbc", "leukocyte"],
        "rbc": ["red blood cell", "rbc", "erythrocyte"],
        "platelet": ["plt", "platelet", "platelet count"],
        "glucose": ["glu", "glucose", "blood sugar"],
        "potassium": ["k", "k+", "potassium"],
        "sodium": ["na", "na+", "sodium"],
        "creatinine": ["cr", "creat", "creatinine"],
        "bun": ["bun", "blood urea nitrogen"],
    }
    
    # Units normalization
    UNIT_ALIASES: Dict[str, List[str]] = {
        "g/dL": ["g/dl", "gm/dl", "g/dL"],
        "mg/dL": ["mg/dl", "mg/dL"],
        "mEq/L": ["meq/l", "mEq/L", "mmol/L"],
        "x10³/µL": ["x10^3/ul", "x10³/µL", "K/uL"],
    }

# =============================================================================
# API CONFIGURATION
# =============================================================================

class APIConfig:
    """Configuration for FastAPI application"""
    
    # API metadata
    TITLE = "Medical Report Assistant API"
    DESCRIPTION = "AI-powered medical report explainer with safety triage"
    VERSION = "0.1.0"
    
    # CORS
    # Read from environment variable, default to localhost list if not found
    _cors_env = os.getenv("CORS_ORIGINS")
    if _cors_env:
        # Split by comma if multiple origins provided
        CORS_ORIGINS = [origin.strip() for origin in _cors_env.split(",")]
    else:
        # Fallback for local development
        CORS_ORIGINS = [
            "http://localhost:3000",
            "http://localhost:8501",
            "http://localhost:8000",
        ]
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_PERIOD = 3600  # 1 hour in seconds
    
    # Session
    SESSION_EXPIRY_HOURS = 24

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

class LogConfig:
    """Logging configuration"""
    
    # Log levels
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Log format
    LOG_FORMAT = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Rotation
    LOG_ROTATION = "100 MB"
    LOG_RETENTION = "30 days"
    
    # Separate log files
    LOGS = {
        "app": {
            "path": Paths.APP_LOG,
            "level": "INFO",
            "rotation": LOG_ROTATION,
        },
        "audit": {
            "path": Paths.AUDIT_LOG,
            "level": "INFO",
            "rotation": LOG_ROTATION,
        },
        "error": {
            "path": Paths.ERROR_LOG,
            "level": "ERROR",
            "rotation": LOG_ROTATION,
        },
    }


# =============================================================================
# MEDICAL CONFIGURATION
# =============================================================================

class MedicalConfig:
    """Medical-specific configuration"""
    
    # Disclaimer text
    DISCLAIMER_TEXT = """
    ⚠️ IMPORTANT DISCLAIMER:
    
    This tool is for informational and educational purposes only. It does NOT:
    - Provide medical advice, diagnosis, or treatment recommendations
    - Replace consultation with qualified healthcare professionals
    - Guarantee accuracy or completeness of information
    
    ALWAYS discuss your test results with your healthcare provider.
    In case of medical emergency, call emergency services immediately.
    """
    
    # Critical value notification
    CRITICAL_VALUE_MESSAGE = """
    🚨 CRITICAL VALUE DETECTED 🚨
    
    This result requires immediate medical attention.
    Please contact your healthcare provider or seek emergency care immediately.
    """
    
    # Sources to cite
    TRUSTED_SOURCES = [
        "MedlinePlus (NIH)",
        "StatPearls (NCBI)",
        "CDC Clinical Guidelines",
        "Mayo Clinic",
    ]


# =============================================================================
# AUDIT & COMPLIANCE
# =============================================================================

class AuditConfig:
    """Audit and compliance configuration"""
    
    # Data retention
    AUDIT_LOG_RETENTION_DAYS = 365
    SESSION_DATA_RETENTION_DAYS = 30
    
    # What to log
    LOG_FILE_UPLOADS = True
    LOG_PARSING_RESULTS = True
    LOG_LLM_CALLS = True
    LOG_SAFETY_ALERTS = True
    LOG_USER_INTERACTIONS = True
    
    # Anonymization
    ANONYMIZE_PATIENT_DATA = True
    HASH_SENSITIVE_FIELDS = True


# =============================================================================
# FEATURE FLAGS
# =============================================================================

class FeatureFlags:
    """Toggle features on/off"""
    
    ENABLE_OCR = True
    ENABLE_LLM_EXPLANATIONS = True
    ENABLE_SAFETY_TRIAGE = True
    ENABLE_AUDIT_LOGGING = True
    ENABLE_RAG = True
    
    # Future features
    ENABLE_MULTI_LANGUAGE = False
    ENABLE_VOICE_INPUT = False
    ENABLE_EXPORT_PDF = False


# =============================================================================
# INITIALIZE ON IMPORT
# =============================================================================

# Ensure all directories exist
Paths.ensure_directories()

# Validation
if not settings.GROQ_API_KEY and FeatureFlags.ENABLE_LLM_EXPLANATIONS:
    print("⚠️  WARNING: GROQ_API_KEY not set. LLM features will not work.")

if settings.ENVIRONMENT == "production":
    # Production-specific checks
    if settings.SECRET_KEY == "dev-secret-key-change-in-production":
        raise ValueError("❌ Must set a secure SECRET_KEY in production!")
    
    if settings.DEBUG:
        print("⚠️  WARNING: DEBUG mode enabled in production!")


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "settings",
    "Paths",
    "ModelConfig",
    "RAGConfig",
    "UploadConfig",
    "ParserConfig",
    "APIConfig",
    "LogConfig",
    "MedicalConfig",
    "AuditConfig",
    "FeatureFlags",
]