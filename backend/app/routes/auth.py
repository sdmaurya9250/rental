from fastapi import APIRouter, Request, HTTPException
from models.user import LoginRequest, TokenResponse
from services.auth_service import login_user

router = APIRouter()


# Sign-up and password reset use mobile OTP (see routes/otp_auth.py).
# Email register / login / forgot-password were removed.
@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request: Request):
    try:
        db = request.scope["env"].DB
        return await login_user(data, db)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Login failed")
