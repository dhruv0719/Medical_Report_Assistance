# # backend/api/routes/users.py
# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordRequestForm
# from fastapi_users import FastAPIUsers

# from backend.api.auth.models import User
# from backend.api.auth.schemas import UserRead, UserCreate, UserUpdate
# from backend.api.auth.logic import auth_backend, get_user_manager

# # This object handles all the user-related logic
# fastapi_users = FastAPIUsers[User, int](
#     get_user_manager,
#     [auth_backend],
# )

# # Create routers
# router = APIRouter()

# # We create a custom login route to ensure it handles form data correctly.
# @router.post("/auth/jwt/login")
# async def login(
#     form_data: OAuth2PasswordRequestForm = Depends(),
#     user_manager = Depends(get_user_manager)
# ):
#     """
#     OAuth2 compatible token login, get an access token for future requests.
#     """
#     # This is the new way to handle login with form data
#     user = await user_manager.authenticate(form_data)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Incorrect email or password",
#         )
    
#     # Create the token
#     token = await auth_backend.get_strategy().write_token(user)
#     return {"access_token": token, "token_type": "bearer"}

# # Auth routes (e.g., /auth/jwt/login)
# router.include_router(
#     fastapi_users.get_auth_router(auth_backend),
#     prefix="/auth/jwt",
#     tags=["auth"],
# )

# # Register routes (e.g., /auth/register)
# router.include_router(
#     fastapi_users.get_register_router(UserRead, UserCreate),
#     prefix="/auth",
#     tags=["auth"],
# )

# # User management routes (e.g., /users/me)
# router.include_router(
#     fastapi_users.get_users_router(UserRead, UserUpdate),
#     prefix="/users",
#     tags=["users"],
# )

# backend/api/routes/users.py
from fastapi import APIRouter, Depends
from fastapi_users import FastAPIUsers

from backend.api.auth.logic import auth_backend, get_user_manager, get_current_user_from_form
from backend.api.auth.models import User
from backend.api.auth.schemas import UserCreate, UserRead, UserUpdate

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

router = APIRouter()

# --- CUSTOM LOGIN ROUTE ---
@router.post("/auth/jwt/login", tags=["auth"])
async def login(
    user: User = Depends(get_current_user_from_form),
):
    """
    Login for an existing user. Returns an access token.
    This route is specifically designed to work with the FastAPI docs UI.
    """
    token = await auth_backend.get_strategy().write_token(user)
    return {"access_token": token, "token_type": "bearer"}
# -------------------------

# Auth routes (logout only, as we have a custom login)
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"],
)

# Register routes
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

# Forgot password and verification routes
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

# User management routes
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)