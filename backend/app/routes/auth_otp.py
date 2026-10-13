from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
import secrets, hashlib, hmac, json, re
from datetime import datetime, timedelta
from utils.security import create_access_token  # your existing helper

router = APIRouter()

OTP_TTL_SEC = 300
OTP_MAX_ATTEMPTS = 5


class OtpSendRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=16)
    purpose: Literal["login", "signup"] = "login"


class OtpVerifyRequest(BaseModel):
    mobile: str
    otp: str = Field(..., min_length=4, max_length=8)
    purpose: Literal["login", "signup"] = "login"
    # signup fields
    fullName: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    country: Optional[str] = "India"
    city: Optional[str] = None
    pincode: Optional[str] = None
    gender: Optional[str] = None
    want_to: Optional[Literal["finder", "companion"]] = "finder"
    lat: Optional[float] = None
    lng: Optional[float] = None


def _normalize_mobile(raw: str) -> str:
    s = re.sub(r"[^\d+]", "", (raw or "").strip())
    if s.startswith("00"):
        s = "+" + s[2:]
    if not s.startswith("+"):
        # default India if 10 digits
        digits = re.sub(r"\D", "", s)
        if len(digits) == 10:
            s = "+91" + digits
        else:
            s = "+" + digits
    return s


def _hash_otp(code: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()


async def _send_whatsapp_otp(request: Request, mobile: str, code: str):
    env = request.scope["env"]
    token = (getattr(env, "WHATSAPP_TOKEN", None) or "").strip()
    phone_id = (getattr(env, "WHATSAPP_PHONE_NUMBER_ID", None) or "").strip()
    template = (getattr(env, "WHATSAPP_OTP_TEMPLATE", None) or "").strip()

    if not token or not phone_id:
        raise HTTPException(500, detail="WhatsApp not configured")

    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Prefer AUTHENTICATION template in production
    if template:
        body = {
            "messaging_product": "whatsapp",
            "to": mobile.lstrip("+") if False else mobile.replace("+", ""),  # Meta wants country code without + often
            "type": "template",
            "template": {
                "name": template,
                "language": {"code": "en"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": code}],
                    },
                    {
                        "type": "button",
                        "sub_type": "url",
                        "index": "0",
                        "parameters": [{"type": "text", "text": code}],
                    },
                ],
            },
        }
        # If your template has only body {{1}}, drop the button component
        body["template"]["components"] = [
            {"type": "body", "parameters": [{"type": "text", "text": code}]}
        ]
        body["to"] = re.sub(r"\D", "", mobile)  # 9198... no plus
    else:
        # Dev only — may fail outside 24h window / without template
        body = {
            "messaging_product": "whatsapp",
            "to": re.sub(r"\D", "", mobile),
            "type": "text",
            "text": {"body": f"Your verification code is {code}. Valid for 5 minutes."},
        }

    # Use same Workers fetch helper as Cashfree (not urllib)
    from routes.payments import _http_json  # or shared http util
    code_http, data = await _http_json("POST", url, headers, body)
    if code_http >= 400:
        raise HTTPException(
            502,
            detail=data.get("error", {}).get("message") if isinstance(data, dict) else "WhatsApp send failed",
        )
    return data


@router.post("/auth/otp/send")
async def otp_send(data: OtpSendRequest, request: Request):
    db = request.scope["env"].DB
    mobile = _normalize_mobile(data.mobile)
    purpose = data.purpose

    user = await db.prepare(
        "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
    ).bind(mobile, mobile.lstrip("+")).first()

    if purpose == "login" and not user:
        raise HTTPException(404, detail="No account with this mobile. Please sign up.")
    if purpose == "signup" and user:
        raise HTTPException(409, detail="Mobile already registered. Please login.")

    code = f"{secrets.randbelow(10**6):06d}"
    salt = secrets.token_hex(8)
    code_hash = _hash_otp(code, salt)
    expires = (datetime.utcnow() + timedelta(seconds=OTP_TTL_SEC)).isoformat()
    otp_id = secrets.token_hex(8)

    # Invalidate old OTPs for this mobile+purpose
    await db.prepare(
        "UPDATE otp_codes SET consumed = 1 WHERE mobile = ? AND purpose = ? AND consumed = 0"
    ).bind(mobile, purpose).run()

    await db.prepare(
        """
        INSERT INTO otp_codes (id, mobile, purpose, code_hash, expires_at, attempts, consumed)
        VALUES (?, ?, ?, ?, ?, 0, 0)
        """
    ).bind(otp_id, mobile, purpose, f"{salt}:{code_hash}", expires).run()

    await _send_whatsapp_otp(request, mobile, code)

    return {
        "message": "OTP sent on WhatsApp",
        "mobile": mobile,
        "purpose": purpose,
        "expires_in": OTP_TTL_SEC,
    }


@router.post("/auth/otp/verify")
async def otp_verify(data: OtpVerifyRequest, request: Request):
    db = request.scope["env"].DB
    mobile = _normalize_mobile(data.mobile)
    purpose = data.purpose
    otp = (data.otp or "").strip()

    row = await db.prepare(
        """
        SELECT * FROM otp_codes
        WHERE mobile = ? AND purpose = ? AND consumed = 0
        ORDER BY created_at DESC LIMIT 1
        """
    ).bind(mobile, purpose).first()
    if not row:
        raise HTTPException(400, detail="OTP expired or not found. Request a new one.")

    r = dict(row)
    if r.get("attempts", 0) >= OTP_MAX_ATTEMPTS:
        raise HTTPException(429, detail="Too many attempts. Request a new OTP.")

    exp = datetime.fromisoformat(str(r["expires_at"]).replace("Z", ""))
    if datetime.utcnow() > exp:
        raise HTTPException(400, detail="OTP expired. Request a new one.")

    salt, stored_hash = str(r["code_hash"]).split(":", 1)
    if not hmac.compare_digest(_hash_otp(otp, salt), stored_hash):
        await db.prepare(
            "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ?"
        ).bind(r["id"]).run()
        raise HTTPException(400, detail="Invalid OTP")

    await db.prepare(
        "UPDATE otp_codes SET consumed = 1 WHERE id = ?"
    ).bind(r["id"]).run()

    if purpose == "login":
        user = await db.prepare(
            "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
        ).bind(mobile, mobile.lstrip("+")).first()
        if not user:
            raise HTTPException(404, detail="User not found")
        u = dict(user)
    else:
        # signup
        existing = await db.prepare(
            "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
        ).bind(mobile, mobile.lstrip("+")).first()
        if existing:
            raise HTTPException(409, detail="Mobile already registered")

        full_name = (data.fullName or data.name or "User").strip()
        user_id = secrets.token_hex(4).upper()  # match your id style if needed
        email = (data.email or f"{re.sub(r'\\D', '', mobile)}@otp.local").strip()
        want_to = data.want_to or "finder"

        await db.prepare(
            """
            INSERT INTO users (
                id, full_name, email, mobile, country, city, pincode,
                gender, want_to, password_hash, lat, lng
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        ).bind(
            user_id,
            full_name,
            email,
            mobile,
            data.country or "India",
            data.city or "",
            data.pincode or "",
            data.gender or "",
            want_to,
            secrets.token_hex(16),  # no password login required
            data.lat,
            data.lng,
        ).run()
        user = await db.prepare("SELECT * FROM users WHERE id = ?").bind(user_id).first()
        u = dict(user)

    token = create_access_token({"sub": u["id"]})
    return {
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "user": {
            "id": u["id"],
            "account_id": u["id"],
            "fullName": u.get("full_name"),
            "name": u.get("full_name"),
            "email": u.get("email"),
            "mobile": u.get("mobile"),
            "want_to": u.get("want_to"),
            "role": u.get("want_to"),
            "city": u.get("city"),
        },
    }