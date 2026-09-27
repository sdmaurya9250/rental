from fastapi import APIRouter, status, Request
from models.user import RegisterRequest, LoginRequest, UserResponse
from services.auth_service import register_user, login_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, request: Request):
    db = request.scope["env"].DB
    return await register_user(data, db)


@router.post("/login")
async def login(data: LoginRequest, request: Request):
    db = request.scope["env"].DB
    return await login_user(data, db)