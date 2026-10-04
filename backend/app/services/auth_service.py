# import secrets
# import json
# from fastapi import HTTPException, status
# from models.user import RegisterRequest, LoginRequest
# from utils.security import hash_password, verify_password, create_access_token
#
#
# async def register_user(data: RegisterRequest, db):
#     existing = await db.prepare("SELECT id FROM users WHERE email = ?").bind(data.email).first()
#     if existing:
#         raise HTTPException(status_code=400, detail="Email already registered")
#
#     existing_mobile = await db.prepare("SELECT id FROM users WHERE mobile = ?").bind(data.mobile).first()
#     if existing_mobile:
#         raise HTTPException(status_code=400, detail="Mobile number already registered")
#
#     user_id = secrets.token_hex(8)
#
#     await db.prepare(
#         """
#         INSERT INTO users (id, email, mobile, password, country, city, pincode, gender, want_to)
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """
#     ).bind(
#         user_id, data.email, data.mobile, hash_password(data.password),
#         data.country, data.city, data.pincode, data.gender, data.want_to
#     ).run()
#
#     return {
#         "id": user_id,
#         "email": data.email,
#         "mobile": data.mobile,
#         "country": data.country,
#         "city": data.city,
#         "gender": data.gender,
#         "want_to": data.want_to,
#         "message": "Registration successful"
#     }
#
#
# async def login_user(data: LoginRequest, db):
#     user = await db.prepare("SELECT * FROM users WHERE email = ?").bind(data.email).first()
#
#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid email or password")
#
#     user_dict = dict(user)
#
#     if not verify_password(data.password, user_dict["password"]):
#         raise HTTPException(status_code=401, detail="Invalid email or password")
#
#     # Create JWT token
#     access_token = create_access_token(data={"sub": user_dict["id"], "email": user_dict["email"]})
#
#     return {
#         "access_token": access_token,
#         "token_type": "bearer",
#         "user": {
#             "id": user_dict["id"],
#             "email": user_dict["email"],
#             "mobile": user_dict["mobile"],
#             "country": user_dict.get("country"),
#             "city": user_dict.get("city"),
#             "gender": user_dict.get("gender"),
#             "want_to": user_dict.get("want_to"),
#         }
#     }



import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException
from models.user import (
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from utils.security import hash_password, verify_password, create_access_token


async def register_user(data: RegisterRequest, db):
    existing = await db.prepare(
        "SELECT id FROM users WHERE email = ?"
    ).bind(data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_mobile = await db.prepare(
        "SELECT id FROM users WHERE mobile = ?"
    ).bind(data.mobile).first()
    if existing_mobile:
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    user_id = secrets.token_hex(8)

    await db.prepare(
        """
        INSERT INTO users (
            id, email, mobile, password, country, city, pincode,
            gender, want_to, lat, lng
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    ).bind(
        user_id,
        data.email,
        data.mobile,
        hash_password(data.password),
        data.country,
        data.city,
        data.pincode,
        data.gender,
        data.want_to,
        data.lat,
        data.lng,
    ).run()

    return {
        "id": user_id,
        "email": data.email,
        "mobile": data.mobile,
        "country": data.country,
        "city": data.city,
        "gender": data.gender,
        "want_to": data.want_to,
        "lat": data.lat,
        "lng": data.lng,
        "message": "Registration successful",
    }


async def login_user(data: LoginRequest, db):
    user = await db.prepare(
        "SELECT * FROM users WHERE email = ?"
    ).bind(data.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_dict = dict(user)

    if not verify_password(data.password, user_dict["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = create_access_token(
        data={"sub": user_dict["id"], "email": user_dict["email"]}
    )

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
            "lat": user_dict.get("lat"),
            "lng": user_dict.get("lng"),
        },
    }


async def forgot_password(data: ForgotPasswordRequest, db):
    email = data.email.strip().lower()

    user = await db.prepare(
        "SELECT id, email FROM users WHERE email = ?"
    ).bind(email).first()

    generic = {
        "message": "If this email is registered, a reset link has been generated.",
    }

    if not user:
        return generic

    user_dict = dict(user)
    token = secrets.token_urlsafe(32)
    reset_id = secrets.token_hex(8)
    expires_at = (datetime.utcnow() + timedelta(minutes=30)).isoformat()

    # Invalidate old unused tokens
    await db.prepare(
        "UPDATE password_resets SET used = 1 WHERE user_id = ? AND used = 0"
    ).bind(user_dict["id"]).run()

    await db.prepare(
        """
        INSERT INTO password_resets (id, user_id, email, token, expires_at, used)
        VALUES (?, ?, ?, ?, ?, 0)
        """
    ).bind(
        reset_id,
        user_dict["id"],
        email,
        token,
        expires_at,
    ).run()

    # Testing only — remove token from response in production
    return {
        **generic,
        "token": token,
        "expires_at": expires_at,
    }


async def reset_password(data: ResetPasswordRequest, db):
    token = data.token.strip()
    new_password = data.new_password

    row = await db.prepare(
        """
        SELECT * FROM password_resets
        WHERE token = ? AND used = 0
        """
    ).bind(token).first()

    if not row:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    reset = dict(row)

    try:
        expires = datetime.fromisoformat(reset["expires_at"])
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    if datetime.utcnow() > expires:
        await db.prepare(
            "UPDATE password_resets SET used = 1 WHERE id = ?"
        ).bind(reset["id"]).run()
        raise HTTPException(status_code=400, detail="Reset token has expired")

    hashed = hash_password(new_password)
    await db.prepare(
        "UPDATE users SET password = ? WHERE id = ?"
    ).bind(hashed, reset["user_id"]).run()

    await db.prepare(
        "UPDATE password_resets SET used = 1 WHERE id = ?"
    ).bind(reset["id"]).run()

    return {"message": "Password updated successfully"}