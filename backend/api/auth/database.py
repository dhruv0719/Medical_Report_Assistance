# backend/api/auth/database.py
import os
from typing import AsyncGenerator
from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.api.auth.models import User, Base
from config.settings import settings

# 1. Get the URL from settings
database_url = settings.DATABASE_URL

# 2. Fix the URL for asyncpg
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif database_url.startswith("sqlite:///"):
    database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

# Remove sslmode query param if present, as asyncpg handles it differently
if "?" in database_url:
    base_url, query = database_url.split("?", 1)
    params = query.split("&")

    # Filter out problematic params
    allowed_params = []
    for p in params:
        key = p.split("=")[0]
        if key not in ["sslmode", "channel_binding"]:
            allowed_params.append(p)
            
    if allowed_params:
        database_url = f"{base_url}?{'&'.join(allowed_params)}"
    else:
        database_url = base_url

# 3. Create the engine 
engine = create_async_engine(
    database_url,
    connect_args={
        "ssl": "require"  # Force SSL for asyncpg
    }
)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)