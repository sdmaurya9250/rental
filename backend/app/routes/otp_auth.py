from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
import secrets
import hashlib
import hmac
import re
from datetime import datetime, timedelta
from utils.security import create_access_token

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
        digits = re.sub(r"\D", "", s)
        if len(digits) == 10:
            s = "+91" + digits
        else:
            s = "+" + digits
    return s


def _hash_otp(code: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()


def _digits_only(mobile: str) -> str:
    """Meta 'to' field: digits only, no +."""
    return re.sub(r"\D", "", mobile or "")


async def _http_json(
    method: str,
    url: str,
    headers: dict,
    body: dict | None = None,
) -> tuple[int, dict]:
    """Workers fetch first; urllib fallback for local."""
    import json as _json

    payload = _json.dumps(body) if body is not None else None

    try:
        from js import fetch, Object
        from pyodide.ffi import to_js

        opts = {"method": method, "headers": headers}
        if payload is not None:
            opts["body"] = payload
        resp = await fetch(url, to_js(opts, dict_converter=Object.fromEntries))
        text = await resp.text()
        code = int(resp.status)
        try:
            data = _json.loads(text) if text else {}
        except Exception:
            data = {"message": text}
        return code, data
    except Exception:
        pass

    import urllib.request
    import urllib.error

    data_bytes = payload.encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, (_json.loads(text) if text else {})
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8")
        try:
            data = _json.loads(text) if text else {}
        except Exception:
            data = {"message": text}
        return int(e.code), data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"WhatsApp request failed: {e}")


async def _send_whatsapp_otp(request: Request, mobile: str, code: str):
    """
    Template from WHATSAPP_OTP_TEMPLATE.
    - hello_world: en_US, no components (does NOT include OTP digits)
    - real OTP template: body {{1}} = code
    """
    env = request.scope["env"]
    token = (getattr(env, "WHATSAPP_TOKEN", None) or "").strip()
    phone_id = (getattr(env, "WHATSAPP_PHONE_NUMBER_ID", None) or "").strip()
    template = (getattr(env, "WHATSAPP_OTP_TEMPLATE", None) or "hello_world").strip()
    lang = (getattr(env, "WHATSAPP_OTP_LANG", None) or "en_US").strip()

    if not token or not phone_id:
        raise HTTPException(status_code=500, detail="WhatsApp not configured")

    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    to = _digits_only(mobile)

    if template.lower() in ("hello_world", "hello world"):
        body = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": "hello_world",
                "language": {"code": "en_US"},
            },
        }
    elif template:
        body = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template,
                "language": {"code": lang},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": code}],
                    }
                ],
            },
        }
    else:
        body = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": f"Your verification code is {code}. Valid for 5 minutes.",
            },
        }

    code_http, data = await _http_json("POST", url, headers, body)
    if code_http >= 400:
        err = {}
        if isinstance(data, dict):
            err = data.get("error") or data
        msg = err.get("message") if isinstance(err, dict) else str(data)
        raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
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
        raise HTTPException(
            status_code=404,
            detail="No account with this mobile. Please sign up.",
        )
    if purpose == "signup" and user:
        raise HTTPException(
            status_code=409,
            detail="Mobile already registered. Please login.",
        )

    code = f"{secrets.randbelow(10**6):06d}"
    salt = secrets.token_hex(8)
    code_hash = _hash_otp(code, salt)
    expires = (datetime.utcnow() + timedelta(seconds=OTP_TTL_SEC)).isoformat()
    otp_id = secrets.token_hex(8)

    await db.prepare(
        """
        UPDATE otp_codes SET consumed = 1
        WHERE mobile = ? AND purpose = ? AND consumed = 0
        """
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
        raise HTTPException(
            status_code=400,
            detail="OTP expired or not found. Request a new one.",
        )

    r = dict(row)
    if int(r.get("attempts") or 0) >= OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Request a new OTP.",
        )

    exp = datetime.fromisoformat(str(r["expires_at"]).replace("Z", ""))
    if datetime.utcnow() > exp:
        raise HTTPException(
            status_code=400,
            detail="OTP expired. Request a new one.",
        )

    salt, stored_hash = str(r["code_hash"]).split(":", 1)
    if not hmac.compare_digest(_hash_otp(otp, salt), stored_hash):
        await db.prepare(
            "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ?"
        ).bind(r["id"]).run()
        raise HTTPException(status_code=400, detail="Invalid OTP")

    await db.prepare(
        "UPDATE otp_codes SET consumed = 1 WHERE id = ?"
    ).bind(r["id"]).run()

    if purpose == "login":
        user = await db.prepare(
            "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
        ).bind(mobile, mobile.lstrip("+")).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        u = dict(user)
    else:
        existing = await db.prepare(
            "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
        ).bind(mobile, mobile.lstrip("+")).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail="Mobile already registered",
            )

        full_name = (data.fullName or data.name or "User").strip()
        user_id = secrets.token_hex(4).upper()
        digits = _digits_only(mobile)
        email = (data.email or f"{digits}@otp.local").strip()
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
            secrets.token_hex(16),
            data.lat,
            data.lng,
        ).run()

        user = await db.prepare(
            "SELECT * FROM users WHERE id = ?"
        ).bind(user_id).first()
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