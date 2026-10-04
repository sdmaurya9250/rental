# from fastapi import APIRouter, status, Request, HTTPException
# from models.user import RegisterRequest, LoginRequest, UserResponse, TokenResponse
# from services.auth_service import register_user, login_user
#
# router = APIRouter()
#
#
# @router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
# async def register(data: RegisterRequest, request: Request):
#     try:
#         db = request.scope["env"].DB
#         return await register_user(data, db)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
#
# @router.post("/login", response_model=TokenResponse)
# async def login(data: LoginRequest, request: Request):
#     try:
#         db = request.scope["env"].DB
#         return await login_user(data, db)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


from fastapi import APIRouter, status, Request, HTTPException
from models.user import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from services.auth_service import (
    register_user,
    login_user,
    forgot_password,
    reset_password,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, request: Request):
    try:
        db = request.scope["env"].DB
        return await register_user(data, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request: Request):
    try:
        db = request.scope["env"].DB
        return await login_user(data, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/forgot-password")
async def forgot_password_route(data: ForgotPasswordRequest, request: Request):
    try:
        db = request.scope["env"].DB
        return await forgot_password(data, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-password")
async def reset_password_route(data: ResetPasswordRequest, request: Request):
    try:
        db = request.scope["env"].DB
        return await reset_password(data, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))