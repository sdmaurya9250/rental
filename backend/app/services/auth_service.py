import secrets
from fastapi import HTTPException, status
from models.user import RegisterRequest, LoginRequest
from utils.security import hash_password, verify_password

users_db = {}


def register_user(data: RegisterRequest):
    if data.email in users_db:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    for user in users_db.values():
        if user["mobile"] == data.mobile:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mobile number already registered")

    user_id = secrets.token_hex(8)

    users_db[data.email] = {
        "id": user_id,
        "email": data.email,
        "mobile": data.mobile,
        "password": hash_password(data.password),
        "country": data.country,
        "city": data.city,
        "pincode": data.pincode,
        "gender": data.gender,
        "want_to": data.want_to,
    }

    return {
        "id": user_id,
        "email": data.email,
        "mobile": data.mobile,
        "country": data.country,
        "city": data.city,
        "gender": data.gender,
        "want_to": data.want_to,
        "message": "Registration successful"
    }


def login_user(data: LoginRequest):
    user = users_db.get(data.email)

    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    return {
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "mobile": user["mobile"],
            "country": user["country"],
            "city": user["city"],
            "gender": user["gender"],
            "want_to": user["want_to"],
        }
    }