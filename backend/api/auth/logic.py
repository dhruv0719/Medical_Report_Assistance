# backend/api/auth/logic.py
from typing import Optional
from fastapi import Depends, Request, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import BaseUserManager, IntegerIDMixin
from fastapi_users.authentication import AuthenticationBackend, JWTStrategy, BearerTransport
from fastapi_users.db import SQLAlchemyUserDatabase

from config.settings import settings
from backend.api.auth.database import get_user_db
from backend.api.auth.models import User
from config.logging_config import get_logger

logger = get_logger(__name__)

# --- Secret for tokens ---
SECRET = settings.SECRET_KEY

# --- User Manager ---
class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        logger.info(f"User {user.id} has registered.")
        # You can add email sending logic here

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        logger.info(f"User {user.id} has requested a password reset. Token: {token}")
        # You can add email sending logic here


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


# --- Authentication Backend ---
bearer_transport = BearerTransport(tokenUrl="/api/v1/auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Create a dependency that performs the authentication logic.
# This makes it explicit that we need form data.
async def get_current_user_from_form(
        credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager)
) -> User:
    user = await user_manager.authenticate(credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user