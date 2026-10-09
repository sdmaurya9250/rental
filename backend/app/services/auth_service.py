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



# import secrets
# from datetime import datetime, timedelta
# from fastapi import HTTPException
# from models.user import (
#     RegisterRequest,
#     LoginRequest,
#     ForgotPasswordRequest,
#     ResetPasswordRequest,
# )
# from utils.security import hash_password, verify_password, create_access_token
#
#
# async def register_user(data: RegisterRequest, db):
#     existing = await db.prepare(
#         "SELECT id FROM users WHERE email = ?"
#     ).bind(data.email).first()
#     if existing:
#         raise HTTPException(status_code=400, detail="Email already registered")
#
#     existing_mobile = await db.prepare(
#         "SELECT id FROM users WHERE mobile = ?"
#     ).bind(data.mobile).first()
#     if existing_mobile:
#         raise HTTPException(status_code=400, detail="Mobile number already registered")
#
#     user_id = secrets.token_hex(8)
#
#     await db.prepare(
#         """
#         INSERT INTO users (
#             id, email, mobile, password, country, city, pincode,
#             gender, want_to, lat, lng
#         )
#         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """
#     ).bind(
#         user_id,
#         data.email,
#         data.mobile,
#         hash_password(data.password),
#         data.country,
#         data.city,
#         data.pincode,
#         data.gender,
#         data.want_to,
#         data.lat,
#         data.lng,
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
#         "lat": data.lat,
#         "lng": data.lng,
#         "message": "Registration successful",
#     }
#
#
# async def login_user(data: LoginRequest, db):
#     user = await db.prepare(
#         "SELECT * FROM users WHERE email = ?"
#     ).bind(data.email).first()
#
#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid email or password")
#
#     user_dict = dict(user)
#
#     if not verify_password(data.password, user_dict["password"]):
#         raise HTTPException(status_code=401, detail="Invalid email or password")
#
#     access_token = create_access_token(
#         data={"sub": user_dict["id"], "email": user_dict["email"]}
#     )
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
#             "lat": user_dict.get("lat"),
#             "lng": user_dict.get("lng"),
#         },
#     }
#
#
# async def forgot_password(data: ForgotPasswordRequest, db):
#     email = data.email.strip().lower()
#
#     user = await db.prepare(
#         "SELECT id, email FROM users WHERE email = ?"
#     ).bind(email).first()
#
#     generic = {
#         "message": "If this email is registered, a reset link has been generated.",
#     }
#
#     if not user:
#         return generic
#
#     user_dict = dict(user)
#     token = secrets.token_urlsafe(32)
#     reset_id = secrets.token_hex(8)
#     expires_at = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
#
#     # Invalidate old unused tokens
#     await db.prepare(
#         "UPDATE password_resets SET used = 1 WHERE user_id = ? AND used = 0"
#     ).bind(user_dict["id"]).run()
#
#     await db.prepare(
#         """
#         INSERT INTO password_resets (id, user_id, email, token, expires_at, used)
#         VALUES (?, ?, ?, ?, ?, 0)
#         """
#     ).bind(
#         reset_id,
#         user_dict["id"],
#         email,
#         token,
#         expires_at,
#     ).run()
#
#     # Testing only — remove token from response in production
#     return {
#         **generic,
#         "token": token,
#         "expires_at": expires_at,
#     }
#
#
# async def reset_password(data: ResetPasswordRequest, db):
#     token = data.token.strip()
#     new_password = data.new_password
#
#     row = await db.prepare(
#         """
#         SELECT * FROM password_resets
#         WHERE token = ? AND used = 0
#         """
#     ).bind(token).first()
#
#     if not row:
#         raise HTTPException(status_code=400, detail="Invalid or expired reset token")
#
#     reset = dict(row)
#
#     try:
#         expires = datetime.fromisoformat(reset["expires_at"])
#     except Exception:
#         raise HTTPException(status_code=400, detail="Invalid or expired reset token")
#
#     if datetime.utcnow() > expires:
#         await db.prepare(
#             "UPDATE password_resets SET used = 1 WHERE id = ?"
#         ).bind(reset["id"]).run()
#         raise HTTPException(status_code=400, detail="Reset token has expired")
#
#     hashed = hash_password(new_password)
#     await db.prepare(
#         "UPDATE users SET password = ? WHERE id = ?"
#     ).bind(hashed, reset["user_id"]).run()
#
#     await db.prepare(
#         "UPDATE password_resets SET used = 1 WHERE id = ?"
#     ).bind(reset["id"]).run()
#
#     return {"message": "Password updated successfully"}



import secrets
import re
import string
from datetime import datetime, timedelta
from fastapi import HTTPException
from models.user import (
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from utils.security import hash_password, verify_password, create_access_token


def generate_user_id(name: str, length: int = 6) -> str:
    """
    ID = name initials + random letters/digits (no underscore).
    Example: "Pavan Kumar" → PK7A2X9B
    """
    cleaned = re.sub(r"[^a-zA-Z\s]", "", name or "").strip()
    parts = [p for p in cleaned.split() if p]

    if not parts:
        prefix = "US"
    elif len(parts) == 1:
        w = parts[0].upper()
        prefix = (w[:2] if len(w) >= 2 else (w + "X")[:2])
    else:
        prefix = "".join(p[0].upper() for p in parts[:4])

    alphabet = string.ascii_uppercase + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}{suffix}"


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

    # Name for ID + optional full_name
    display_name = (
        getattr(data, "name", None)
        or getattr(data, "fullName", None)
        or (data.email or "user").split("@")[0]
    )
    display_name = str(display_name).strip()

    user_id = None
    for _ in range(8):
        candidate = generate_user_id(display_name, length=6)
        taken = await db.prepare(
            "SELECT id FROM users WHERE id = ?"
        ).bind(candidate).first()
        if not taken:
            user_id = candidate
            break
    if not user_id:
        user_id = generate_user_id(display_name, length=10)

    await db.prepare(
        """
        INSERT INTO users (
            id, email, mobile, password, country, city, pincode,
            gender, want_to, lat, lng, full_name
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        display_name,
    ).run()

    return {
        "id": user_id,
        "account_id": user_id,
        "email": data.email,
        "mobile": data.mobile,
        "country": data.country,
        "city": data.city,
        "gender": data.gender,
        "want_to": data.want_to,
        "role": data.want_to,
        "name": display_name,
        "fullName": display_name,
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
        "token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_dict["id"],
            "account_id": user_dict["id"],
            "email": user_dict["email"],
            "mobile": user_dict["mobile"],
            "phone": user_dict.get("mobile"),
            "country": user_dict.get("country"),
            "city": user_dict.get("city"),
            "gender": user_dict.get("gender"),
            "want_to": user_dict.get("want_to"),
            "role": user_dict.get("want_to"),
            "name": user_dict.get("full_name") or "",
            "fullName": user_dict.get("full_name") or "",
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