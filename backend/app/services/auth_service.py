

import secrets
import re
from datetime import datetime, timedelta
from fastapi import HTTPException
from models.user import LoginRequest
from utils.security import hash_password, verify_password, create_access_token

def _normalize_mobile(raw: str | None) -> str | None:
    if not raw:
        return None
    s = re.sub(r"[^\d+]", "", str(raw).strip())
    if s.startswith("00"):
        s = "+" + s[2:]
    if not s.startswith("+"):
        digits = re.sub(r"\D", "", s)
        if len(digits) == 10:
            s = "+91" + digits
        elif digits:
            s = "+" + digits
        else:
            return None
    return s


async def login_user(data: LoginRequest, db):
    mobile_raw = (data.mobile or "").strip() or None

    if not mobile_raw:
        raise HTTPException(status_code=400, detail="Mobile number is required")

    user = None

    if mobile_raw:
        mobile = _normalize_mobile(mobile_raw)
        digits = re.sub(r"\D", "", mobile_raw)
        user = await db.prepare(
            """
            SELECT * FROM users
            WHERE mobile = ?
               OR mobile = ?
               OR mobile = ?
               OR mobile = ?
            LIMIT 1
            """
        ).bind(
            mobile or "",
            (mobile or "").lstrip("+"),
            digits[-10:] if len(digits) >= 10 else digits,
            mobile_raw,
        ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid mobile number or password")

    user_dict = dict(user)
    stored = user_dict.get("password") or user_dict.get("password_hash") or ""

    if not stored or not verify_password(data.password, stored):
        raise HTTPException(status_code=401, detail="Invalid mobile number or password")

    access_token = create_access_token(
        data={"sub": user_dict["id"]}
    )

    return {
        "access_token": access_token,
        "token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_dict["id"],
            "mobile": user_dict.get("mobile"),
            "country": user_dict.get("country"),
            "city": user_dict.get("city"),
            "gender": user_dict.get("gender"),
            "want_to": user_dict.get("want_to"),
            "fullName": user_dict.get("full_name"),
            "name": user_dict.get("full_name"),
            "lat": user_dict.get("lat"),
            "lng": user_dict.get("lng"),
        },
    }

