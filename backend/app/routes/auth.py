# from fastapi import APIRouter, status, Request, HTTPException
# from models.user import RegisterRequest, LoginRequest, UserResponse
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
#         raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
#
#
# @router.post("/login")
# async def login(data: LoginRequest, request: Request):
#     try:
#         db = request.scope["env"].DB
#         return await login_user(data, db)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


from fastapi import APIRouter, status, Request, HTTPException
from models.user import RegisterRequest, LoginRequest, UserResponse, TokenResponse
from services.auth_service import register_user, login_user

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