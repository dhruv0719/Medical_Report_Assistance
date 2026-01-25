# backend/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import analysis, users, health
from backend.audit.database import init_db as init_audit_db
from backend.api.auth.models import Base as UserBase
from backend.api.auth.database import engine as user_engine
from config.settings import APIConfig
from config.logging_config import setup_logging, get_logger 
from scripts.setup_knowledge_base import setup_knowledge_base
from backend.rag.knowledge_base import KnowledgeBase

# Setup logging on startup
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=APIConfig.TITLE,
    description=APIConfig.DESCRIPTION,
    version=APIConfig.VERSION,
)

# Add CORS middleware to allow your frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=APIConfig.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all the different API routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1/analysis")

@app.on_event("startup")
async def on_startup():
    """
    Initialize databases on application startup.
    """
    logger.info("🚀 Starting up...")

    # Create user database tables
    try:
        logger.info("🛠️ DEBUG: Testing User DB Connection...")
        async with user_engine.begin() as conn:
            await conn.run_sync(UserBase.metadata.create_all)
        logger.info("✅ DEBUG: User DB Connected Successfully!")

    except Exception as e:
        logger.error(f"❌ DEBUG: User DB Connection Failed: {e}")
    
    # Create audit log database tables
    init_audit_db()

    # Check/Build Knowledge Base (Since Render disk is ephemeral)
    try:
        kb = KnowledgeBase()
        if kb.get_count() == 0:
            logger.info("🧠 Knowledge base empty (new deployment). Ingesting data...")
            setup_knowledge_base(reset=True)
        else:
            logger.info(f"🧠 Knowledge base loaded: {kb.get_count()} docs")
    except Exception as e:
        logger.error(f"❌ Error setting up knowledge base: {e}")

@app.get("/", include_in_schema=False)
def root():
    return {"message": "Medical Report Assistant API is running!"}