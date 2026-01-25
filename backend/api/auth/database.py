# backend/api/auth/database.py
import os
from typing import AsyncGenerator
from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.api.auth.models import User, Base
from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

logger.info("🛠️ DEBUG: Configuring Database...") 

# 1. Get the URL from settings
database_url = settings.DATABASE_URL

# 2. Fix the URL for asyncpg
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif database_url.startswith("sqlite:///"):
    database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

# 3. Clean up query parameters, We will pass SSL settings via connect_args instead
if "?" in database_url:
    base_url, query = database_url.split("?", 1)
    # Remove problematic params
    params = [p for p in query.split("&") if not p.startswith("sslmode=") and not p.startswith("channel_binding=")]
    if params:
        database_url = f"{base_url}?{'&'.join(params)}"
    else:
        database_url = base_url

# 4. Create the engine with EXPLICIT SSL CONTEXT
connect_args = {}
if "sqlite" not in database_url:
    # Only for Postgres/Neon
    connect_args = {"ssl": "require"}

logger.info(f"🛠️ DEBUG: Connecting to {database_url.split('@')[1] if '@' in database_url else 'SQLITE'}")

engine = create_async_engine(
    database_url,
    connect_args=connect_args,
    echo=True,  # Enable SQL query logging for debugging
)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)