# from fastapi import APIRouter, Request, HTTPException
# from pydantic import BaseModel, Field
# from typing import Optional, Literal
# import secrets
# import hashlib
# import hmac
# import re
# from datetime import datetime, timedelta
# from utils.security import create_access_token, hash_password
#
# router = APIRouter()
#
# OTP_TTL_SEC = 300
# OTP_MAX_ATTEMPTS = 5
#
# NO_PARAM_TEMPLATES = {"hello_world", "hello world"}
# AUTH_OTP_TEMPLATES = {
#     "login_otp",
#     "verify_code",
#     "verify_code_1",
#     "authentication_code",
#     "otp_verification",
# }
#
#
# class OtpSendRequest(BaseModel):
#     mobile: str = Field(..., min_length=10, max_length=16)
#     purpose: Literal["login", "signup"] = "login"
#
#
# class OtpVerifyRequest(BaseModel):
#     mobile: str
#     otp: str = Field(..., min_length=4, max_length=8)
#     purpose: Literal["login", "signup"] = "login"
#     password: Optional[str] = Field(None, min_length=6, max_length=128)
#     fullName: Optional[str] = None
#     name: Optional[str] = None
# #     country: Optional[str] = "India"
#     city: Optional[str] = None
#     pincode: Optional[str] = None
#     gender: Optional[str] = None
#     want_to: Optional[Literal["finder", "companion"]] = "finder"
#     lat: Optional[float] = None
#     lng: Optional[float] = None
#
#
# def _normalize_mobile(raw: str) -> str:
#     s = re.sub(r"[^\d+]", "", (raw or "").strip())
#     if s.startswith("00"):
#         s = "+" + s[2:]
#     if not s.startswith("+"):
#         digits = re.sub(r"\D", "", s)
#         if len(digits) == 10:
#             s = "+91" + digits
#         else:
#             s = "+" + digits
#     return s
#
#
# def _hash_otp(code: str, salt: str) -> str:
#     return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()
#
#
# def _digits_only(mobile: str) -> str:
#     return re.sub(r"\D", "", mobile or "")
#
#
# async def _http_json(method: str, url: str, headers: dict, body: dict | None = None):
#     import json as _json
#
#     payload = _json.dumps(body) if body is not None else None
#     try:
#         from js import fetch, Object
#         from pyodide.ffi import to_js
#
#         opts = {"method": method, "headers": headers}
#         if payload is not None:
#             opts["body"] = payload
#         resp = await fetch(url, to_js(opts, dict_converter=Object.fromEntries))
#         text = await resp.text()
#         code = int(resp.status)
#         try:
#             data = _json.loads(text) if text else {}
#         except Exception:
#             data = {"message": text}
#         return code, data
#     except Exception:
#         pass
#
#     import urllib.request
#     import urllib.error
#
#     data_bytes = payload.encode("utf-8") if payload else None
#     req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
#     try:
#         with urllib.request.urlopen(req, timeout=30) as resp:
#             text = resp.read().decode("utf-8")
#             return resp.status, (_json.loads(text) if text else {})
#     except urllib.error.HTTPError as e:
#         text = e.read().decode("utf-8")
#         try:
#             data = _json.loads(text) if text else {}
#         except Exception:
#             data = {"message": text}
#         return int(e.code), data
#     except Exception as e:
#         raise HTTPException(status_code=502, detail=f"WhatsApp request failed: {e}")
#
#
# def _build_auth_otp_template(name: str, lang: str, code: str) -> dict:
#     return {
#         "name": name,
#         "language": {"code": lang},
#         "components": [
#             {
#                 "type": "body",
#                 "parameters": [{"type": "text", "text": str(code)}],
#             },
#             {
#                 "type": "button",
#                 "sub_type": "url",
#                 "index": "0",
#                 "parameters": [{"type": "text", "text": str(code)}],
#             },
#         ],
#     }
#
#
# async def _send_whatsapp_otp(request: Request, mobile: str, code: str):
#     env = request.scope["env"]
#     token = (getattr(env, "WHATSAPP_TOKEN", None) or "").strip()
#     phone_id = (getattr(env, "WHATSAPP_PHONE_NUMBER_ID", None) or "").strip()
#     template = (getattr(env, "WHATSAPP_OTP_TEMPLATE", None) or "login_otp").strip()
#     lang = (getattr(env, "WHATSAPP_OTP_LANG", None) or "en").strip()
#
#     if not token or not phone_id:
#         raise HTTPException(status_code=500, detail="WhatsApp not configured")
#
#     url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json",
#     }
#     to = _digits_only(mobile)
#     t_lower = template.lower().replace("-", "_")
#
#     if t_lower in NO_PARAM_TEMPLATES:
#         template_obj = {
#             "name": "hello_world",
#             "language": {"code": "en_US"},
#         }
#     elif t_lower in AUTH_OTP_TEMPLATES or "otp" in t_lower:
#         template_obj = _build_auth_otp_template(template, lang, code)
#     elif template:
#         template_obj = {
#             "name": template,
#             "language": {"code": lang},
#             "components": [
#                 {
#                     "type": "body",
#                     "parameters": [{"type": "text", "text": str(code)}],
#                 }
#             ],
#         }
#     else:
#         body = {
#             "messaging_product": "whatsapp",
#             "to": to,
#             "type": "text",
#             "text": {
#                 "body": f"Your verification code is {code}. Valid for 5 minutes.",
#             },
#         }
#         code_http, data = await _http_json("POST", url, headers, body)
#         if code_http >= 400:
#             err = (data.get("error") if isinstance(data, dict) else None) or data
#             msg = err.get("message") if isinstance(err, dict) else str(data)
#             raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
#         return data
#
#     body = {
#         "messaging_product": "whatsapp",
#         "recipient_type": "individual",
#         "to": to,
#         "type": "template",
#         "template": template_obj,
#     }
#
#     code_http, data = await _http_json("POST", url, headers, body)
#     if (
#         code_http >= 400
#         and template_obj.get("components")
#         and len(template_obj["components"]) > 1
#     ):
#         template_obj = {
#             "name": template_obj["name"],
#             "language": template_obj["language"],
#             "components": [
#                 {
#                     "type": "body",
#                     "parameters": [{"type": "text", "text": str(code)}],
#                 }
#             ],
#         }
#         body["template"] = template_obj
#         code_http, data = await _http_json("POST", url, headers, body)
#
#     if code_http >= 400:
#         err = (data.get("error") if isinstance(data, dict) else None) or data
#         msg = err.get("message") if isinstance(err, dict) else str(data)
#         raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
#     return data
#
#
# @router.post("/auth/otp/send")
# async def otp_send(data: OtpSendRequest, request: Request):
#     db = request.scope["env"].DB
#     mobile = _normalize_mobile(data.mobile)
#     purpose = data.purpose
#
#     user = await db.prepare(
#         "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
#     ).bind(mobile, mobile.lstrip("+")).first()
#
#     # Also match 10-digit storage from old register
#     if not user:
#         digits = _digits_only(mobile)
#         last10 = digits[-10:] if len(digits) >= 10 else digits
#         user = await db.prepare(
#             "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
#         ).bind(last10, digits).first()
#
#     if purpose == "login" and not user:
#         raise HTTPException(
#             status_code=404,
#             detail="No account with this mobile. Please sign up.",
#         )
#     if purpose == "signup" and user:
#         raise HTTPException(
#             status_code=409,
#             detail="Mobile already registered. Please login.",
#         )
#
#     code = f"{secrets.randbelow(10**6):06d}"
#     salt = secrets.token_hex(8)
#     code_hash = _hash_otp(code, salt)
#     expires = (datetime.utcnow() + timedelta(seconds=OTP_TTL_SEC)).isoformat()
#     otp_id = secrets.token_hex(8)
#
#     await db.prepare(
#         """
#         UPDATE otp_codes SET consumed = 1
#         WHERE mobile = ? AND purpose = ? AND consumed = 0
#         """
#     ).bind(mobile, purpose).run()
#
#     await db.prepare(
#         """
#         INSERT INTO otp_codes (id, mobile, purpose, code_hash, expires_at, attempts, consumed)
#         VALUES (?, ?, ?, ?, ?, 0, 0)
#         """
#     ).bind(otp_id, mobile, purpose, f"{salt}:{code_hash}", expires).run()
#
#     await _send_whatsapp_otp(request, mobile, code)
#
#     return {
#         "message": "OTP sent on WhatsApp",
#         "mobile": mobile,
#         "purpose": purpose,
#         "expires_in": OTP_TTL_SEC,
#     }
#
#
# @router.post("/auth/otp/verify")
# async def otp_verify(data: OtpVerifyRequest, request: Request):
#     db = request.scope["env"].DB
#     mobile = _normalize_mobile(data.mobile)
#     purpose = data.purpose
#     otp = (data.otp or "").strip()
#
#     row = await db.prepare(
#         """
#         SELECT * FROM otp_codes
#         WHERE mobile = ? AND purpose = ? AND consumed = 0
#         ORDER BY created_at DESC LIMIT 1
#         """
#     ).bind(mobile, purpose).first()
#     if not row:
#         raise HTTPException(
#             status_code=400,
#             detail="OTP expired or not found. Request a new one.",
#         )
#
#     r = dict(row)
#     if int(r.get("attempts") or 0) >= OTP_MAX_ATTEMPTS:
#         raise HTTPException(
#             status_code=429,
#             detail="Too many attempts. Request a new OTP.",
#         )
#
#     exp = datetime.fromisoformat(str(r["expires_at"]).replace("Z", ""))
#     if datetime.utcnow() > exp:
#         raise HTTPException(
#             status_code=400,
#             detail="OTP expired. Request a new one.",
#         )
#
#     salt, stored_hash = str(r["code_hash"]).split(":", 1)
#     if not hmac.compare_digest(_hash_otp(otp, salt), stored_hash):
#         await db.prepare(
#             "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ?"
#         ).bind(r["id"]).run()
#         raise HTTPException(status_code=400, detail="Invalid OTP")
#
#     # Mark consumed only after OTP is valid
#     await db.prepare(
#         "UPDATE otp_codes SET consumed = 1 WHERE id = ?"
#     ).bind(r["id"]).run()
#
#     if purpose == "login":
#         user = await db.prepare(
#             "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
#         ).bind(mobile, mobile.lstrip("+")).first()
#         if not user:
#             digits = _digits_only(mobile)
#             last10 = digits[-10:] if len(digits) >= 10 else digits
#             user = await db.prepare(
#                 "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
#             ).bind(last10, digits).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
#         u = dict(user)
#     else:
#         # --- SIGNUP: create user (same columns as register_user) ---
#         existing = await db.prepare(
#             "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
#         ).bind(mobile, mobile.lstrip("+")).first()
#         if not existing:
#             digits = _digits_only(mobile)
#             last10 = digits[-10:] if len(digits) >= 10 else digits
#             existing = await db.prepare(
#                 "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
#             ).bind(last10, digits).first()
#         if existing:
#             raise HTTPException(status_code=409, detail="Mobile already registered")
#
#         plain = (data.password or "").strip()
#         if len(plain) < 6:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Password required (min 6 characters) for signup",
#             )
#
#         full_name = (data.fullName or data.name or "User").strip()
#         user_id = secrets.token_hex(8)
#         digits = _digits_only(mobile)
#         email = f"{digits}@otp.local"  # internal placeholder, never shown
#         want_to = data.want_to or "finder"
#         password_hashed = hash_password(plain)
#
#         # Avoid unique email clash
#         email_taken = await db.prepare(
#             "SELECT id FROM users WHERE email = ?"
#         ).bind(email).first()
#         if email_taken:
#             email = f"{digits}.{user_id[:8].lower()}@otp.local"
#
#         country = (data.country or "India").strip() or "India"
#         city = (data.city or "").strip()
#         pincode = (data.pincode or "000000").strip() or "000000"
#         if len(pincode) > 6:
#             pincode = pincode[:6]
#         gender = (data.gender or "Other").strip() or "Other"
#         if gender not in ("Male", "Female", "Other"):
#             gender = "Other"
#         if want_to not in ("finder", "companion"):
#             want_to = "finder"
#
#         try:
#             # Same shape as services/auth_service.register_user
#             await db.prepare(
#                 """
#                 INSERT INTO users (
#                     id, email, mobile, password, country, city, pincode,
#                     gender, want_to, lat, lng
#                 )
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                 """
#             ).bind(
#                 user_id,
#                 email,
#                 mobile,
#                 password_hashed,
#                 country,
#                 city,
#                 pincode,
#                 gender,
#                 want_to,
#                 data.lat,
#                 data.lng,
#             ).run()
#         except Exception as e:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"User create failed: {e}",
#             )
#
#         # Optional full_name if column exists
#         try:
#             await db.prepare(
#                 "UPDATE users SET full_name = ? WHERE id = ?"
#             ).bind(full_name, user_id).run()
#         except Exception:
#             pass
#
#         user = await db.prepare(
#             "SELECT * FROM users WHERE id = ?"
#         ).bind(user_id).first()
#         if not user:
#             raise HTTPException(
#                 status_code=500,
#                 detail="User create failed: row not found after insert",
#             )
#         u = dict(user)
#
#     token = create_access_token(
#         data={"sub": u["id"]}
#     )
#     return {
#         "access_token": token,
#         "token": token,
#         "token_type": "bearer",
#         "user": {
#             "id": u["id"],
#             "account_id": u["id"],
#             "fullName": u.get("full_name") or full_name if purpose == "signup" else u.get("full_name"),
#             "name": u.get("full_name") or (full_name if purpose == "signup" else None),
#             "email": u.get("email"),
#             "mobile": u.get("mobile"),
#             "want_to": u.get("want_to"),
#             "role": u.get("want_to"),
#             "city": u.get("city"),
#             "country": u.get("country"),
#         },
#     }


from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
import secrets
import hashlib
import hmac
import re
from datetime import datetime, timedelta
from utils.security import create_access_token, hash_password

router = APIRouter()

OTP_TTL_SEC = 300
OTP_MAX_ATTEMPTS = 5

NO_PARAM_TEMPLATES = {"hello_world", "hello world"}
AUTH_OTP_TEMPLATES = {
    "login_otp",
    "verify_code",
    "verify_code_1",
    "authentication_code",
    "otp_verification",
}


class OtpSendRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=16)
    purpose: Literal["login", "signup", "reset"] = "login"


class OtpVerifyRequest(BaseModel):
    mobile: str
    otp: str = Field(..., min_length=4, max_length=8)
    purpose: Literal["login", "signup", "reset"] = "login"
    # signup + reset
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    # signup profile (optional)
    fullName: Optional[str] = None
    name: Optional[str] = None
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
    return re.sub(r"\D", "", mobile or "")


async def _find_user_by_mobile(db, mobile: str):
    """Match +91..., without +, 10-digit, or raw."""
    user = await db.prepare(
        "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
    ).bind(mobile, mobile.lstrip("+")).first()
    if user:
        return dict(user)

    digits = _digits_only(mobile)
    last10 = digits[-10:] if len(digits) >= 10 else digits
    user = await db.prepare(
        "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
    ).bind(last10, digits).first()
    return dict(user) if user else None


async def _http_json(method: str, url: str, headers: dict, body: dict | None = None):
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


def _build_auth_otp_template(name: str, lang: str, code: str) -> dict:
    return {
        "name": name,
        "language": {"code": lang},
        "components": [
            {
                "type": "body",
                "parameters": [{"type": "text", "text": str(code)}],
            },
            {
                "type": "button",
                "sub_type": "url",
                "index": "0",
                "parameters": [{"type": "text", "text": str(code)}],
            },
        ],
    }


async def _send_whatsapp_otp(request: Request, mobile: str, code: str):
    env = request.scope["env"]
    token = (getattr(env, "WHATSAPP_TOKEN", None) or "").strip()
    phone_id = (getattr(env, "WHATSAPP_PHONE_NUMBER_ID", None) or "").strip()
    template = (getattr(env, "WHATSAPP_OTP_TEMPLATE", None) or "login_otp").strip()
    lang = (getattr(env, "WHATSAPP_OTP_LANG", None) or "en").strip()

    if not token or not phone_id:
        raise HTTPException(status_code=500, detail="WhatsApp not configured")

    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    to = _digits_only(mobile)
    t_lower = template.lower().replace("-", "_")

    if t_lower in NO_PARAM_TEMPLATES:
        template_obj = {
            "name": "hello_world",
            "language": {"code": "en_US"},
        }
    elif t_lower in AUTH_OTP_TEMPLATES or "otp" in t_lower:
        template_obj = _build_auth_otp_template(template, lang, code)
    elif template:
        template_obj = {
            "name": template,
            "language": {"code": lang},
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(code)}],
                }
            ],
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
            err = (data.get("error") if isinstance(data, dict) else None) or data
            msg = err.get("message") if isinstance(err, dict) else str(data)
            raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
        return data

    body = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "template",
        "template": template_obj,
    }

    code_http, data = await _http_json("POST", url, headers, body)
    if (
        code_http >= 400
        and template_obj.get("components")
        and len(template_obj["components"]) > 1
    ):
        template_obj = {
            "name": template_obj["name"],
            "language": template_obj["language"],
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(code)}],
                }
            ],
        }
        body["template"] = template_obj
        code_http, data = await _http_json("POST", url, headers, body)

    if code_http >= 400:
        err = (data.get("error") if isinstance(data, dict) else None) or data
        msg = err.get("message") if isinstance(err, dict) else str(data)
        raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
    return data


def _user_payload(u: dict) -> dict:
    name = u.get("full_name") or ""
    return {
        "id": u["id"],
        "account_id": u["id"],
        "fullName": name,
        "name": name,
        "mobile": u.get("mobile"),
        "want_to": u.get("want_to"),
        "role": u.get("want_to"),
        "city": u.get("city"),
        "country": u.get("country"),
    }


@router.post("/auth/otp/send")
async def otp_send(data: OtpSendRequest, request: Request):
    db = request.scope["env"].DB
    mobile = _normalize_mobile(data.mobile)
    purpose = data.purpose

    user = await _find_user_by_mobile(db, mobile)

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
    if purpose == "reset" and not user:
        raise HTTPException(
            status_code=404,
            detail="No account with this mobile.",
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

    # ---------- RESET PASSWORD (WhatsApp OTP only) ----------
    if purpose == "reset":
        plain = (data.password or "").strip()
        if len(plain) < 6:
            raise HTTPException(
                status_code=400,
                detail="New password required (min 6 characters)",
            )

        u = await _find_user_by_mobile(db, mobile)
        if not u:
            raise HTTPException(status_code=404, detail="User not found")

        password_hashed = hash_password(plain)
        await db.prepare(
            "UPDATE users SET password = ? WHERE id = ?"
        ).bind(password_hashed, u["id"]).run()

        token = create_access_token(
            data={"sub": u["id"]}
        )
        return {
            "message": "Password updated successfully",
            "access_token": token,
            "token": token,
            "token_type": "bearer",
            "user": _user_payload(u),
        }

    # ---------- OTP LOGIN (optional) ----------
    if purpose == "login":
        u = await _find_user_by_mobile(db, mobile)
        if not u:
            raise HTTPException(status_code=404, detail="User not found")

        token = create_access_token(
            data={"sub": u["id"]}
        )
        return {
            "access_token": token,
            "token": token,
            "token_type": "bearer",
            "user": _user_payload(u),
        }

    # ---------- SIGNUP ----------
    existing = await _find_user_by_mobile(db, mobile)
    if existing:
        raise HTTPException(status_code=409, detail="Mobile already registered")

    plain = (data.password or "").strip()
    if len(plain) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password required (min 6 characters) for signup",
        )

    full_name = (data.fullName or data.name or "User").strip()
    user_id = secrets.token_hex(8)
    digits = _digits_only(mobile)
    email = f"{digits}@otp.local"  # internal placeholder, never shown
    want_to = data.want_to or "finder"
    password_hashed = hash_password(plain)

    email_taken = await db.prepare(
        "SELECT id FROM users WHERE email = ?"
    ).bind(email).first()
    if email_taken:
        email = f"{digits}.{user_id[:8].lower()}@otp.local"

    country = (data.country or "India").strip() or "India"
    city = (data.city or "").strip()
    pincode = (data.pincode or "000000").strip() or "000000"
    if len(pincode) > 6:
        pincode = pincode[:6]
    gender = (data.gender or "Other").strip() or "Other"
    if gender not in ("Male", "Female", "Other"):
        gender = "Other"
    if want_to not in ("finder", "companion"):
        want_to = "finder"

    try:
        # Same columns as register_user (password, not password_hash)
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
            email,
            mobile,
            password_hashed,
            country,
            city,
            pincode,
            gender,
            want_to,
            data.lat,
            data.lng,
        ).run()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"User create failed: {e}",
        )

    try:
        await db.prepare(
            "UPDATE users SET full_name = ? WHERE id = ?"
        ).bind(full_name, user_id).run()
    except Exception:
        pass

    user = await db.prepare(
        "SELECT * FROM users WHERE id = ?"
    ).bind(user_id).first()
    if not user:
        raise HTTPException(
            status_code=500,
            detail="User create failed: row not found after insert",
        )
    u = dict(user)
    if not u.get("full_name"):
        u["full_name"] = full_name

    token = create_access_token(
        data={"sub": u["id"]}
    )
    return {
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "user": _user_payload(u),
    }