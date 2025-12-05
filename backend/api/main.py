# backend/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import analysis, users, health
from backend.audit.database import init_db as init_audit_db
from backend.api.auth.models import Base as UserBase
from backend.api.auth.database import engine as user_engine
from config.settings import APIConfig
from config.logging_config import setup_logging

# Setup logging on startup
setup_logging()

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
app.include_router(analysis.router, prefix="/api/v1")

@app.on_event("startup")
async def on_startup():
    """
    Initialize databases on application startup.
    """
    # Create user database tables
    async with user_engine.begin() as conn:
        await conn.run_sync(UserBase.metadata.create_all)
    
    # Create audit log database tables
    init_audit_db()

@app.get("/", include_in_schema=False)
def root():
    return {"message": "Medical Report Assistant API is running!"}