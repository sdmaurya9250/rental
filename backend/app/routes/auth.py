from fastapi import APIRouter, status
from models.user import RegisterRequest, LoginRequest, UserResponse
from services.auth_service import register_user, login_user

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest):
    return register_user(data)


@router.post("/login")
async def login(data: LoginRequest):
    return login_user(data)