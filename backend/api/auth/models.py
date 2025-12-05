# backend/api/auth/models.py
from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Integer

Base = declarative_base()

class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)