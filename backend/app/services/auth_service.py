import secrets
import json
from fastapi import HTTPException, status
from models.user import RegisterRequest, LoginRequest
from utils.security import hash_password, verify_password, create_access_token


async def register_user(data: RegisterRequest, db):
    existing = await db.prepare("SELECT id FROM users WHERE email = ?").bind(data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_mobile = await db.prepare("SELECT id FROM users WHERE mobile = ?").bind(data.mobile).first()
    if existing_mobile:
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    user_id = secrets.token_hex(8)

    await db.prepare(
        """
        INSERT INTO users (id, email, mobile, password, country, city, pincode, gender, want_to)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    ).bind(
        user_id, data.email, data.mobile, hash_password(data.password),
        data.country, data.city, data.pincode, data.gender, data.want_to
    ).run()

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


async def login_user(data: LoginRequest, db):
    user = await db.prepare("SELECT * FROM users WHERE email = ?").bind(data.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_dict = dict(user)

    if not verify_password(data.password, user_dict["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create JWT token
    access_token = create_access_token(data={"sub": user_dict["id"], "email": user_dict["email"]})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_dict["id"],
            "email": user_dict["email"],
            "mobile": user_dict["mobile"],
            "country": user_dict.get("country"),
            "city": user_dict.get("city"),
            "gender": user_dict.get("gender"),
            "want_to": user_dict.get("want_to"),
        }
    }