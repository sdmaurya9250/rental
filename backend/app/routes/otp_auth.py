# # # # # # # # from fastapi import APIRouter, Request, HTTPException
# # # # # # # # from pydantic import BaseModel, Field
# # # # # # # # from typing import Optional, Literal
# # # # # # # # import secrets
# # # # # # # # import hashlib
# # # # # # # # import hmac
# # # # # # # # import re
# # # # # # # # from datetime import datetime, timedelta
# # # # # # # # from utils.security import create_access_token
# # # # # # # #
# # # # # # # # router = APIRouter()
# # # # # # # #
# # # # # # # # OTP_TTL_SEC = 300
# # # # # # # # OTP_MAX_ATTEMPTS = 5
# # # # # # # #
# # # # # # # #
# # # # # # # # class OtpSendRequest(BaseModel):
# # # # # # # #     mobile: str = Field(..., min_length=10, max_length=16)
# # # # # # # #     purpose: Literal["login", "signup"] = "login"
# # # # # # # #
# # # # # # # #
# # # # # # # # class OtpVerifyRequest(BaseModel):
# # # # # # # #     mobile: str
# # # # # # # #     otp: str = Field(..., min_length=4, max_length=8)
# # # # # # # #     purpose: Literal["login", "signup"] = "login"
# # # # # # # #     fullName: Optional[str] = None
# # # # # # # #     name: Optional[str] = None
# # # # # # # #     email: Optional[str] = None
# # # # # # # #     country: Optional[str] = "India"
# # # # # # # #     city: Optional[str] = None
# # # # # # # #     pincode: Optional[str] = None
# # # # # # # #     gender: Optional[str] = None
# # # # # # # #     want_to: Optional[Literal["finder", "companion"]] = "finder"
# # # # # # # #     lat: Optional[float] = None
# # # # # # # #     lng: Optional[float] = None
# # # # # # # #
# # # # # # # #
# # # # # # # # def _normalize_mobile(raw: str) -> str:
# # # # # # # #     s = re.sub(r"[^\d+]", "", (raw or "").strip())
# # # # # # # #     if s.startswith("00"):
# # # # # # # #         s = "+" + s[2:]
# # # # # # # #     if not s.startswith("+"):
# # # # # # # #         digits = re.sub(r"\D", "", s)
# # # # # # # #         if len(digits) == 10:
# # # # # # # #             s = "+91" + digits
# # # # # # # #         else:
# # # # # # # #             s = "+" + digits
# # # # # # # #     return s
# # # # # # # #
# # # # # # # #
# # # # # # # # def _hash_otp(code: str, salt: str) -> str:
# # # # # # # #     return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()
# # # # # # # #
# # # # # # # #
# # # # # # # # def _digits_only(mobile: str) -> str:
# # # # # # # #     """Meta 'to' field: digits only, no +."""
# # # # # # # #     return re.sub(r"\D", "", mobile or "")
# # # # # # # #
# # # # # # # #
# # # # # # # # async def _http_json(
# # # # # # # #     method: str,
# # # # # # # #     url: str,
# # # # # # # #     headers: dict,
# # # # # # # #     body: dict | None = None,
# # # # # # # # ) -> tuple[int, dict]:
# # # # # # # #     """Workers fetch first; urllib fallback for local."""
# # # # # # # #     import json as _json
# # # # # # # #
# # # # # # # #     payload = _json.dumps(body) if body is not None else None
# # # # # # # #
# # # # # # # #     try:
# # # # # # # #         from js import fetch, Object
# # # # # # # #         from pyodide.ffi import to_js
# # # # # # # #
# # # # # # # #         opts = {"method": method, "headers": headers}
# # # # # # # #         if payload is not None:
# # # # # # # #             opts["body"] = payload
# # # # # # # #         resp = await fetch(url, to_js(opts, dict_converter=Object.fromEntries))
# # # # # # # #         text = await resp.text()
# # # # # # # #         code = int(resp.status)
# # # # # # # #         try:
# # # # # # # #             data = _json.loads(text) if text else {}
# # # # # # # #         except Exception:
# # # # # # # #             data = {"message": text}
# # # # # # # #         return code, data
# # # # # # # #     except Exception:
# # # # # # # #         pass
# # # # # # # #
# # # # # # # #     import urllib.request
# # # # # # # #     import urllib.error
# # # # # # # #
# # # # # # # #     data_bytes = payload.encode("utf-8") if payload else None
# # # # # # # #     req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
# # # # # # # #     try:
# # # # # # # #         with urllib.request.urlopen(req, timeout=30) as resp:
# # # # # # # #             text = resp.read().decode("utf-8")
# # # # # # # #             return resp.status, (_json.loads(text) if text else {})
# # # # # # # #     except urllib.error.HTTPError as e:
# # # # # # # #         text = e.read().decode("utf-8")
# # # # # # # #         try:
# # # # # # # #             data = _json.loads(text) if text else {}
# # # # # # # #         except Exception:
# # # # # # # #             data = {"message": text}
# # # # # # # #         return int(e.code), data
# # # # # # # #     except Exception as e:
# # # # # # # #         raise HTTPException(status_code=502, detail=f"WhatsApp request failed: {e}")
# # # # # # # #
# # # # # # # #
# # # # # # # # async def _send_whatsapp_otp(request: Request, mobile: str, code: str):
# # # # # # # #     """
# # # # # # # #     Template from WHATSAPP_OTP_TEMPLATE.
# # # # # # # #     - hello_world: en_US, no components (does NOT include OTP digits)
# # # # # # # #     - real OTP template: body {{1}} = code
# # # # # # # #     """
# # # # # # # #     env = request.scope["env"]
# # # # # # # #     token = (getattr(env, "WHATSAPP_TOKEN", None) or "").strip()
# # # # # # # #     phone_id = (getattr(env, "WHATSAPP_PHONE_NUMBER_ID", None) or "").strip()
# # # # # # # #     template = (getattr(env, "WHATSAPP_OTP_TEMPLATE", None) or "login_otp").strip()
# # # # # # # #     lang = (getattr(env, "WHATSAPP_OTP_LANG", None) or "en_US").strip()
# # # # # # # #
# # # # # # # #     if not token or not phone_id:
# # # # # # # #         raise HTTPException(status_code=500, detail="WhatsApp not configured")
# # # # # # # #
# # # # # # # #     url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
# # # # # # # #     headers = {
# # # # # # # #         "Authorization": f"Bearer {token}",
# # # # # # # #         "Content-Type": "application/json",
# # # # # # # #     }
# # # # # # # #     to = _digits_only(mobile)
# # # # # # # #
# # # # # # # #     if template.lower() in ("login_otp", "hello world"):
# # # # # # # #         body = {
# # # # # # # #             "messaging_product": "whatsapp",
# # # # # # # #             "to": to,
# # # # # # # #             "type": "template",
# # # # # # # #             "template": {
# # # # # # # #                 "name": "login_otp",
# # # # # # # #                 "language": {"code": "en_US"},
# # # # # # # #             },
# # # # # # # #         }
# # # # # # # #     elif template:
# # # # # # # #         body = {
# # # # # # # #             "messaging_product": "whatsapp",
# # # # # # # #             "to": to,
# # # # # # # #             "type": "template",
# # # # # # # #             "template": {
# # # # # # # #                 "name": template,
# # # # # # # #                 "language": {"code": lang},
# # # # # # # #                 "components": [
# # # # # # # #                     {
# # # # # # # #                         "type": "body",
# # # # # # # #                         "parameters": [{"type": "text", "text": code}],
# # # # # # # #                     }
# # # # # # # #                 ],
# # # # # # # #             },
# # # # # # # #         }
# # # # # # # #     else:
# # # # # # # #         body = {
# # # # # # # #             "messaging_product": "whatsapp",
# # # # # # # #             "to": to,
# # # # # # # #             "type": "text",
# # # # # # # #             "text": {
# # # # # # # #                 "body": f"Your verification code is {code}. Valid for 5 minutes.",
# # # # # # # #             },
# # # # # # # #         }
# # # # # # # #
# # # # # # # #     code_http, data = await _http_json("POST", url, headers, body)
# # # # # # # #     if code_http >= 400:
# # # # # # # #         err = {}
# # # # # # # #         if isinstance(data, dict):
# # # # # # # #             err = data.get("error") or data
# # # # # # # #         msg = err.get("message") if isinstance(err, dict) else str(data)
# # # # # # # #         raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
# # # # # # # #     return data
# # # # # # # #
# # # # # # # #
# # # # # # # # @router.post("/auth/otp/send")
# # # # # # # # async def otp_send(data: OtpSendRequest, request: Request):
# # # # # # # #     db = request.scope["env"].DB
# # # # # # # #     mobile = _normalize_mobile(data.mobile)
# # # # # # # #     purpose = data.purpose
# # # # # # # #
# # # # # # # #     user = await db.prepare(
# # # # # # # #         "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
# # # # # # # #     ).bind(mobile, mobile.lstrip("+")).first()
# # # # # # # #
# # # # # # # #     if purpose == "login" and not user:
# # # # # # # #         raise HTTPException(
# # # # # # # #             status_code=404,
# # # # # # # #             detail="No account with this mobile. Please sign up.",
# # # # # # # #         )
# # # # # # # #     if purpose == "signup" and user:
# # # # # # # #         raise HTTPException(
# # # # # # # #             status_code=409,
# # # # # # # #             detail="Mobile already registered. Please login.",
# # # # # # # #         )
# # # # # # # #
# # # # # # # #     code = f"{secrets.randbelow(10**6):06d}"
# # # # # # # #     salt = secrets.token_hex(8)
# # # # # # # #     code_hash = _hash_otp(code, salt)
# # # # # # # #     expires = (datetime.utcnow() + timedelta(seconds=OTP_TTL_SEC)).isoformat()
# # # # # # # #     otp_id = secrets.token_hex(8)
# # # # # # # #
# # # # # # # #     await db.prepare(
# # # # # # # #         """
# # # # # # # #         UPDATE otp_codes SET consumed = 1
# # # # # # # #         WHERE mobile = ? AND purpose = ? AND consumed = 0
# # # # # # # #         """
# # # # # # # #     ).bind(mobile, purpose).run()
# # # # # # # #
# # # # # # # #     await db.prepare(
# # # # # # # #         """
# # # # # # # #         INSERT INTO otp_codes (id, mobile, purpose, code_hash, expires_at, attempts, consumed)
# # # # # # # #         VALUES (?, ?, ?, ?, ?, 0, 0)
# # # # # # # #         """
# # # # # # # #     ).bind(otp_id, mobile, purpose, f"{salt}:{code_hash}", expires).run()
# # # # # # # #
# # # # # # # #     await _send_whatsapp_otp(request, mobile, code)
# # # # # # # #
# # # # # # # #     return {
# # # # # # # #         "message": "OTP sent on WhatsApp",
# # # # # # # #         "mobile": mobile,
# # # # # # # #         "purpose": purpose,
# # # # # # # #         "expires_in": OTP_TTL_SEC,
# # # # # # # #     }
# # # # # # # #
# # # # # # # #
# # # # # # # # @router.post("/auth/otp/verify")
# # # # # # # # async def otp_verify(data: OtpVerifyRequest, request: Request):
# # # # # # # #     db = request.scope["env"].DB
# # # # # # # #     mobile = _normalize_mobile(data.mobile)
# # # # # # # #     purpose = data.purpose
# # # # # # # #     otp = (data.otp or "").strip()
# # # # # # # #
# # # # # # # #     row = await db.prepare(
# # # # # # # #         """
# # # # # # # #         SELECT * FROM otp_codes
# # # # # # # #         WHERE mobile = ? AND purpose = ? AND consumed = 0
# # # # # # # #         ORDER BY created_at DESC LIMIT 1
# # # # # # # #         """
# # # # # # # #     ).bind(mobile, purpose).first()
# # # # # # # #     if not row:
# # # # # # # #         raise HTTPException(
# # # # # # # #             status_code=400,
# # # # # # # #             detail="OTP expired or not found. Request a new one.",
# # # # # # # #         )
# # # # # # # #
# # # # # # # #     r = dict(row)
# # # # # # # #     if int(r.get("attempts") or 0) >= OTP_MAX_ATTEMPTS:
# # # # # # # #         raise HTTPException(
# # # # # # # #             status_code=429,
# # # # # # # #             detail="Too many attempts. Request a new OTP.",
# # # # # # # #         )
# # # # # # # #
# # # # # # # #     exp = datetime.fromisoformat(str(r["expires_at"]).replace("Z", ""))
# # # # # # # #     if datetime.utcnow() > exp:
# # # # # # # #         raise HTTPException(
# # # # # # # #             status_code=400,
# # # # # # # #             detail="OTP expired. Request a new one.",
# # # # # # # #         )
# # # # # # # #
# # # # # # # #     salt, stored_hash = str(r["code_hash"]).split(":", 1)
# # # # # # # #     if not hmac.compare_digest(_hash_otp(otp, salt), stored_hash):
# # # # # # # #         await db.prepare(
# # # # # # # #             "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ?"
# # # # # # # #         ).bind(r["id"]).run()
# # # # # # # #         raise HTTPException(status_code=400, detail="Invalid OTP")
# # # # # # # #
# # # # # # # #     await db.prepare(
# # # # # # # #         "UPDATE otp_codes SET consumed = 1 WHERE id = ?"
# # # # # # # #     ).bind(r["id"]).run()
# # # # # # # #
# # # # # # # #     if purpose == "login":
# # # # # # # #         user = await db.prepare(
# # # # # # # #             "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
# # # # # # # #         ).bind(mobile, mobile.lstrip("+")).first()
# # # # # # # #         if not user:
# # # # # # # #             raise HTTPException(status_code=404, detail="User not found")
# # # # # # # #         u = dict(user)
# # # # # # # #     else:
# # # # # # # #         existing = await db.prepare(
# # # # # # # #             "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
# # # # # # # #         ).bind(mobile, mobile.lstrip("+")).first()
# # # # # # # #         if existing:
# # # # # # # #             raise HTTPException(
# # # # # # # #                 status_code=409,
# # # # # # # #                 detail="Mobile already registered",
# # # # # # # #             )
# # # # # # # #
# # # # # # # #         full_name = (data.fullName or data.name or "User").strip()
# # # # # # # #         user_id = secrets.token_hex(4).upper()
# # # # # # # #         digits = _digits_only(mobile)
# # # # # # # #         email = (data.email or f"{digits}@otp.local").strip()
# # # # # # # #         want_to = data.want_to or "finder"
# # # # # # # #
# # # # # # # #         await db.prepare(
# # # # # # # #             """
# # # # # # # #             INSERT INTO users (
# # # # # # # #                 id, full_name, email, mobile, country, city, pincode,
# # # # # # # #                 gender, want_to, password_hash, lat, lng
# # # # # # # #             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
# # # # # # # #             """
# # # # # # # #         ).bind(
# # # # # # # #             user_id,
# # # # # # # #             full_name,
# # # # # # # #             email,
# # # # # # # #             mobile,
# # # # # # # #             data.country or "India",
# # # # # # # #             data.city or "",
# # # # # # # #             data.pincode or "",
# # # # # # # #             data.gender or "",
# # # # # # # #             want_to,
# # # # # # # #             secrets.token_hex(16),
# # # # # # # #             data.lat,
# # # # # # # #             data.lng,
# # # # # # # #         ).run()
# # # # # # # #
# # # # # # # #         user = await db.prepare(
# # # # # # # #             "SELECT * FROM users WHERE id = ?"
# # # # # # # #         ).bind(user_id).first()
# # # # # # # #         u = dict(user)
# # # # # # # #
# # # # # # # #     token = create_access_token({"sub": u["id"]})
# # # # # # # #     return {
# # # # # # # #         "access_token": token,
# # # # # # # #         "token": token,
# # # # # # # #         "token_type": "bearer",
# # # # # # # #         "user": {
# # # # # # # #             "id": u["id"],
# # # # # # # #             "account_id": u["id"],
# # # # # # # #             "fullName": u.get("full_name"),
# # # # # # # #             "name": u.get("full_name"),
# # # # # # # #             "email": u.get("email"),
# # # # # # # #             "mobile": u.get("mobile"),
# # # # # # # #             "want_to": u.get("want_to"),
# # # # # # # #             "role": u.get("want_to"),
# # # # # # # #             "city": u.get("city"),
# # # # # # # #         },
# # # # # # # #     }
# # # # # # #
# # # # # # #
# # # # # # # from fastapi import APIRouter, Request, HTTPException
# # # # # # # from pydantic import BaseModel, Field
# # # # # # # from typing import Optional, Literal
# # # # # # # import secrets
# # # # # # # import hashlib
# # # # # # # import hmac
# # # # # # # import re
# # # # # # # from datetime import datetime, timedelta
# # # # # # # from utils.security import create_access_token
# # # # # # #
# # # # # # # router = APIRouter()
# # # # # # #
# # # # # # # OTP_TTL_SEC = 300
# # # # # # # OTP_MAX_ATTEMPTS = 5
# # # # # # #
# # # # # # # # Templates that do NOT take body parameters (Meta sample)
# # # # # # # NO_PARAM_TEMPLATES = {"hello_world", "hello world"}
# # # # # # #
# # # # # # # # Auth / OTP templates that take {{1}} = code (+ copy-code button)
# # # # # # # AUTH_OTP_TEMPLATES = {
# # # # # # #     "logn_otp",
# # # # # # #     "verify_code",
# # # # # # #     "verify_code_1",
# # # # # # #     "authentication_code",
# # # # # # #     "otp_verification",
# # # # # # # }
# # # # # # #
# # # # # # #
# # # # # # # class OtpSendRequest(BaseModel):
# # # # # # #     mobile: str = Field(..., min_length=10, max_length=16)
# # # # # # #     purpose: Literal["login", "signup"] = "login"
# # # # # # #
# # # # # # #
# # # # # # # class OtpVerifyRequest(BaseModel):
# # # # # # #     mobile: str
# # # # # # #     otp: str = Field(..., min_length=4, max_length=8)
# # # # # # #     purpose: Literal["login", "signup"] = "login"
# # # # # # #     fullName: Optional[str] = None
# # # # # # #     name: Optional[str] = None
# # # # # # #     email: Optional[str] = None
# # # # # # #     country: Optional[str] = "India"
# # # # # # #     city: Optional[str] = None
# # # # # # #     pincode: Optional[str] = None
# # # # # # #     gender: Optional[str] = None
# # # # # # #     want_to: Optional[Literal["finder", "companion"]] = "finder"
# # # # # # #     lat: Optional[float] = None
# # # # # # #     lng: Optional[float] = None
# # # # # # #
# # # # # # #
# # # # # # # def _normalize_mobile(raw: str) -> str:
# # # # # # #     s = re.sub(r"[^\d+]", "", (raw or "").strip())
# # # # # # #     if s.startswith("00"):
# # # # # # #         s = "+" + s[2:]
# # # # # # #     if not s.startswith("+"):
# # # # # # #         digits = re.sub(r"\D", "", s)
# # # # # # #         if len(digits) == 10:
# # # # # # #             s = "+91" + digits
# # # # # # #         else:
# # # # # # #             s = "+" + digits
# # # # # # #     return s
# # # # # # #
# # # # # # #
# # # # # # # def _hash_otp(code: str, salt: str) -> str:
# # # # # # #     return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()
# # # # # # #
# # # # # # #
# # # # # # # def _digits_only(mobile: str) -> str:
# # # # # # #     """Meta 'to' field: digits only, no +."""
# # # # # # #     return re.sub(r"\D", "", mobile or "")
# # # # # # #
# # # # # # #
# # # # # # # async def _http_json(
# # # # # # #     method: str,
# # # # # # #     url: str,
# # # # # # #     headers: dict,
# # # # # # #     body: dict | None = None,
# # # # # # # ) -> tuple[int, dict]:
# # # # # # #     """Workers fetch first; urllib fallback for local."""
# # # # # # #     import json as _json
# # # # # # #
# # # # # # #     payload = _json.dumps(body) if body is not None else None
# # # # # # #
# # # # # # #     try:
# # # # # # #         from js import fetch, Object
# # # # # # #         from pyodide.ffi import to_js
# # # # # # #
# # # # # # #         opts = {"method": method, "headers": headers}
# # # # # # #         if payload is not None:
# # # # # # #             opts["body"] = payload
# # # # # # #         resp = await fetch(url, to_js(opts, dict_converter=Object.fromEntries))
# # # # # # #         text = await resp.text()
# # # # # # #         code = int(resp.status)
# # # # # # #         try:
# # # # # # #             data = _json.loads(text) if text else {}
# # # # # # #         except Exception:
# # # # # # #             data = {"message": text}
# # # # # # #         return code, data
# # # # # # #     except Exception:
# # # # # # #         pass
# # # # # # #
# # # # # # #     import urllib.request
# # # # # # #     import urllib.error
# # # # # # #
# # # # # # #     data_bytes = payload.encode("utf-8") if payload else None
# # # # # # #     req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
# # # # # # #     try:
# # # # # # #         with urllib.request.urlopen(req, timeout=30) as resp:
# # # # # # #             text = resp.read().decode("utf-8")
# # # # # # #             return resp.status, (_json.loads(text) if text else {})
# # # # # # #     except urllib.error.HTTPError as e:
# # # # # # #         text = e.read().decode("utf-8")
# # # # # # #         try:
# # # # # # #             data = _json.loads(text) if text else {}
# # # # # # #         except Exception:
# # # # # # #             data = {"message": text}
# # # # # # #         return int(e.code), data
# # # # # # #     except Exception as e:
# # # # # # #         raise HTTPException(status_code=502, detail=f"WhatsApp request failed: {e}")
# # # # # # #
# # # # # # #
# # # # # # # def _build_auth_otp_template(name: str, lang: str, code: str) -> dict:
# # # # # # #     """
# # # # # # #     Authentication template send payload (Meta docs).
# # # # # # #     - BODY parameter {{1}} = OTP
# # # # # # #     - BUTTON (copy code / OTP) also needs the same code
# # # # # # #     """
# # # # # # #     return {
# # # # # # #         "name": name,
# # # # # # #         "language": {"code": lang},
# # # # # # #         "components": [
# # # # # # #             {
# # # # # # #                 "type": "body",
# # # # # # #                 "parameters": [
# # # # # # #                     {"type": "text", "text": str(code)},
# # # # # # #                 ],
# # # # # # #             },
# # # # # # #             {
# # # # # # #                 "type": "button",
# # # # # # #                 "sub_type": "url",
# # # # # # #                 "index": "0",
# # # # # # #                 "parameters": [
# # # # # # #                     {"type": "text", "text": str(code)},
# # # # # # #                 ],
# # # # # # #             },
# # # # # # #         ],
# # # # # # #     }
# # # # # # #
# # # # # # #
# # # # # # # async def _send_whatsapp_otp(request: Request, mobile: str, code: str):
# # # # # # #     """
# # # # # # #     WHATSAPP_OTP_TEMPLATE:
# # # # # # #       - hello_world → sample, no params (does not show OTP)
# # # # # # #       - login_otp / auth names → Authentication body+button with code
# # # # # # #       - other → body {{1}} only
# # # # # # #       - empty → session text (only works inside 24h window)
# # # # # # #     """
# # # # # # #     env = request.scope["env"]
# # # # # # #     token = (getattr(env, "WHATSAPP_TOKEN", None) or "").strip()
# # # # # # #     phone_id = (getattr(env, "WHATSAPP_PHONE_NUMBER_ID", None) or "").strip()
# # # # # # #     template = (getattr(env, "WHATSAPP_OTP_TEMPLATE", None) or "logn_otp").strip()
# # # # # # #     lang = (getattr(env, "WHATSAPP_OTP_LANG", None) or "en").strip()
# # # # # # #
# # # # # # #     if not token or not phone_id:
# # # # # # #         raise HTTPException(status_code=500, detail="WhatsApp not configured")
# # # # # # #
# # # # # # #     url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
# # # # # # #     headers = {
# # # # # # #         "Authorization": f"Bearer {token}",
# # # # # # #         "Content-Type": "application/json",
# # # # # # #     }
# # # # # # #     to = _digits_only(mobile)
# # # # # # #     t_lower = template.lower().replace("-", "_")
# # # # # # #
# # # # # # #     if t_lower in NO_PARAM_TEMPLATES:
# # # # # # #         # Meta sample — no OTP in message
# # # # # # #         template_obj = {
# # # # # # #             "name": "hello_world",
# # # # # # #             "language": {"code": "en"},
# # # # # # #         }
# # # # # # #     elif t_lower in AUTH_OTP_TEMPLATES or t_lower.endswith("_otp") or "otp" in t_lower:
# # # # # # #         # Authentication OTP (login_otp, etc.)
# # # # # # #         template_obj = _build_auth_otp_template(template, lang, code)
# # # # # # #     elif template:
# # # # # # #         # Generic utility with single body param
# # # # # # #         template_obj = {
# # # # # # #             "name": template,
# # # # # # #             "language": {"code": lang},
# # # # # # #             "components": [
# # # # # # #                 {
# # # # # # #                     "type": "body",
# # # # # # #                     "parameters": [{"type": "text", "text": str(code)}],
# # # # # # #                 }
# # # # # # #             ],
# # # # # # #         }
# # # # # # #     else:
# # # # # # #         # Session free-text (user must have messaged you in last 24h)
# # # # # # #         body = {
# # # # # # #             "messaging_product": "whatsapp",
# # # # # # #             "to": to,
# # # # # # #             "type": "text",
# # # # # # #             "text": {
# # # # # # #                 "body": f"Your verification code is {code}. Valid for 5 minutes.",
# # # # # # #             },
# # # # # # #         }
# # # # # # #         code_http, data = await _http_json("POST", url, headers, body)
# # # # # # #         if code_http >= 400:
# # # # # # #             err = (data.get("error") if isinstance(data, dict) else None) or data
# # # # # # #             msg = err.get("message") if isinstance(err, dict) else str(data)
# # # # # # #             raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
# # # # # # #         return data
# # # # # # #
# # # # # # #     body = {
# # # # # # #         "messaging_product": "whatsapp",
# # # # # # #         "recipient_type": "individual",
# # # # # # #         "to": to,
# # # # # # #         "type": "template",
# # # # # # #         "template": template_obj,
# # # # # # #     }
# # # # # # #
# # # # # # #     code_http, data = await _http_json("POST", url, headers, body)
# # # # # # #     if code_http >= 400:
# # # # # # #         err = {}
# # # # # # #         if isinstance(data, dict):
# # # # # # #             err = data.get("error") or data
# # # # # # #         msg = err.get("message") if isinstance(err, dict) else str(data)
# # # # # # #         # If button component not accepted (template has no button), retry body-only
# # # # # # #         if (
# # # # # # #             code_http >= 400
# # # # # # #             and isinstance(err, dict)
# # # # # # #             and template_obj.get("components")
# # # # # # #             and len(template_obj["components"]) > 1
# # # # # # #         ):
# # # # # # #             template_obj = {
# # # # # # #                 "name": template_obj["name"],
# # # # # # #                 "language": template_obj["language"],
# # # # # # #                 "components": [
# # # # # # #                     {
# # # # # # #                         "type": "body",
# # # # # # #                         "parameters": [{"type": "text", "text": str(code)}],
# # # # # # #                     }
# # # # # # #                 ],
# # # # # # #             }
# # # # # # #             body["template"] = template_obj
# # # # # # #             code_http, data = await _http_json("POST", url, headers, body)
# # # # # # #             if code_http < 400:
# # # # # # #                 return data
# # # # # # #             err = (data.get("error") if isinstance(data, dict) else None) or data
# # # # # # #             msg = err.get("message") if isinstance(err, dict) else str(data)
# # # # # # #         raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
# # # # # # #     return data
# # # # # # #
# # # # # # #
# # # # # # # @router.post("/auth/otp/send")
# # # # # # # async def otp_send(data: OtpSendRequest, request: Request):
# # # # # # #     db = request.scope["env"].DB
# # # # # # #     mobile = _normalize_mobile(data.mobile)
# # # # # # #     purpose = data.purpose
# # # # # # #
# # # # # # #     user = await db.prepare(
# # # # # # #         "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
# # # # # # #     ).bind(mobile, mobile.lstrip("+")).first()
# # # # # # #
# # # # # # #     if purpose == "login" and not user:
# # # # # # #         raise HTTPException(
# # # # # # #             status_code=404,
# # # # # # #             detail="No account with this mobile. Please sign up.",
# # # # # # #         )
# # # # # # #     if purpose == "signup" and user:
# # # # # # #         raise HTTPException(
# # # # # # #             status_code=409,
# # # # # # #             detail="Mobile already registered. Please login.",
# # # # # # #         )
# # # # # # #
# # # # # # #     code = f"{secrets.randbelow(10**6):06d}"
# # # # # # #     salt = secrets.token_hex(8)
# # # # # # #     code_hash = _hash_otp(code, salt)
# # # # # # #     expires = (datetime.utcnow() + timedelta(seconds=OTP_TTL_SEC)).isoformat()
# # # # # # #     otp_id = secrets.token_hex(8)
# # # # # # #
# # # # # # #     await db.prepare(
# # # # # # #         """
# # # # # # #         UPDATE otp_codes SET consumed = 1
# # # # # # #         WHERE mobile = ? AND purpose = ? AND consumed = 0
# # # # # # #         """
# # # # # # #     ).bind(mobile, purpose).run()
# # # # # # #
# # # # # # #     await db.prepare(
# # # # # # #         """
# # # # # # #         INSERT INTO otp_codes (id, mobile, purpose, code_hash, expires_at, attempts, consumed)
# # # # # # #         VALUES (?, ?, ?, ?, ?, 0, 0)
# # # # # # #         """
# # # # # # #     ).bind(otp_id, mobile, purpose, f"{salt}:{code_hash}", expires).run()
# # # # # # #
# # # # # # #     await _send_whatsapp_otp(request, mobile, code)
# # # # # # #
# # # # # # #     return {
# # # # # # #         "message": "OTP sent on WhatsApp",
# # # # # # #         "mobile": mobile,
# # # # # # #         "purpose": purpose,
# # # # # # #         "expires_in": OTP_TTL_SEC,
# # # # # # #     }
# # # # # # #
# # # # # # #
# # # # # # # @router.post("/auth/otp/verify")
# # # # # # # async def otp_verify(data: OtpVerifyRequest, request: Request):
# # # # # # #     db = request.scope["env"].DB
# # # # # # #     mobile = _normalize_mobile(data.mobile)
# # # # # # #     purpose = data.purpose
# # # # # # #     otp = (data.otp or "").strip()
# # # # # # #
# # # # # # #     row = await db.prepare(
# # # # # # #         """
# # # # # # #         SELECT * FROM otp_codes
# # # # # # #         WHERE mobile = ? AND purpose = ? AND consumed = 0
# # # # # # #         ORDER BY created_at DESC LIMIT 1
# # # # # # #         """
# # # # # # #     ).bind(mobile, purpose).first()
# # # # # # #     if not row:
# # # # # # #         raise HTTPException(
# # # # # # #             status_code=400,
# # # # # # #             detail="OTP expired or not found. Request a new one.",
# # # # # # #         )
# # # # # # #
# # # # # # #     r = dict(row)
# # # # # # #     if int(r.get("attempts") or 0) >= OTP_MAX_ATTEMPTS:
# # # # # # #         raise HTTPException(
# # # # # # #             status_code=429,
# # # # # # #             detail="Too many attempts. Request a new OTP.",
# # # # # # #         )
# # # # # # #
# # # # # # #     exp = datetime.fromisoformat(str(r["expires_at"]).replace("Z", ""))
# # # # # # #     if datetime.utcnow() > exp:
# # # # # # #         raise HTTPException(
# # # # # # #             status_code=400,
# # # # # # #             detail="OTP expired. Request a new one.",
# # # # # # #         )
# # # # # # #
# # # # # # #     salt, stored_hash = str(r["code_hash"]).split(":", 1)
# # # # # # #     if not hmac.compare_digest(_hash_otp(otp, salt), stored_hash):
# # # # # # #         await db.prepare(
# # # # # # #             "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ?"
# # # # # # #         ).bind(r["id"]).run()
# # # # # # #         raise HTTPException(status_code=400, detail="Invalid OTP")
# # # # # # #
# # # # # # #     await db.prepare(
# # # # # # #         "UPDATE otp_codes SET consumed = 1 WHERE id = ?"
# # # # # # #     ).bind(r["id"]).run()
# # # # # # #
# # # # # # #     if purpose == "login":
# # # # # # #         user = await db.prepare(
# # # # # # #             "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
# # # # # # #         ).bind(mobile, mobile.lstrip("+")).first()
# # # # # # #         if not user:
# # # # # # #             raise HTTPException(status_code=404, detail="User not found")
# # # # # # #         u = dict(user)
# # # # # # #     else:
# # # # # # #         existing = await db.prepare(
# # # # # # #             "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
# # # # # # #         ).bind(mobile, mobile.lstrip("+")).first()
# # # # # # #         if existing:
# # # # # # #             raise HTTPException(
# # # # # # #                 status_code=409,
# # # # # # #                 detail="Mobile already registered",
# # # # # # #             )
# # # # # # #
# # # # # # #         full_name = (data.fullName or data.name or "User").strip()
# # # # # # #         user_id = secrets.token_hex(4).upper()
# # # # # # #         digits = _digits_only(mobile)
# # # # # # #         email = (data.email or f"{digits}@otp.local").strip()
# # # # # # #         want_to = data.want_to or "finder"
# # # # # # #
# # # # # # #         await db.prepare(
# # # # # # #             """
# # # # # # #             INSERT INTO users (
# # # # # # #                 id, full_name, email, mobile, country, city, pincode,
# # # # # # #                 gender, want_to, password_hash, lat, lng
# # # # # # #             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
# # # # # # #             """
# # # # # # #         ).bind(
# # # # # # #             user_id,
# # # # # # #             full_name,
# # # # # # #             email,
# # # # # # #             mobile,
# # # # # # #             data.country or "India",
# # # # # # #             data.city or "",
# # # # # # #             data.pincode or "",
# # # # # # #             data.gender or "",
# # # # # # #             want_to,
# # # # # # #             secrets.token_hex(16),
# # # # # # #             data.lat,
# # # # # # #             data.lng,
# # # # # # #         ).run()
# # # # # # #
# # # # # # #         user = await db.prepare(
# # # # # # #             "SELECT * FROM users WHERE id = ?"
# # # # # # #         ).bind(user_id).first()
# # # # # # #         u = dict(user)
# # # # # # #
# # # # # # #     token = create_access_token({"sub": u["id"]})
# # # # # # #     return {
# # # # # # #         "access_token": token,
# # # # # # #         "token": token,
# # # # # # #         "token_type": "bearer",
# # # # # # #         "user": {
# # # # # # #             "id": u["id"],
# # # # # # #             "account_id": u["id"],
# # # # # # #             "fullName": u.get("full_name"),
# # # # # # #             "name": u.get("full_name"),
# # # # # # #             "email": u.get("email"),
# # # # # # #             "mobile": u.get("mobile"),
# # # # # # #             "want_to": u.get("want_to"),
# # # # # # #             "role": u.get("want_to"),
# # # # # # #             "city": u.get("city"),
# # # # # # #         },
# # # # # # #     }
# # # # # #
# # # # # #
# # # # # # from fastapi import APIRouter, Request, HTTPException
# # # # # # from pydantic import BaseModel, Field
# # # # # # from typing import Optional, Literal
# # # # # # import secrets
# # # # # # import hashlib
# # # # # # import hmac
# # # # # # import re
# # # # # # from datetime import datetime, timedelta
# # # # # # from utils.security import create_access_token
# # # # # #
# # # # # # router = APIRouter()
# # # # # #
# # # # # # OTP_TTL_SEC = 300
# # # # # # OTP_MAX_ATTEMPTS = 5
# # # # # #
# # # # # # NO_PARAM_TEMPLATES = {"hello_world", "hello world"}
# # # # # #
# # # # # # AUTH_OTP_TEMPLATES = {
# # # # # #     "login_otp",  # fixed typo (was logn_otp)
# # # # # #     "logn_otp",   # keep alias if secret still has old name
# # # # # #     "verify_code",
# # # # # #     "verify_code_1",
# # # # # #     "authentication_code",
# # # # # #     "otp_verification",
# # # # # # }
# # # # # #
# # # # # #
# # # # # # class OtpSendRequest(BaseModel):
# # # # # #     mobile: str = Field(..., min_length=10, max_length=16)
# # # # # #     purpose: Literal["login", "signup"] = "login"
# # # # # #
# # # # # #
# # # # # # class OtpVerifyRequest(BaseModel):
# # # # # #     mobile: str
# # # # # #     otp: str = Field(..., min_length=4, max_length=8)
# # # # # #     purpose: Literal["login", "signup"] = "login"
# # # # # #     fullName: Optional[str] = None
# # # # # #     name: Optional[str] = None
# # # # # #     email: Optional[str] = None
# # # # # #     country: Optional[str] = "India"
# # # # # #     city: Optional[str] = None
# # # # # #     pincode: Optional[str] = None
# # # # # #     gender: Optional[str] = None
# # # # # #     want_to: Optional[Literal["finder", "companion"]] = "finder"
# # # # # #     lat: Optional[float] = None
# # # # # #     lng: Optional[float] = None
# # # # # #
# # # # # #
# # # # # # def _normalize_mobile(raw: str) -> str:
# # # # # #     s = re.sub(r"[^\d+]", "", (raw or "").strip())
# # # # # #     if s.startswith("00"):
# # # # # #         s = "+" + s[2:]
# # # # # #     if not s.startswith("+"):
# # # # # #         digits = re.sub(r"\D", "", s)
# # # # # #         if len(digits) == 10:
# # # # # #             s = "+91" + digits
# # # # # #         else:
# # # # # #             s = "+" + digits
# # # # # #     return s
# # # # # #
# # # # # #
# # # # # # def _hash_otp(code: str, salt: str) -> str:
# # # # # #     return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()
# # # # # #
# # # # # #
# # # # # # def _digits_only(mobile: str) -> str:
# # # # # #     return re.sub(r"\D", "", mobile or "")
# # # # # #
# # # # # #
# # # # # # async def _http_json(
# # # # # #     method: str,
# # # # # #     url: str,
# # # # # #     headers: dict,
# # # # # #     body: dict | None = None,
# # # # # # ) -> tuple[int, dict]:
# # # # # #     import json as _json
# # # # # #
# # # # # #     payload = _json.dumps(body) if body is not None else None
# # # # # #
# # # # # #     try:
# # # # # #         from js import fetch, Object
# # # # # #         from pyodide.ffi import to_js
# # # # # #
# # # # # #         opts = {"method": method, "headers": headers}
# # # # # #         if payload is not None:
# # # # # #             opts["body"] = payload
# # # # # #         resp = await fetch(url, to_js(opts, dict_converter=Object.fromEntries))
# # # # # #         text = await resp.text()
# # # # # #         code = int(resp.status)
# # # # # #         try:
# # # # # #             data = _json.loads(text) if text else {}
# # # # # #         except Exception:
# # # # # #             data = {"message": text}
# # # # # #         return code, data
# # # # # #     except Exception:
# # # # # #         pass
# # # # # #
# # # # # #     import urllib.request
# # # # # #     import urllib.error
# # # # # #
# # # # # #     data_bytes = payload.encode("utf-8") if payload else None
# # # # # #     req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
# # # # # #     try:
# # # # # #         with urllib.request.urlopen(req, timeout=30) as resp:
# # # # # #             text = resp.read().decode("utf-8")
# # # # # #             return resp.status, (_json.loads(text) if text else {})
# # # # # #     except urllib.error.HTTPError as e:
# # # # # #         text = e.read().decode("utf-8")
# # # # # #         try:
# # # # # #             data = _json.loads(text) if text else {}
# # # # # #         except Exception:
# # # # # #             data = {"message": text}
# # # # # #         return int(e.code), data
# # # # # #     except Exception as e:
# # # # # #         raise HTTPException(status_code=502, detail=f"WhatsApp request failed: {e}")
# # # # # #
# # # # # #
# # # # # # def _build_auth_otp_template(name: str, lang: str, code: str) -> dict:
# # # # # #     return {
# # # # # #         "name": name,
# # # # # #         "language": {"code": lang},
# # # # # #         "components": [
# # # # # #             {
# # # # # #                 "type": "body",
# # # # # #                 "parameters": [{"type": "text", "text": str(code)}],
# # # # # #             },
# # # # # #             {
# # # # # #                 "type": "button",
# # # # # #                 "sub_type": "url",
# # # # # #                 "index": "0",
# # # # # #                 "parameters": [{"type": "text", "text": str(code)}],
# # # # # #             },
# # # # # #         ],
# # # # # #     }
# # # # # #
# # # # # #
# # # # # # async def _send_whatsapp_otp(request: Request, mobile: str, code: str):
# # # # # #     env = request.scope["env"]
# # # # # #     token = (getattr(env, "WHATSAPP_TOKEN", None) or "").strip()
# # # # # #     phone_id = (getattr(env, "WHATSAPP_PHONE_NUMBER_ID", None) or "").strip()
# # # # # #     template = (getattr(env, "WHATSAPP_OTP_TEMPLATE", None) or "login_otp").strip()
# # # # # #     lang = (getattr(env, "WHATSAPP_OTP_LANG", None) or "en").strip()
# # # # # #
# # # # # #     if not token or not phone_id:
# # # # # #         raise HTTPException(status_code=500, detail="WhatsApp not configured")
# # # # # #
# # # # # #     url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
# # # # # #     headers = {
# # # # # #         "Authorization": f"Bearer {token}",
# # # # # #         "Content-Type": "application/json",
# # # # # #     }
# # # # # #     to = _digits_only(mobile)
# # # # # #     t_lower = template.lower().replace("-", "_")
# # # # # #
# # # # # #     if t_lower in NO_PARAM_TEMPLATES:
# # # # # #         template_obj = {
# # # # # #             "name": "hello_world",
# # # # # #             "language": {"code": lang or "en"},
# # # # # #         }
# # # # # #     elif t_lower in AUTH_OTP_TEMPLATES or t_lower.endswith("_otp") or "otp" in t_lower:
# # # # # #         template_obj = _build_auth_otp_template(template, lang, code)
# # # # # #     elif template:
# # # # # #         template_obj = {
# # # # # #             "name": template,
# # # # # #             "language": {"code": lang},
# # # # # #             "components": [
# # # # # #                 {
# # # # # #                     "type": "body",
# # # # # #                     "parameters": [{"type": "text", "text": str(code)}],
# # # # # #                 }
# # # # # #             ],
# # # # # #         }
# # # # # #     else:
# # # # # #         body = {
# # # # # #             "messaging_product": "whatsapp",
# # # # # #             "to": to,
# # # # # #             "type": "text",
# # # # # #             "text": {
# # # # # #                 "body": f"Your verification code is {code}. Valid for 5 minutes.",
# # # # # #             },
# # # # # #         }
# # # # # #         code_http, data = await _http_json("POST", url, headers, body)
# # # # # #         if code_http >= 400:
# # # # # #             err = (data.get("error") if isinstance(data, dict) else None) or data
# # # # # #             msg = err.get("message") if isinstance(err, dict) else str(data)
# # # # # #             raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
# # # # # #         return data
# # # # # #
# # # # # #     body = {
# # # # # #         "messaging_product": "whatsapp",
# # # # # #         "recipient_type": "individual",
# # # # # #         "to": to,
# # # # # #         "type": "template",
# # # # # #         "template": template_obj,
# # # # # #     }
# # # # # #
# # # # # #     code_http, data = await _http_json("POST", url, headers, body)
# # # # # #     if code_http >= 400:
# # # # # #         err = {}
# # # # # #         if isinstance(data, dict):
# # # # # #             err = data.get("error") or data
# # # # # #         msg = err.get("message") if isinstance(err, dict) else str(data)
# # # # # #         if (
# # # # # #             code_http >= 400
# # # # # #             and isinstance(err, dict)
# # # # # #             and template_obj.get("components")
# # # # # #             and len(template_obj["components"]) > 1
# # # # # #         ):
# # # # # #             template_obj = {
# # # # # #                 "name": template_obj["name"],
# # # # # #                 "language": template_obj["language"],
# # # # # #                 "components": [
# # # # # #                     {
# # # # # #                         "type": "body",
# # # # # #                         "parameters": [{"type": "text", "text": str(code)}],
# # # # # #                     }
# # # # # #                 ],
# # # # # #             }
# # # # # #             body["template"] = template_obj
# # # # # #             code_http, data = await _http_json("POST", url, headers, body)
# # # # # #             if code_http < 400:
# # # # # #                 return data
# # # # # #             err = (data.get("error") if isinstance(data, dict) else None) or data
# # # # # #             msg = err.get("message") if isinstance(err, dict) else str(data)
# # # # # #         raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
# # # # # #     return data
# # # # # #
# # # # # #
# # # # # # @router.post("/auth/otp/send")
# # # # # # async def otp_send(data: OtpSendRequest, request: Request):
# # # # # #     db = request.scope["env"].DB
# # # # # #     mobile = _normalize_mobile(data.mobile)
# # # # # #     purpose = data.purpose
# # # # # #
# # # # # #     user = await db.prepare(
# # # # # #         "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
# # # # # #     ).bind(mobile, mobile.lstrip("+")).first()
# # # # # #
# # # # # #     if purpose == "login" and not user:
# # # # # #         raise HTTPException(
# # # # # #             status_code=404,
# # # # # #             detail="No account with this mobile. Please sign up.",
# # # # # #         )
# # # # # #     if purpose == "signup" and user:
# # # # # #         raise HTTPException(
# # # # # #             status_code=409,
# # # # # #             detail="Mobile already registered. Please login.",
# # # # # #         )
# # # # # #
# # # # # #     code = f"{secrets.randbelow(10**6):06d}"
# # # # # #     salt = secrets.token_hex(8)
# # # # # #     code_hash = _hash_otp(code, salt)
# # # # # #     expires = (datetime.utcnow() + timedelta(seconds=OTP_TTL_SEC)).isoformat()
# # # # # #     otp_id = secrets.token_hex(8)
# # # # # #
# # # # # #     await db.prepare(
# # # # # #         """
# # # # # #         UPDATE otp_codes SET consumed = 1
# # # # # #         WHERE mobile = ? AND purpose = ? AND consumed = 0
# # # # # #         """
# # # # # #     ).bind(mobile, purpose).run()
# # # # # #
# # # # # #     await db.prepare(
# # # # # #         """
# # # # # #         INSERT INTO otp_codes (id, mobile, purpose, code_hash, expires_at, attempts, consumed)
# # # # # #         VALUES (?, ?, ?, ?, ?, 0, 0)
# # # # # #         """
# # # # # #     ).bind(otp_id, mobile, purpose, f"{salt}:{code_hash}", expires).run()
# # # # # #
# # # # # #     await _send_whatsapp_otp(request, mobile, code)
# # # # # #
# # # # # #     return {
# # # # # #         "message": "OTP sent on WhatsApp",
# # # # # #         "mobile": mobile,
# # # # # #         "purpose": purpose,
# # # # # #         "expires_in": OTP_TTL_SEC,
# # # # # #     }
# # # # # #
# # # # # #
# # # # # # @router.post("/auth/otp/verify")
# # # # # # async def otp_verify(data: OtpVerifyRequest, request: Request):
# # # # # #     db = request.scope["env"].DB
# # # # # #     mobile = _normalize_mobile(data.mobile)
# # # # # #     purpose = data.purpose
# # # # # #     otp = (data.otp or "").strip()
# # # # # #
# # # # # #     row = await db.prepare(
# # # # # #         """
# # # # # #         SELECT * FROM otp_codes
# # # # # #         WHERE mobile = ? AND purpose = ? AND consumed = 0
# # # # # #         ORDER BY created_at DESC LIMIT 1
# # # # # #         """
# # # # # #     ).bind(mobile, purpose).first()
# # # # # #     if not row:
# # # # # #         raise HTTPException(
# # # # # #             status_code=400,
# # # # # #             detail="OTP expired or not found. Request a new one.",
# # # # # #         )
# # # # # #
# # # # # #     r = dict(row)
# # # # # #     if int(r.get("attempts") or 0) >= OTP_MAX_ATTEMPTS:
# # # # # #         raise HTTPException(
# # # # # #             status_code=429,
# # # # # #             detail="Too many attempts. Request a new OTP.",
# # # # # #         )
# # # # # #
# # # # # #     try:
# # # # # #         exp = datetime.fromisoformat(str(r["expires_at"]).replace("Z", ""))
# # # # # #     except Exception:
# # # # # #         raise HTTPException(status_code=400, detail="OTP expired. Request a new one.")
# # # # # #
# # # # # #     if datetime.utcnow() > exp:
# # # # # #         raise HTTPException(
# # # # # #             status_code=400,
# # # # # #             detail="OTP expired. Request a new one.",
# # # # # #         )
# # # # # #
# # # # # #     try:
# # # # # #         salt, stored_hash = str(r["code_hash"]).split(":", 1)
# # # # # #     except Exception:
# # # # # #         raise HTTPException(status_code=400, detail="Invalid OTP record. Request a new one.")
# # # # # #
# # # # # #     if not hmac.compare_digest(_hash_otp(otp, salt), stored_hash):
# # # # # #         await db.prepare(
# # # # # #             "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ?"
# # # # # #         ).bind(r["id"]).run()
# # # # # #         raise HTTPException(status_code=400, detail="Invalid OTP")
# # # # # #
# # # # # #     await db.prepare(
# # # # # #         "UPDATE otp_codes SET consumed = 1 WHERE id = ?"
# # # # # #     ).bind(r["id"]).run()
# # # # # #
# # # # # #     try:
# # # # # #         if purpose == "login":
# # # # # #             user = await db.prepare(
# # # # # #                 "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
# # # # # #             ).bind(mobile, mobile.lstrip("+")).first()
# # # # # #             if not user:
# # # # # #                 raise HTTPException(status_code=404, detail="User not found")
# # # # # #             u = dict(user)
# # # # # #         else:
# # # # # #             # Mobile already registered
# # # # # #             existing = await db.prepare(
# # # # # #                 "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
# # # # # #             ).bind(mobile, mobile.lstrip("+")).first()
# # # # # #             if existing:
# # # # # #                 raise HTTPException(
# # # # # #                     status_code=409,
# # # # # #                     detail="Mobile already registered. Please login.",
# # # # # #                 )
# # # # # #
# # # # # #             full_name = (data.fullName or data.name or "User").strip() or "User"
# # # # # #             user_id = secrets.token_hex(4).upper()
# # # # # #             digits = _digits_only(mobile)
# # # # # #             email = (data.email or f"{digits}@otp.local").strip()
# # # # # #             want_to = data.want_to or "finder"
# # # # # #             gender = (data.gender or "").strip()
# # # # # #             city = (data.city or "").strip()
# # # # # #             pincode = (data.pincode or "").strip()
# # # # # #             country = (data.country or "India").strip()
# # # # # #
# # # # # #             # Email unique → clear 409 instead of DB 500
# # # # # #             if email and not email.endswith("@otp.local"):
# # # # # #                 em = await db.prepare(
# # # # # #                     "SELECT id FROM users WHERE LOWER(email) = LOWER(?)"
# # # # # #                 ).bind(email).first()
# # # # # #                 if em:
# # # # # #                     raise HTTPException(
# # # # # #                         status_code=409,
# # # # # #                         detail="Email already registered. Use another email or login.",
# # # # # #                     )
# # # # # #
# # # # # #             try:
# # # # # #                 await db.prepare(
# # # # # #                     """
# # # # # #                     INSERT INTO users (
# # # # # #                         id, full_name, email, mobile, country, city, pincode,
# # # # # #                         gender, want_to, password_hash, lat, lng
# # # # # #                     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
# # # # # #                     """
# # # # # #                 ).bind(
# # # # # #                     user_id,
# # # # # #                     full_name,
# # # # # #                     email,
# # # # # #                     mobile,
# # # # # #                     country,
# # # # # #                     city,
# # # # # #                     pincode,
# # # # # #                     gender,
# # # # # #                     want_to,
# # # # # #                     secrets.token_hex(16),
# # # # # #                     data.lat,
# # # # # #                     data.lng,
# # # # # #                 ).run()
# # # # # #             except Exception as e:
# # # # # #                 msg = str(e).lower()
# # # # # #                 if "unique" in msg or "constraint" in msg:
# # # # # #                     if "email" in msg:
# # # # # #                         raise HTTPException(
# # # # # #                             status_code=409,
# # # # # #                             detail="Email already registered. Use another email or login.",
# # # # # #                         )
# # # # # #                     if "mobile" in msg:
# # # # # #                         raise HTTPException(
# # # # # #                             status_code=409,
# # # # # #                             detail="Mobile already registered. Please login.",
# # # # # #                         )
# # # # # #                     raise HTTPException(
# # # # # #                         status_code=409,
# # # # # #                         detail="Account already exists. Please login.",
# # # # # #                     )
# # # # # #                 raise HTTPException(
# # # # # #                     status_code=500,
# # # # # #                     detail=f"Signup failed: {type(e).__name__}: {e}",
# # # # # #                 )
# # # # # #
# # # # # #             user = await db.prepare(
# # # # # #                 "SELECT * FROM users WHERE id = ?"
# # # # # #             ).bind(user_id).first()
# # # # # #             if not user:
# # # # # #                 raise HTTPException(
# # # # # #                     status_code=500,
# # # # # #                     detail="Signup failed: user not found after insert",
# # # # # #                 )
# # # # # #             u = dict(user)
# # # # # #
# # # # # #         token = create_access_token({"sub": u["id"]})
# # # # # #         return {
# # # # # #             "access_token": token,
# # # # # #             "token": token,
# # # # # #             "token_type": "bearer",
# # # # # #             "user": {
# # # # # #                 "id": u["id"],
# # # # # #                 "account_id": u["id"],
# # # # # #                 "fullName": u.get("full_name"),
# # # # # #                 "name": u.get("full_name"),
# # # # # #                 "email": u.get("email"),
# # # # # #                 "mobile": u.get("mobile"),
# # # # # #                 "want_to": u.get("want_to"),
# # # # # #                 "role": u.get("want_to"),
# # # # # #                 "city": u.get("city"),
# # # # # #             },
# # # # # #         }
# # # # # #     except HTTPException:
# # # # # #         raise
# # # # # #     except Exception as e:
# # # # # #         raise HTTPException(
# # # # # #             status_code=500,
# # # # # #             detail=f"Verify failed: {type(e).__name__}: {e}",
# # # # # #         )
# # # # #
# # # # # from fastapi import APIRouter, Request, HTTPException
# # # # # from pydantic import BaseModel, Field
# # # # # from typing import Optional, Literal
# # # # # import secrets
# # # # # import hashlib
# # # # # import hmac
# # # # # import re
# # # # # from datetime import datetime, timedelta
# # # # # from utils.security import create_access_token
# # # # #
# # # # # router = APIRouter()
# # # # #
# # # # # OTP_TTL_SEC = 300
# # # # # OTP_MAX_ATTEMPTS = 5
# # # # #
# # # # # NO_PARAM_TEMPLATES = {"hello_world", "hello world"}
# # # # #
# # # # # AUTH_OTP_TEMPLATES = {
# # # # #     "login_otp",
# # # # #     "logn_otp",
# # # # #     "signup_verification_otp",
# # # # #     "verify_code",
# # # # #     "verify_code_1",
# # # # #     "authentication_code",
# # # # #     "otp_verification",
# # # # # }
# # # # #
# # # # #
# # # # # class OtpSendRequest(BaseModel):
# # # # #     mobile: str = Field(..., min_length=10, max_length=16)
# # # # #     purpose: Literal["login", "signup"] = "login"
# # # # #
# # # # #
# # # # # class OtpVerifyRequest(BaseModel):
# # # # #     mobile: str
# # # # #     otp: str = Field(..., min_length=4, max_length=8)
# # # # #     purpose: Literal["login", "signup"] = "login"
# # # # #     fullName: Optional[str] = None
# # # # #     name: Optional[str] = None
# # # # #     email: Optional[str] = None
# # # # #     country: Optional[str] = "India"
# # # # #     city: Optional[str] = None
# # # # #     pincode: Optional[str] = None
# # # # #     gender: Optional[str] = None
# # # # #     want_to: Optional[Literal["finder", "companion"]] = "finder"
# # # # #     lat: Optional[float] = None
# # # # #     lng: Optional[float] = None
# # # # #
# # # # #
# # # # # def _normalize_mobile(raw: str) -> str:
# # # # #     s = re.sub(r"[^\d+]", "", (raw or "").strip())
# # # # #     if s.startswith("00"):
# # # # #         s = "+" + s[2:]
# # # # #     if not s.startswith("+"):
# # # # #         digits = re.sub(r"\D", "", s)
# # # # #         if len(digits) == 10:
# # # # #             s = "+91" + digits
# # # # #         else:
# # # # #             s = "+" + digits
# # # # #     return s
# # # # #
# # # # #
# # # # # def _hash_otp(code: str, salt: str) -> str:
# # # # #     return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()
# # # # #
# # # # #
# # # # # def _digits_only(mobile: str) -> str:
# # # # #     return re.sub(r"\D", "", mobile or "")
# # # # #
# # # # #
# # # # # async def _http_json(
# # # # #     method: str,
# # # # #     url: str,
# # # # #     headers: dict,
# # # # #     body: dict | None = None,
# # # # # ) -> tuple[int, dict]:
# # # # #     import json as _json
# # # # #
# # # # #     payload = _json.dumps(body) if body is not None else None
# # # # #
# # # # #     try:
# # # # #         from js import fetch, Object
# # # # #         from pyodide.ffi import to_js
# # # # #
# # # # #         opts = {"method": method, "headers": headers}
# # # # #         if payload is not None:
# # # # #             opts["body"] = payload
# # # # #         resp = await fetch(url, to_js(opts, dict_converter=Object.fromEntries))
# # # # #         text = await resp.text()
# # # # #         code = int(resp.status)
# # # # #         try:
# # # # #             data = _json.loads(text) if text else {}
# # # # #         except Exception:
# # # # #             data = {"message": text}
# # # # #         return code, data
# # # # #     except Exception:
# # # # #         pass
# # # # #
# # # # #     import urllib.request
# # # # #     import urllib.error
# # # # #
# # # # #     data_bytes = payload.encode("utf-8") if payload else None
# # # # #     req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
# # # # #     try:
# # # # #         with urllib.request.urlopen(req, timeout=30) as resp:
# # # # #             text = resp.read().decode("utf-8")
# # # # #             return resp.status, (_json.loads(text) if text else {})
# # # # #     except urllib.error.HTTPError as e:
# # # # #         text = e.read().decode("utf-8")
# # # # #         try:
# # # # #             data = _json.loads(text) if text else {}
# # # # #         except Exception:
# # # # #             data = {"message": text}
# # # # #         return int(e.code), data
# # # # #     except Exception as e:
# # # # #         raise HTTPException(status_code=502, detail=f"WhatsApp request failed: {e}")
# # # # #
# # # # #
# # # # # def _build_auth_otp_template(name: str, lang: str, code: str) -> dict:
# # # # #     return {
# # # # #         "name": name,
# # # # #         "language": {"code": lang},
# # # # #         "components": [
# # # # #             {
# # # # #                 "type": "body",
# # # # #                 "parameters": [{"type": "text", "text": str(code)}],
# # # # #             },
# # # # #             {
# # # # #                 "type": "button",
# # # # #                 "sub_type": "url",
# # # # #                 "index": "0",
# # # # #                 "parameters": [{"type": "text", "text": str(code)}],
# # # # #             },
# # # # #         ],
# # # # #     }
# # # # #
# # # # #
# # # # # async def _send_whatsapp_otp(request: Request, mobile: str, code: str):
# # # # #     env = request.scope["env"]
# # # # #     token = (getattr(env, "WHATSAPP_TOKEN", None) or "").strip()
# # # # #     phone_id = (getattr(env, "WHATSAPP_PHONE_NUMBER_ID", None) or "").strip()
# # # # #     template = (
# # # # #         getattr(env, "WHATSAPP_OTP_TEMPLATE", None) or "signup_verification_otp"
# # # # #     ).strip()
# # # # #     lang = (getattr(env, "WHATSAPP_OTP_LANG", None) or "en").strip()
# # # # #
# # # # #     if not token or not phone_id:
# # # # #         raise HTTPException(status_code=500, detail="WhatsApp not configured")
# # # # #
# # # # #     url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
# # # # #     headers = {
# # # # #         "Authorization": f"Bearer {token}",
# # # # #         "Content-Type": "application/json",
# # # # #     }
# # # # #     to = _digits_only(mobile)
# # # # #     t_lower = template.lower().replace("-", "_")
# # # # #
# # # # #     if t_lower in NO_PARAM_TEMPLATES:
# # # # #         template_obj = {
# # # # #             "name": "hello_world",
# # # # #             "language": {"code": lang or "en"},
# # # # #         }
# # # # #     elif t_lower in AUTH_OTP_TEMPLATES or t_lower.endswith("_otp") or "otp" in t_lower:
# # # # #         template_obj = _build_auth_otp_template(template, lang, code)
# # # # #     elif template:
# # # # #         template_obj = {
# # # # #             "name": template,
# # # # #             "language": {"code": lang},
# # # # #             "components": [
# # # # #                 {
# # # # #                     "type": "body",
# # # # #                     "parameters": [{"type": "text", "text": str(code)}],
# # # # #                 }
# # # # #             ],
# # # # #         }
# # # # #     else:
# # # # #         body = {
# # # # #             "messaging_product": "whatsapp",
# # # # #             "to": to,
# # # # #             "type": "text",
# # # # #             "text": {
# # # # #                 "body": f"Your verification code is {code}. Valid for 5 minutes.",
# # # # #             },
# # # # #         }
# # # # #         code_http, data = await _http_json("POST", url, headers, body)
# # # # #         if code_http >= 400:
# # # # #             err = (data.get("error") if isinstance(data, dict) else None) or data
# # # # #             msg = err.get("message") if isinstance(err, dict) else str(data)
# # # # #             raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
# # # # #         return data
# # # # #
# # # # #     body = {
# # # # #         "messaging_product": "whatsapp",
# # # # #         "recipient_type": "individual",
# # # # #         "to": to,
# # # # #         "type": "template",
# # # # #         "template": template_obj,
# # # # #     }
# # # # #
# # # # #     code_http, data = await _http_json("POST", url, headers, body)
# # # # #     if code_http >= 400:
# # # # #         err = {}
# # # # #         if isinstance(data, dict):
# # # # #             err = data.get("error") or data
# # # # #         msg = err.get("message") if isinstance(err, dict) else str(data)
# # # # #         if (
# # # # #             code_http >= 400
# # # # #             and isinstance(err, dict)
# # # # #             and template_obj.get("components")
# # # # #             and len(template_obj["components"]) > 1
# # # # #         ):
# # # # #             template_obj = {
# # # # #                 "name": template_obj["name"],
# # # # #                 "language": template_obj["language"],
# # # # #                 "components": [
# # # # #                     {
# # # # #                         "type": "body",
# # # # #                         "parameters": [{"type": "text", "text": str(code)}],
# # # # #                     }
# # # # #                 ],
# # # # #             }
# # # # #             body["template"] = template_obj
# # # # #             code_http, data = await _http_json("POST", url, headers, body)
# # # # #             if code_http < 400:
# # # # #                 return data
# # # # #             err = (data.get("error") if isinstance(data, dict) else None) or data
# # # # #             msg = err.get("message") if isinstance(err, dict) else str(data)
# # # # #         raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
# # # # #     return data
# # # # #
# # # # #
# # # # # @router.post("/auth/otp/send")
# # # # # async def otp_send(data: OtpSendRequest, request: Request):
# # # # #     db = request.scope["env"].DB
# # # # #     mobile = _normalize_mobile(data.mobile)
# # # # #     purpose = data.purpose
# # # # #
# # # # #     user = await db.prepare(
# # # # #         "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
# # # # #     ).bind(mobile, mobile.lstrip("+")).first()
# # # # #
# # # # #     if purpose == "login" and not user:
# # # # #         raise HTTPException(
# # # # #             status_code=404,
# # # # #             detail="No account with this mobile. Please sign up.",
# # # # #         )
# # # # #     if purpose == "signup" and user:
# # # # #         raise HTTPException(
# # # # #             status_code=409,
# # # # #             detail="Mobile already registered. Please login.",
# # # # #         )
# # # # #
# # # # #     code = f"{secrets.randbelow(10**6):06d}"
# # # # #     salt = secrets.token_hex(8)
# # # # #     code_hash = _hash_otp(code, salt)
# # # # #     expires = (datetime.utcnow() + timedelta(seconds=OTP_TTL_SEC)).isoformat()
# # # # #     otp_id = secrets.token_hex(8)
# # # # #
# # # # #     await db.prepare(
# # # # #         """
# # # # #         UPDATE otp_codes SET consumed = 1
# # # # #         WHERE mobile = ? AND purpose = ? AND consumed = 0
# # # # #         """
# # # # #     ).bind(mobile, purpose).run()
# # # # #
# # # # #     await db.prepare(
# # # # #         """
# # # # #         INSERT INTO otp_codes (id, mobile, purpose, code_hash, expires_at, attempts, consumed)
# # # # #         VALUES (?, ?, ?, ?, ?, 0, 0)
# # # # #         """
# # # # #     ).bind(otp_id, mobile, purpose, f"{salt}:{code_hash}", expires).run()
# # # # #
# # # # #     await _send_whatsapp_otp(request, mobile, code)
# # # # #
# # # # #     return {
# # # # #         "message": "OTP sent on WhatsApp",
# # # # #         "mobile": mobile,
# # # # #         "purpose": purpose,
# # # # #         "expires_in": OTP_TTL_SEC,
# # # # #     }
# # # # #
# # # # #
# # # # # @router.post("/auth/otp/verify")
# # # # # async def otp_verify(data: OtpVerifyRequest, request: Request):
# # # # #     db = request.scope["env"].DB
# # # # #     mobile = _normalize_mobile(data.mobile)
# # # # #     purpose = data.purpose
# # # # #     otp = (data.otp or "").strip()
# # # # #
# # # # #     row = await db.prepare(
# # # # #         """
# # # # #         SELECT * FROM otp_codes
# # # # #         WHERE mobile = ? AND purpose = ? AND consumed = 0
# # # # #         ORDER BY created_at DESC LIMIT 1
# # # # #         """
# # # # #     ).bind(mobile, purpose).first()
# # # # #     if not row:
# # # # #         raise HTTPException(
# # # # #             status_code=400,
# # # # #             detail="OTP expired or not found. Request a new one.",
# # # # #         )
# # # # #
# # # # #     r = dict(row)
# # # # #     if int(r.get("attempts") or 0) >= OTP_MAX_ATTEMPTS:
# # # # #         raise HTTPException(
# # # # #             status_code=429,
# # # # #             detail="Too many attempts. Request a new OTP.",
# # # # #         )
# # # # #
# # # # #     try:
# # # # #         exp = datetime.fromisoformat(str(r["expires_at"]).replace("Z", ""))
# # # # #     except Exception:
# # # # #         raise HTTPException(status_code=400, detail="OTP expired. Request a new one.")
# # # # #
# # # # #     if datetime.utcnow() > exp:
# # # # #         raise HTTPException(
# # # # #             status_code=400,
# # # # #             detail="OTP expired. Request a new one.",
# # # # #         )
# # # # #
# # # # #     try:
# # # # #         salt, stored_hash = str(r["code_hash"]).split(":", 1)
# # # # #     except Exception:
# # # # #         raise HTTPException(
# # # # #             status_code=400,
# # # # #             detail="Invalid OTP record. Request a new one.",
# # # # #         )
# # # # #
# # # # #     if not hmac.compare_digest(_hash_otp(otp, salt), stored_hash):
# # # # #         await db.prepare(
# # # # #             "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ?"
# # # # #         ).bind(r["id"]).run()
# # # # #         raise HTTPException(status_code=400, detail="Invalid OTP")
# # # # #
# # # # #     await db.prepare(
# # # # #         "UPDATE otp_codes SET consumed = 1 WHERE id = ?"
# # # # #     ).bind(r["id"]).run()
# # # # #
# # # # #     try:
# # # # #         if purpose == "login":
# # # # #             user = await db.prepare(
# # # # #                 "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
# # # # #             ).bind(mobile, mobile.lstrip("+")).first()
# # # # #             if not user:
# # # # #                 raise HTTPException(status_code=404, detail="User not found")
# # # # #             u = dict(user)
# # # # #         else:
# # # # #             existing = await db.prepare(
# # # # #                 "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
# # # # #             ).bind(mobile, mobile.lstrip("+")).first()
# # # # #             if existing:
# # # # #                 raise HTTPException(
# # # # #                     status_code=409,
# # # # #                     detail="Mobile already registered. Please login.",
# # # # #                 )
# # # # #
# # # # #             full_name = (data.fullName or data.name or "User").strip() or "User"
# # # # #             user_id = secrets.token_hex(4).upper()
# # # # #             digits = _digits_only(mobile)
# # # # #             email = (data.email or f"{digits}@otp.local").strip()
# # # # #             want_to = data.want_to or "finder"
# # # # #             gender = (data.gender or "").strip()
# # # # #             city = (data.city or "").strip()
# # # # #             pincode = (data.pincode or "").strip()
# # # # #             country = (data.country or "India").strip()
# # # # #
# # # # #             if email and not email.endswith("@otp.local"):
# # # # #                 em = await db.prepare(
# # # # #                     "SELECT id FROM users WHERE LOWER(email) = LOWER(?)"
# # # # #                 ).bind(email).first()
# # # # #                 if em:
# # # # #                     raise HTTPException(
# # # # #                         status_code=409,
# # # # #                         detail="Email already registered. Use another email or login.",
# # # # #                     )
# # # # #
# # # # #             try:
# # # # #                 await db.prepare(
# # # # #                     """
# # # # #                     INSERT INTO users (
# # # # #                         id, full_name, email, mobile, country, city, pincode,
# # # # #                         gender, want_to, lat, lng
# # # # #                     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
# # # # #                     """
# # # # #                 ).bind(
# # # # #                     user_id,
# # # # #                     full_name,
# # # # #                     email,
# # # # #                     mobile,
# # # # #                     country,
# # # # #                     city,
# # # # #                     pincode,
# # # # #                     gender,
# # # # #                     want_to,
# # # # #                     data.lat,
# # # # #                     data.lng,
# # # # #                 ).run()
# # # # #             except Exception as e:
# # # # #                 msg = str(e).lower()
# # # # #                 if "unique" in msg or "constraint" in msg:
# # # # #                     if "email" in msg:
# # # # #                         raise HTTPException(
# # # # #                             status_code=409,
# # # # #                             detail="Email already registered. Use another email or login.",
# # # # #                         )
# # # # #                     if "mobile" in msg:
# # # # #                         raise HTTPException(
# # # # #                             status_code=409,
# # # # #                             detail="Mobile already registered. Please login.",
# # # # #                         )
# # # # #                     raise HTTPException(
# # # # #                         status_code=409,
# # # # #                         detail="Account already exists. Please login.",
# # # # #                     )
# # # # #                 raise HTTPException(
# # # # #                     status_code=500,
# # # # #                     detail=f"Signup failed: {type(e).__name__}: {e}",
# # # # #                 )
# # # # #
# # # # #             user = await db.prepare(
# # # # #                 "SELECT * FROM users WHERE id = ?"
# # # # #             ).bind(user_id).first()
# # # # #             if not user:
# # # # #                 raise HTTPException(
# # # # #                     status_code=500,
# # # # #                     detail="Signup failed: user not found after insert",
# # # # #                 )
# # # # #             u = dict(user)
# # # # #
# # # # #         token = create_access_token({"sub": u["id"]})
# # # # #         return {
# # # # #             "access_token": token,
# # # # #             "token": token,
# # # # #             "token_type": "bearer",
# # # # #             "user": {
# # # # #                 "id": u["id"],
# # # # #                 "account_id": u["id"],
# # # # #                 "fullName": u.get("full_name"),
# # # # #                 "name": u.get("full_name"),
# # # # #                 "email": u.get("email"),
# # # # #                 "mobile": u.get("mobile"),
# # # # #                 "want_to": u.get("want_to"),
# # # # #                 "role": u.get("want_to"),
# # # # #                 "city": u.get("city"),
# # # # #             },
# # # # #         }
# # # # #     except HTTPException:
# # # # #         raise
# # # # #     except Exception as e:
# # # # #         raise HTTPException(
# # # # #             status_code=500,
# # # # #             detail=f"Verify failed: {type(e).__name__}: {e}",
# # # # #         )
# # # #
# # # #
# # # # from fastapi import APIRouter, Request, HTTPException
# # # # from pydantic import BaseModel, Field
# # # # from typing import Optional, Literal
# # # # import secrets
# # # # import hashlib
# # # # import hmac
# # # # import re
# # # # from datetime import datetime, timedelta
# # # # from utils.security import create_access_token
# # # #
# # # # router = APIRouter()
# # # #
# # # # OTP_TTL_SEC = 300
# # # # OTP_MAX_ATTEMPTS = 5
# # # #
# # # # NO_PARAM_TEMPLATES = {"hello_world", "hello world"}
# # # #
# # # # AUTH_OTP_TEMPLATES = {
# # # #     "login_otp",
# # # #     "logn_otp",
# # # #     "signup_verification_otp",
# # # #     "verify_code",
# # # #     "verify_code_1",
# # # #     "authentication_code",
# # # #     "otp_verification",
# # # # }
# # # #
# # # #
# # # # class OtpSendRequest(BaseModel):
# # # #     mobile: str = Field(..., min_length=10, max_length=16)
# # # #     purpose: Literal["login", "signup"] = "login"
# # # #
# # # #
# # # # class OtpVerifyRequest(BaseModel):
# # # #     mobile: str
# # # #     otp: str = Field(..., min_length=4, max_length=8)
# # # #     purpose: Literal["login", "signup"] = "login"
# # # #     fullName: Optional[str] = None
# # # #     name: Optional[str] = None
# # # #     email: Optional[str] = None
# # # #     country: Optional[str] = "India"
# # # #     city: Optional[str] = None
# # # #     pincode: Optional[str] = None
# # # #     gender: Optional[str] = None
# # # #     want_to: Optional[Literal["finder", "companion"]] = "finder"
# # # #     lat: Optional[float] = None
# # # #     lng: Optional[float] = None
# # # #
# # # #
# # # # def _normalize_mobile(raw: str) -> str:
# # # #     s = re.sub(r"[^\d+]", "", (raw or "").strip())
# # # #     if s.startswith("00"):
# # # #         s = "+" + s[2:]
# # # #     if not s.startswith("+"):
# # # #         digits = re.sub(r"\D", "", s)
# # # #         if len(digits) == 10:
# # # #             s = "+91" + digits
# # # #         else:
# # # #             s = "+" + digits
# # # #     return s
# # # #
# # # #
# # # # def _digits_only(mobile: str) -> str:
# # # #     return re.sub(r"\D", "", mobile or "")
# # # #
# # # #
# # # # def _mobile_variants(raw: str) -> list[str]:
# # # #     """All forms we might have stored for the same Indian mobile."""
# # # #     mobile = _normalize_mobile(raw)
# # # #     digits = _digits_only(mobile)
# # # #     last10 = digits[-10:] if len(digits) >= 10 else digits
# # # #     variants = {mobile, digits, last10, f"+{digits}"}
# # # #     if digits.startswith("91") and len(digits) >= 12:
# # # #         variants.add(digits[2:])
# # # #     return [v for v in variants if v]
# # # #
# # # #
# # # # async def _find_user_by_mobile(db, raw: str):
# # # #     variants = _mobile_variants(raw)
# # # #     if not variants:
# # # #         return None
# # # #     placeholders = ", ".join("?" for _ in variants)
# # # #     return await db.prepare(
# # # #         f"SELECT * FROM users WHERE mobile IN ({placeholders}) LIMIT 1"
# # # #     ).bind(*variants).first()
# # # #
# # # #
# # # # async def _find_user_id_by_mobile(db, raw: str):
# # # #     variants = _mobile_variants(raw)
# # # #     if not variants:
# # # #         return None
# # # #     placeholders = ", ".join("?" for _ in variants)
# # # #     return await db.prepare(
# # # #         f"SELECT id FROM users WHERE mobile IN ({placeholders}) LIMIT 1"
# # # #     ).bind(*variants).first()
# # # #
# # # #
# # # # def _hash_otp(code: str, salt: str) -> str:
# # # #     return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()
# # # #
# # # #
# # # # def _random_password_placeholder() -> str:
# # # #     """
# # # #     users.password is NOT NULL. OTP accounts never use this for login.
# # # #     Prefer your real hasher if you have one, e.g. hash_password(secrets.token_urlsafe(32)).
# # # #     """
# # # #     try:
# # # #         from utils.security import hash_password
# # # #
# # # #         return hash_password(secrets.token_urlsafe(32))
# # # #     except Exception:
# # # #         return hashlib.sha256(secrets.token_hex(32).encode()).hexdigest()
# # # #
# # # #
# # # # async def _http_json(
# # # #     method: str,
# # # #     url: str,
# # # #     headers: dict,
# # # #     body: dict | None = None,
# # # # ) -> tuple[int, dict]:
# # # #     import json as _json
# # # #
# # # #     payload = _json.dumps(body) if body is not None else None
# # # #
# # # #     try:
# # # #         from js import fetch, Object
# # # #         from pyodide.ffi import to_js
# # # #
# # # #         opts = {"method": method, "headers": headers}
# # # #         if payload is not None:
# # # #             opts["body"] = payload
# # # #         resp = await fetch(url, to_js(opts, dict_converter=Object.fromEntries))
# # # #         text = await resp.text()
# # # #         code = int(resp.status)
# # # #         try:
# # # #             data = _json.loads(text) if text else {}
# # # #         except Exception:
# # # #             data = {"message": text}
# # # #         return code, data
# # # #     except Exception:
# # # #         pass
# # # #
# # # #     import urllib.request
# # # #     import urllib.error
# # # #
# # # #     data_bytes = payload.encode("utf-8") if payload else None
# # # #     req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
# # # #     try:
# # # #         with urllib.request.urlopen(req, timeout=30) as resp:
# # # #             text = resp.read().decode("utf-8")
# # # #             return resp.status, (_json.loads(text) if text else {})
# # # #     except urllib.error.HTTPError as e:
# # # #         text = e.read().decode("utf-8")
# # # #         try:
# # # #             data = _json.loads(text) if text else {}
# # # #         except Exception:
# # # #             data = {"message": text}
# # # #         return int(e.code), data
# # # #     except Exception as e:
# # # #         raise HTTPException(status_code=502, detail=f"WhatsApp request failed: {e}")
# # # #
# # # #
# # # # def _build_auth_otp_template(name: str, lang: str, code: str) -> dict:
# # # #     return {
# # # #         "name": name,
# # # #         "language": {"code": lang},
# # # #         "components": [
# # # #             {
# # # #                 "type": "body",
# # # #                 "parameters": [{"type": "text", "text": str(code)}],
# # # #             },
# # # #             {
# # # #                 "type": "button",
# # # #                 "sub_type": "url",
# # # #                 "index": "0",
# # # #                 "parameters": [{"type": "text", "text": str(code)}],
# # # #             },
# # # #         ],
# # # #     }
# # # #
# # # #
# # # # async def _send_whatsapp_otp(request: Request, mobile: str, code: str):
# # # #     env = request.scope["env"]
# # # #     token = (getattr(env, "WHATSAPP_TOKEN", None) or "").strip()
# # # #     phone_id = (getattr(env, "WHATSAPP_PHONE_NUMBER_ID", None) or "").strip()
# # # #     template = (
# # # #         getattr(env, "WHATSAPP_OTP_TEMPLATE", None) or "signup_verification_otp"
# # # #     ).strip()
# # # #     lang = (getattr(env, "WHATSAPP_OTP_LANG", None) or "en").strip()
# # # #
# # # #     if not token or not phone_id:
# # # #         raise HTTPException(status_code=500, detail="WhatsApp not configured")
# # # #
# # # #     url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
# # # #     headers = {
# # # #         "Authorization": f"Bearer {token}",
# # # #         "Content-Type": "application/json",
# # # #     }
# # # #     to = _digits_only(mobile)
# # # #     t_lower = template.lower().replace("-", "_")
# # # #
# # # #     if t_lower in NO_PARAM_TEMPLATES:
# # # #         template_obj = {
# # # #             "name": "hello_world",
# # # #             "language": {"code": lang or "en"},
# # # #         }
# # # #     elif t_lower in AUTH_OTP_TEMPLATES or t_lower.endswith("_otp") or "otp" in t_lower:
# # # #         template_obj = _build_auth_otp_template(template, lang, code)
# # # #     elif template:
# # # #         template_obj = {
# # # #             "name": template,
# # # #             "language": {"code": lang},
# # # #             "components": [
# # # #                 {
# # # #                     "type": "body",
# # # #                     "parameters": [{"type": "text", "text": str(code)}],
# # # #                 }
# # # #             ],
# # # #         }
# # # #     else:
# # # #         body = {
# # # #             "messaging_product": "whatsapp",
# # # #             "to": to,
# # # #             "type": "text",
# # # #             "text": {
# # # #                 "body": f"Your verification code is {code}. Valid for 5 minutes.",
# # # #             },
# # # #         }
# # # #         code_http, data = await _http_json("POST", url, headers, body)
# # # #         if code_http >= 400:
# # # #             err = (data.get("error") if isinstance(data, dict) else None) or data
# # # #             msg = err.get("message") if isinstance(err, dict) else str(data)
# # # #             raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
# # # #         return data
# # # #
# # # #     body = {
# # # #         "messaging_product": "whatsapp",
# # # #         "recipient_type": "individual",
# # # #         "to": to,
# # # #         "type": "template",
# # # #         "template": template_obj,
# # # #     }
# # # #
# # # #     code_http, data = await _http_json("POST", url, headers, body)
# # # #     if code_http >= 400:
# # # #         err = {}
# # # #         if isinstance(data, dict):
# # # #             err = data.get("error") or data
# # # #         msg = err.get("message") if isinstance(err, dict) else str(data)
# # # #         if (
# # # #             code_http >= 400
# # # #             and isinstance(err, dict)
# # # #             and template_obj.get("components")
# # # #             and len(template_obj["components"]) > 1
# # # #         ):
# # # #             template_obj = {
# # # #                 "name": template_obj["name"],
# # # #                 "language": template_obj["language"],
# # # #                 "components": [
# # # #                     {
# # # #                         "type": "body",
# # # #                         "parameters": [{"type": "text", "text": str(code)}],
# # # #                     }
# # # #                 ],
# # # #             }
# # # #             body["template"] = template_obj
# # # #             code_http, data = await _http_json("POST", url, headers, body)
# # # #             if code_http < 400:
# # # #                 return data
# # # #             err = (data.get("error") if isinstance(data, dict) else None) or data
# # # #             msg = err.get("message") if isinstance(err, dict) else str(data)
# # # #         raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
# # # #     return data
# # # #
# # # #
# # # # @router.post("/auth/otp/send")
# # # # async def otp_send(data: OtpSendRequest, request: Request):
# # # #     db = request.scope["env"].DB
# # # #     mobile = _normalize_mobile(data.mobile)
# # # #     purpose = data.purpose
# # # #
# # # #     user = await _find_user_id_by_mobile(db, mobile)
# # # #
# # # #     if purpose == "login" and not user:
# # # #         raise HTTPException(
# # # #             status_code=404,
# # # #             detail="No account with this mobile. Please sign up.",
# # # #         )
# # # #     if purpose == "signup" and user:
# # # #         raise HTTPException(
# # # #             status_code=409,
# # # #             detail="Mobile already registered. Please login.",
# # # #         )
# # # #
# # # #     code = f"{secrets.randbelow(10**6):06d}"
# # # #     salt = secrets.token_hex(8)
# # # #     code_hash = _hash_otp(code, salt)
# # # #     expires = (datetime.utcnow() + timedelta(seconds=OTP_TTL_SEC)).isoformat()
# # # #     otp_id = secrets.token_hex(8)
# # # #
# # # #     await db.prepare(
# # # #         """
# # # #         UPDATE otp_codes SET consumed = 1
# # # #         WHERE mobile = ? AND purpose = ? AND consumed = 0
# # # #         """
# # # #     ).bind(mobile, purpose).run()
# # # #
# # # #     await db.prepare(
# # # #         """
# # # #         INSERT INTO otp_codes (id, mobile, purpose, code_hash, expires_at, attempts, consumed)
# # # #         VALUES (?, ?, ?, ?, ?, 0, 0)
# # # #         """
# # # #     ).bind(otp_id, mobile, purpose, f"{salt}:{code_hash}", expires).run()
# # # #
# # # #     await _send_whatsapp_otp(request, mobile, code)
# # # #
# # # #     return {
# # # #         "message": "OTP sent on WhatsApp",
# # # #         "mobile": mobile,
# # # #         "purpose": purpose,
# # # #         "expires_in": OTP_TTL_SEC,
# # # #     }
# # # #
# # # #
# # # # @router.post("/auth/otp/verify")
# # # # async def otp_verify(data: OtpVerifyRequest, request: Request):
# # # #     db = request.scope["env"].DB
# # # #     mobile = _normalize_mobile(data.mobile)
# # # #     purpose = data.purpose
# # # #     otp = (data.otp or "").strip()
# # # #
# # # #     row = await db.prepare(
# # # #         """
# # # #         SELECT * FROM otp_codes
# # # #         WHERE mobile = ? AND purpose = ? AND consumed = 0
# # # #         ORDER BY created_at DESC LIMIT 1
# # # #         """
# # # #     ).bind(mobile, purpose).first()
# # # #     if not row:
# # # #         raise HTTPException(
# # # #             status_code=400,
# # # #             detail="OTP expired or not found. Request a new one.",
# # # #         )
# # # #
# # # #     r = dict(row)
# # # #     if int(r.get("attempts") or 0) >= OTP_MAX_ATTEMPTS:
# # # #         raise HTTPException(
# # # #             status_code=429,
# # # #             detail="Too many attempts. Request a new OTP.",
# # # #         )
# # # #
# # # #     try:
# # # #         exp = datetime.fromisoformat(str(r["expires_at"]).replace("Z", ""))
# # # #     except Exception:
# # # #         raise HTTPException(status_code=400, detail="OTP expired. Request a new one.")
# # # #
# # # #     if datetime.utcnow() > exp:
# # # #         raise HTTPException(
# # # #             status_code=400,
# # # #             detail="OTP expired. Request a new one.",
# # # #         )
# # # #
# # # #     try:
# # # #         salt, stored_hash = str(r["code_hash"]).split(":", 1)
# # # #     except Exception:
# # # #         raise HTTPException(
# # # #             status_code=400,
# # # #             detail="Invalid OTP record. Request a new one.",
# # # #         )
# # # #
# # # #     if not hmac.compare_digest(_hash_otp(otp, salt), stored_hash):
# # # #         await db.prepare(
# # # #             "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ?"
# # # #         ).bind(r["id"]).run()
# # # #         raise HTTPException(status_code=400, detail="Invalid OTP")
# # # #
# # # #     await db.prepare(
# # # #         "UPDATE otp_codes SET consumed = 1 WHERE id = ?"
# # # #     ).bind(r["id"]).run()
# # # #
# # # #     try:
# # # #         if purpose == "login":
# # # #             user = await _find_user_by_mobile(db, mobile)
# # # #             if not user:
# # # #                 raise HTTPException(status_code=404, detail="User not found")
# # # #             u = dict(user)
# # # #         else:
# # # #             existing = await _find_user_id_by_mobile(db, mobile)
# # # #             if existing:
# # # #                 raise HTTPException(
# # # #                     status_code=409,
# # # #                     detail="Mobile already registered. Please login.",
# # # #                 )
# # # #
# # # #             full_name = (data.fullName or data.name or "User").strip() or "User"
# # # #             user_id = secrets.token_hex(8).upper()
# # # #             digits = _digits_only(mobile)
# # # #             email = (data.email or f"{digits}@otp.local").strip()
# # # #             want_to = data.want_to or "finder"
# # # #             gender = (data.gender or "").strip()
# # # #             city = (data.city or "").strip()
# # # #             pincode = (data.pincode or "").strip()
# # # #             country = (data.country or "India").strip()
# # # #             password_hash = _random_password_placeholder()
# # # #
# # # #             if email and not email.endswith("@otp.local"):
# # # #                 em = await db.prepare(
# # # #                     "SELECT id FROM users WHERE LOWER(email) = LOWER(?)"
# # # #                 ).bind(email).first()
# # # #                 if em:
# # # #                     raise HTTPException(
# # # #                         status_code=409,
# # # #                         detail="Email already registered. Use another email or login.",
# # # #                     )
# # # #
# # # #             try:
# # # #                 await db.prepare(
# # # #                     """
# # # #                     INSERT INTO users (
# # # #                         id, full_name, email, mobile, password, country, city, pincode,
# # # #                         gender, want_to, lat, lng
# # # #                     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
# # # #                     """
# # # #                 ).bind(
# # # #                     user_id,
# # # #                     full_name,
# # # #                     email,
# # # #                     mobile,
# # # #                     password_hash,
# # # #                     country,
# # # #                     city,
# # # #                     pincode,
# # # #                     gender,
# # # #                     want_to,
# # # #                     data.lat,
# # # #                     data.lng,
# # # #                 ).run()
# # # #             except Exception as e:
# # # #                 msg = str(e).lower()
# # # #                 print(f"[otp_verify] INSERT failed: {type(e).__name__}: {e}")
# # # #                 if "unique" in msg or "constraint" in msg:
# # # #                     if "email" in msg:
# # # #                         raise HTTPException(
# # # #                             status_code=409,
# # # #                             detail="Email already registered. Use another email or login.",
# # # #                         )
# # # #                     if "mobile" in msg:
# # # #                         raise HTTPException(
# # # #                             status_code=409,
# # # #                             detail="Mobile already registered. Please login.",
# # # #                         )
# # # #                     if "password" in msg or "not null" in msg:
# # # #                         raise HTTPException(
# # # #                             status_code=500,
# # # #                             detail=f"Signup schema error: {e}",
# # # #                         )
# # # #                     raise HTTPException(
# # # #                         status_code=409,
# # # #                         detail=f"Account conflict: {e}",
# # # #                     )
# # # #                 raise HTTPException(
# # # #                     status_code=500,
# # # #                     detail=f"Signup failed: {type(e).__name__}: {e}",
# # # #                 )
# # # #
# # # #             user = await db.prepare(
# # # #                 "SELECT * FROM users WHERE id = ?"
# # # #             ).bind(user_id).first()
# # # #             if not user:
# # # #                 raise HTTPException(
# # # #                     status_code=500,
# # # #                     detail="Signup failed: user not found after insert",
# # # #                 )
# # # #             u = dict(user)
# # # #
# # # #         token = create_access_token({"sub": u["id"]})
# # # #         return {
# # # #             "access_token": token,
# # # #             "token": token,
# # # #             "token_type": "bearer",
# # # #             "user": {
# # # #                 "id": u["id"],
# # # #                 "account_id": u["id"],
# # # #                 "fullName": u.get("full_name"),
# # # #                 "name": u.get("full_name"),
# # # #                 "email": u.get("email"),
# # # #                 "mobile": u.get("mobile"),
# # # #                 "want_to": u.get("want_to"),
# # # #                 "role": u.get("want_to"),
# # # #                 "city": u.get("city"),
# # # #             },
# # # #         }
# # # #     except HTTPException:
# # # #         raise
# # # #     except Exception as e:
# # # #         raise HTTPException(
# # # #             status_code=500,
# # # #             detail=f"Verify failed: {type(e).__name__}: {e}",
# # # #         )
# # #
# # #
# # # from fastapi import APIRouter, Request, HTTPException
# # # from pydantic import BaseModel, Field
# # # from typing import Optional, Literal
# # # import secrets
# # # import hashlib
# # # import hmac
# # # import re
# # # from datetime import datetime, timedelta
# # # from utils.security import create_access_token
# # #
# # # router = APIRouter()
# # #
# # # OTP_TTL_SEC = 300
# # # OTP_MAX_ATTEMPTS = 5
# # #
# # # NO_PARAM_TEMPLATES = {"hello_world", "hello world"}
# # #
# # # AUTH_OTP_TEMPLATES = {
# # #     "login_otp",
# # #     "logn_otp",
# # #     "signup_verification_otp",
# # #     "verify_code",
# # #     "verify_code_1",
# # #     "authentication_code",
# # #     "otp_verification",
# # # }
# # #
# # #
# # # class OtpSendRequest(BaseModel):
# # #     mobile: str = Field(..., min_length=10, max_length=16)
# # #     purpose: Literal["login", "signup"] = "login"
# # #
# # #
# # # class OtpVerifyRequest(BaseModel):
# # #     mobile: str
# # #     otp: str = Field(..., min_length=4, max_length=8)
# # #     purpose: Literal["login", "signup"] = "login"
# # #     fullName: Optional[str] = None
# # #     name: Optional[str] = None
# # #     email: Optional[str] = None
# # #     password: Optional[str] = None  # from Flutter register form
# # #     country: Optional[str] = "India"
# # #     city: Optional[str] = None
# # #     pincode: Optional[str] = None
# # #     gender: Optional[str] = None
# # #     want_to: Optional[Literal["finder", "companion"]] = "finder"
# # #     lat: Optional[float] = None
# # #     lng: Optional[float] = None
# # #
# # #
# # # def _normalize_mobile(raw: str) -> str:
# # #     s = re.sub(r"[^\d+]", "", (raw or "").strip())
# # #     if s.startswith("00"):
# # #         s = "+" + s[2:]
# # #     if not s.startswith("+"):
# # #         digits = re.sub(r"\D", "", s)
# # #         if len(digits) == 10:
# # #             s = "+91" + digits
# # #         else:
# # #             s = "+" + digits
# # #     return s
# # #
# # #
# # # def _digits_only(mobile: str) -> str:
# # #     return re.sub(r"\D", "", mobile or "")
# # #
# # #
# # # def _mobile_variants(raw: str) -> list[str]:
# # #     mobile = _normalize_mobile(raw)
# # #     digits = _digits_only(mobile)
# # #     last10 = digits[-10:] if len(digits) >= 10 else digits
# # #     variants = {mobile, digits, last10, f"+{digits}"}
# # #     if digits.startswith("91") and len(digits) >= 12:
# # #         variants.add(digits[2:])
# # #     return [v for v in variants if v]
# # #
# # #
# # # async def _find_user_by_mobile(db, raw: str):
# # #     variants = _mobile_variants(raw)
# # #     if not variants:
# # #         return None
# # #     placeholders = ", ".join("?" for _ in variants)
# # #     return await db.prepare(
# # #         f"SELECT * FROM users WHERE mobile IN ({placeholders}) LIMIT 1"
# # #     ).bind(*variants).first()
# # #
# # #
# # # async def _find_user_id_by_mobile(db, raw: str):
# # #     variants = _mobile_variants(raw)
# # #     if not variants:
# # #         return None
# # #     placeholders = ", ".join("?" for _ in variants)
# # #     return await db.prepare(
# # #         f"SELECT id FROM users WHERE mobile IN ({placeholders}) LIMIT 1"
# # #     ).bind(*variants).first()
# # #
# # #
# # # def _hash_otp(code: str, salt: str) -> str:
# # #     return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()
# # #
# # #
# # # def _random_password_placeholder() -> str:
# # #     """Fallback when client does not send password (users.password is NOT NULL)."""
# # #     try:
# # #         from utils.security import hash_password
# # #
# # #         return hash_password(secrets.token_urlsafe(32))
# # #     except Exception:
# # #         return hashlib.sha256(secrets.token_hex(32).encode()).hexdigest()
# # #
# # #
# # # def _password_for_signup(plain: Optional[str]) -> str:
# # #     """Hash user password from app, or random placeholder."""
# # #     if plain and len(plain.strip()) >= 6:
# # #         try:
# # #             from utils.security import hash_password
# # #
# # #             return hash_password(plain.strip())
# # #         except Exception:
# # #             return hashlib.sha256(plain.strip().encode()).hexdigest()
# # #     return _random_password_placeholder()
# # #
# # #
# # # async def _http_json(
# # #     method: str,
# # #     url: str,
# # #     headers: dict,
# # #     body: dict | None = None,
# # # ) -> tuple[int, dict]:
# # #     import json as _json
# # #
# # #     payload = _json.dumps(body) if body is not None else None
# # #
# # #     try:
# # #         from js import fetch, Object
# # #         from pyodide.ffi import to_js
# # #
# # #         opts = {"method": method, "headers": headers}
# # #         if payload is not None:
# # #             opts["body"] = payload
# # #         resp = await fetch(url, to_js(opts, dict_converter=Object.fromEntries))
# # #         text = await resp.text()
# # #         code = int(resp.status)
# # #         try:
# # #             data = _json.loads(text) if text else {}
# # #         except Exception:
# # #             data = {"message": text}
# # #         return code, data
# # #     except Exception:
# # #         pass
# # #
# # #     import urllib.request
# # #     import urllib.error
# # #
# # #     data_bytes = payload.encode("utf-8") if payload else None
# # #     req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
# # #     try:
# # #         with urllib.request.urlopen(req, timeout=30) as resp:
# # #             text = resp.read().decode("utf-8")
# # #             return resp.status, (_json.loads(text) if text else {})
# # #     except urllib.error.HTTPError as e:
# # #         text = e.read().decode("utf-8")
# # #         try:
# # #             data = _json.loads(text) if text else {}
# # #         except Exception:
# # #             data = {"message": text}
# # #         return int(e.code), data
# # #     except Exception as e:
# # #         raise HTTPException(status_code=502, detail=f"WhatsApp request failed: {e}")
# # #
# # #
# # # def _build_auth_otp_template(name: str, lang: str, code: str) -> dict:
# # #     return {
# # #         "name": name,
# # #         "language": {"code": lang},
# # #         "components": [
# # #             {
# # #                 "type": "body",
# # #                 "parameters": [{"type": "text", "text": str(code)}],
# # #             },
# # #             {
# # #                 "type": "button",
# # #                 "sub_type": "url",
# # #                 "index": "0",
# # #                 "parameters": [{"type": "text", "text": str(code)}],
# # #             },
# # #         ],
# # #     }
# # #
# # #
# # # async def _send_whatsapp_otp(request: Request, mobile: str, code: str):
# # #     env = request.scope["env"]
# # #     token = (getattr(env, "WHATSAPP_TOKEN", None) or "").strip()
# # #     phone_id = (getattr(env, "WHATSAPP_PHONE_NUMBER_ID", None) or "").strip()
# # #     template = (
# # #         getattr(env, "WHATSAPP_OTP_TEMPLATE", None) or "signup_verification_otp"
# # #     ).strip()
# # #     lang = (getattr(env, "WHATSAPP_OTP_LANG", None) or "en").strip()
# # #
# # #     if not token or not phone_id:
# # #         raise HTTPException(status_code=500, detail="WhatsApp not configured")
# # #
# # #     url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
# # #     headers = {
# # #         "Authorization": f"Bearer {token}",
# # #         "Content-Type": "application/json",
# # #     }
# # #     to = _digits_only(mobile)
# # #     t_lower = template.lower().replace("-", "_")
# # #
# # #     if t_lower in NO_PARAM_TEMPLATES:
# # #         template_obj = {
# # #             "name": "hello_world",
# # #             "language": {"code": lang or "en"},
# # #         }
# # #     elif t_lower in AUTH_OTP_TEMPLATES or t_lower.endswith("_otp") or "otp" in t_lower:
# # #         template_obj = _build_auth_otp_template(template, lang, code)
# # #     elif template:
# # #         template_obj = {
# # #             "name": template,
# # #             "language": {"code": lang},
# # #             "components": [
# # #                 {
# # #                     "type": "body",
# # #                     "parameters": [{"type": "text", "text": str(code)}],
# # #                 }
# # #             ],
# # #         }
# # #     else:
# # #         body = {
# # #             "messaging_product": "whatsapp",
# # #             "to": to,
# # #             "type": "text",
# # #             "text": {
# # #                 "body": f"Your verification code is {code}. Valid for 5 minutes.",
# # #             },
# # #         }
# # #         code_http, data = await _http_json("POST", url, headers, body)
# # #         if code_http >= 400:
# # #             err = (data.get("error") if isinstance(data, dict) else None) or data
# # #             msg = err.get("message") if isinstance(err, dict) else str(data)
# # #             raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
# # #         return data
# # #
# # #     body = {
# # #         "messaging_product": "whatsapp",
# # #         "recipient_type": "individual",
# # #         "to": to,
# # #         "type": "template",
# # #         "template": template_obj,
# # #     }
# # #
# # #     code_http, data = await _http_json("POST", url, headers, body)
# # #     if code_http >= 400:
# # #         err = {}
# # #         if isinstance(data, dict):
# # #             err = data.get("error") or data
# # #         msg = err.get("message") if isinstance(err, dict) else str(data)
# # #         if (
# # #             code_http >= 400
# # #             and isinstance(err, dict)
# # #             and template_obj.get("components")
# # #             and len(template_obj["components"]) > 1
# # #         ):
# # #             template_obj = {
# # #                 "name": template_obj["name"],
# # #                 "language": template_obj["language"],
# # #                 "components": [
# # #                     {
# # #                         "type": "body",
# # #                         "parameters": [{"type": "text", "text": str(code)}],
# # #                     }
# # #                 ],
# # #             }
# # #             body["template"] = template_obj
# # #             code_http, data = await _http_json("POST", url, headers, body)
# # #             if code_http < 400:
# # #                 return data
# # #             err = (data.get("error") if isinstance(data, dict) else None) or data
# # #             msg = err.get("message") if isinstance(err, dict) else str(data)
# # #         raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
# # #     return data
# # #
# # #
# # # @router.post("/auth/otp/send")
# # # async def otp_send(data: OtpSendRequest, request: Request):
# # #     db = request.scope["env"].DB
# # #     mobile = _normalize_mobile(data.mobile)
# # #     purpose = data.purpose
# # #
# # #     user = await _find_user_id_by_mobile(db, mobile)
# # #
# # #     if purpose == "login" and not user:
# # #         raise HTTPException(
# # #             status_code=404,
# # #             detail="No account with this mobile. Please sign up.",
# # #         )
# # #     if purpose == "signup" and user:
# # #         raise HTTPException(
# # #             status_code=409,
# # #             detail="Mobile already registered. Please login.",
# # #         )
# # #
# # #     code = f"{secrets.randbelow(10**6):06d}"
# # #     salt = secrets.token_hex(8)
# # #     code_hash = _hash_otp(code, salt)
# # #     expires = (datetime.utcnow() + timedelta(seconds=OTP_TTL_SEC)).isoformat()
# # #     otp_id = secrets.token_hex(8)
# # #
# # #     await db.prepare(
# # #         """
# # #         UPDATE otp_codes SET consumed = 1
# # #         WHERE mobile = ? AND purpose = ? AND consumed = 0
# # #         """
# # #     ).bind(mobile, purpose).run()
# # #
# # #     await db.prepare(
# # #         """
# # #         INSERT INTO otp_codes (id, mobile, purpose, code_hash, expires_at, attempts, consumed)
# # #         VALUES (?, ?, ?, ?, ?, 0, 0)
# # #         """
# # #     ).bind(otp_id, mobile, purpose, f"{salt}:{code_hash}", expires).run()
# # #
# # #     await _send_whatsapp_otp(request, mobile, code)
# # #
# # #     return {
# # #         "message": "OTP sent on WhatsApp",
# # #         "mobile": mobile,
# # #         "purpose": purpose,
# # #         "expires_in": OTP_TTL_SEC,
# # #     }
# # #
# # #
# # # @router.post("/auth/otp/verify")
# # # async def otp_verify(data: OtpVerifyRequest, request: Request):
# # #     db = request.scope["env"].DB
# # #     mobile = _normalize_mobile(data.mobile)
# # #     purpose = data.purpose
# # #     otp = (data.otp or "").strip()
# # #
# # #     row = await db.prepare(
# # #         """
# # #         SELECT * FROM otp_codes
# # #         WHERE mobile = ? AND purpose = ? AND consumed = 0
# # #         ORDER BY created_at DESC LIMIT 1
# # #         """
# # #     ).bind(mobile, purpose).first()
# # #     if not row:
# # #         raise HTTPException(
# # #             status_code=400,
# # #             detail="OTP expired or not found. Request a new one.",
# # #         )
# # #
# # #     r = dict(row)
# # #     if int(r.get("attempts") or 0) >= OTP_MAX_ATTEMPTS:
# # #         raise HTTPException(
# # #             status_code=429,
# # #             detail="Too many attempts. Request a new OTP.",
# # #         )
# # #
# # #     try:
# # #         exp = datetime.fromisoformat(str(r["expires_at"]).replace("Z", ""))
# # #     except Exception:
# # #         raise HTTPException(status_code=400, detail="OTP expired. Request a new one.")
# # #
# # #     if datetime.utcnow() > exp:
# # #         raise HTTPException(
# # #             status_code=400,
# # #             detail="OTP expired. Request a new one.",
# # #         )
# # #
# # #     try:
# # #         salt, stored_hash = str(r["code_hash"]).split(":", 1)
# # #     except Exception:
# # #         raise HTTPException(
# # #             status_code=400,
# # #             detail="Invalid OTP record. Request a new one.",
# # #         )
# # #
# # #     if not hmac.compare_digest(_hash_otp(otp, salt), stored_hash):
# # #         await db.prepare(
# # #             "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ?"
# # #         ).bind(r["id"]).run()
# # #         raise HTTPException(status_code=400, detail="Invalid OTP")
# # #
# # #     await db.prepare(
# # #         "UPDATE otp_codes SET consumed = 1 WHERE id = ?"
# # #     ).bind(r["id"]).run()
# # #
# # #     try:
# # #         if purpose == "login":
# # #             user = await _find_user_by_mobile(db, mobile)
# # #             if not user:
# # #                 raise HTTPException(status_code=404, detail="User not found")
# # #             u = dict(user)
# # #         else:
# # #             existing = await _find_user_id_by_mobile(db, mobile)
# # #             if existing:
# # #                 raise HTTPException(
# # #                     status_code=409,
# # #                     detail="Mobile already registered. Please login.",
# # #                 )
# # #
# # #             full_name = (data.fullName or data.name or "User").strip() or "User"
# # #             user_id = secrets.token_hex(8).upper()
# # #             digits = _digits_only(mobile)
# # #             email = (data.email or f"{digits}@otp.local").strip()
# # #             want_to = data.want_to or "finder"
# # #             gender = (data.gender or "").strip()
# # #             city = (data.city or "").strip()
# # #             pincode = (data.pincode or "").strip()
# # #             country = (data.country or "India").strip()
# # #
# # #             # User password from Flutter, or random if missing
# # #             password_value = _password_for_signup(data.password)
# # #
# # #             if email and not email.endswith("@otp.local"):
# # #                 em = await db.prepare(
# # #                     "SELECT id FROM users WHERE LOWER(email) = LOWER(?)"
# # #                 ).bind(email).first()
# # #                 if em:
# # #                     raise HTTPException(
# # #                         status_code=409,
# # #                         detail="Email already registered. Use another email or login.",
# # #                     )
# # #
# # #             try:
# # #                 await db.prepare(
# # #                     """
# # #                     INSERT INTO users (
# # #                         id, full_name, email, mobile, password, country, city, pincode,
# # #                         gender, want_to, lat, lng
# # #                     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
# # #                     """
# # #                 ).bind(
# # #                     user_id,
# # #                     full_name,
# # #                     email,
# # #                     mobile,
# # #                     password_value,
# # #                     country,
# # #                     city,
# # #                     pincode,
# # #                     gender,
# # #                     want_to,
# # #                     data.lat,
# # #                     data.lng,
# # #                 ).run()
# # #             except Exception as e:
# # #                 msg = str(e).lower()
# # #                 print(f"[otp_verify] INSERT failed: {type(e).__name__}: {e}")
# # #                 if "unique" in msg or "constraint" in msg:
# # #                     if "email" in msg:
# # #                         raise HTTPException(
# # #                             status_code=409,
# # #                             detail="Email already registered. Use another email or login.",
# # #                         )
# # #                     if "mobile" in msg:
# # #                         raise HTTPException(
# # #                             status_code=409,
# # #                             detail="Mobile already registered. Please login.",
# # #                         )
# # #                     if "password" in msg or "not null" in msg:
# # #                         raise HTTPException(
# # #                             status_code=500,
# # #                             detail=f"Signup schema error: {e}",
# # #                         )
# # #                     raise HTTPException(
# # #                         status_code=409,
# # #                         detail=f"Account conflict: {e}",
# # #                     )
# # #                 raise HTTPException(
# # #                     status_code=500,
# # #                     detail=f"Signup failed: {type(e).__name__}: {e}",
# # #                 )
# # #
# # #             user = await db.prepare(
# # #                 "SELECT * FROM users WHERE id = ?"
# # #             ).bind(user_id).first()
# # #             if not user:
# # #                 raise HTTPException(
# # #                     status_code=500,
# # #                     detail="Signup failed: user not found after insert",
# # #                 )
# # #             u = dict(user)
# # #
# # #         token = create_access_token({"sub": u["id"]})
# # #         return {
# # #             "access_token": token,
# # #             "token": token,
# # #             "token_type": "bearer",
# # #             "user": {
# # #                 "id": u["id"],
# # #                 "account_id": u["id"],
# # #                 "fullName": u.get("full_name"),
# # #                 "name": u.get("full_name"),
# # #                 "email": u.get("email"),
# # #                 "mobile": u.get("mobile"),
# # #                 "want_to": u.get("want_to"),
# # #                 "role": u.get("want_to"),
# # #                 "city": u.get("city"),
# # #             },
# # #         }
# # #     except HTTPException:
# # #         raise
# # #     except Exception as e:
# # #         raise HTTPException(
# # #             status_code=500,
# # #             detail=f"Verify failed: {type(e).__name__}: {e}",
# # #         )
# #
# #
# # from fastapi import APIRouter, Request, HTTPException
# # from pydantic import BaseModel, Field
# # from typing import Optional, Literal
# # import secrets
# # import hashlib
# # import hmac
# # import re
# # from datetime import datetime, timedelta
# # from utils.security import create_access_token
# #
# # router = APIRouter()
# #
# # OTP_TTL_SEC = 300
# # OTP_MAX_ATTEMPTS = 5
# #
# # NO_PARAM_TEMPLATES = {"hello_world", "hello world"}
# # AUTH_OTP_TEMPLATES = {
# #     "login_otp",
# #     "verify_code",
# #     "verify_code_1",
# #     "authentication_code",
# #     "otp_verification",
# # }
# #
# #
# # class OtpSendRequest(BaseModel):
# #     mobile: str = Field(..., min_length=10, max_length=16)
# #     purpose: Literal["login", "signup"] = "login"
# #
# #
# # class OtpVerifyRequest(BaseModel):
# #     mobile: str
# #     otp: str = Field(..., min_length=4, max_length=8)
# #     purpose: Literal["login", "signup"] = "login"
# #     fullName: Optional[str] = None
# #     name: Optional[str] = None
# #     email: Optional[str] = None
# #     country: Optional[str] = "India"
# #     city: Optional[str] = None
# #     pincode: Optional[str] = None
# #     gender: Optional[str] = None
# #     want_to: Optional[Literal["finder", "companion"]] = "finder"
# #     lat: Optional[float] = None
# #     lng: Optional[float] = None
# #
# #
# # def _normalize_mobile(raw: str) -> str:
# #     s = re.sub(r"[^\d+]", "", (raw or "").strip())
# #     if s.startswith("00"):
# #         s = "+" + s[2:]
# #     if not s.startswith("+"):
# #         digits = re.sub(r"\D", "", s)
# #         if len(digits) == 10:
# #             s = "+91" + digits
# #         else:
# #             s = "+" + digits
# #     return s
# #
# #
# # def _hash_otp(code: str, salt: str) -> str:
# #     return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()
# #
# #
# # def _digits_only(mobile: str) -> str:
# #     return re.sub(r"\D", "", mobile or "")
# #
# #
# # async def _http_json(method: str, url: str, headers: dict, body: dict | None = None):
# #     import json as _json
# #
# #     payload = _json.dumps(body) if body is not None else None
# #     try:
# #         from js import fetch, Object
# #         from pyodide.ffi import to_js
# #
# #         opts = {"method": method, "headers": headers}
# #         if payload is not None:
# #             opts["body"] = payload
# #         resp = await fetch(url, to_js(opts, dict_converter=Object.fromEntries))
# #         text = await resp.text()
# #         code = int(resp.status)
# #         try:
# #             data = _json.loads(text) if text else {}
# #         except Exception:
# #             data = {"message": text}
# #         return code, data
# #     except Exception:
# #         pass
# #
# #     import urllib.request
# #     import urllib.error
# #
# #     data_bytes = payload.encode("utf-8") if payload else None
# #     req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
# #     try:
# #         with urllib.request.urlopen(req, timeout=30) as resp:
# #             text = resp.read().decode("utf-8")
# #             return resp.status, (_json.loads(text) if text else {})
# #     except urllib.error.HTTPError as e:
# #         text = e.read().decode("utf-8")
# #         try:
# #             data = _json.loads(text) if text else {}
# #         except Exception:
# #             data = {"message": text}
# #         return int(e.code), data
# #     except Exception as e:
# #         raise HTTPException(status_code=502, detail=f"WhatsApp request failed: {e}")
# #
# #
# # def _build_auth_otp_template(name: str, lang: str, code: str) -> dict:
# #     return {
# #         "name": name,
# #         "language": {"code": lang},
# #         "components": [
# #             {
# #                 "type": "body",
# #                 "parameters": [{"type": "text", "text": str(code)}],
# #             },
# #             {
# #                 "type": "button",
# #                 "sub_type": "url",
# #                 "index": "0",
# #                 "parameters": [{"type": "text", "text": str(code)}],
# #             },
# #         ],
# #     }
# #
# #
# # async def _send_whatsapp_otp(request: Request, mobile: str, code: str):
# #     env = request.scope["env"]
# #     token = (getattr(env, "WHATSAPP_TOKEN", None) or "").strip()
# #     phone_id = (getattr(env, "WHATSAPP_PHONE_NUMBER_ID", None) or "").strip()
# #     template = (getattr(env, "WHATSAPP_OTP_TEMPLATE", None) or "login_otp").strip()
# #     lang = (getattr(env, "WHATSAPP_OTP_LANG", None) or "en").strip()
# #
# #     if not token or not phone_id:
# #         raise HTTPException(status_code=500, detail="WhatsApp not configured")
# #
# #     url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
# #     headers = {
# #         "Authorization": f"Bearer {token}",
# #         "Content-Type": "application/json",
# #     }
# #     to = _digits_only(mobile)
# #     t_lower = template.lower().replace("-", "_")
# #
# #     if t_lower in NO_PARAM_TEMPLATES:
# #         template_obj = {
# #             "name": "hello_world",
# #             "language": {"code": "en_US"},
# #         }
# #     elif t_lower in AUTH_OTP_TEMPLATES or "otp" in t_lower:
# #         template_obj = _build_auth_otp_template(template, lang, code)
# #     elif template:
# #         template_obj = {
# #             "name": template,
# #             "language": {"code": lang},
# #             "components": [
# #                 {
# #                     "type": "body",
# #                     "parameters": [{"type": "text", "text": str(code)}],
# #                 }
# #             ],
# #         }
# #     else:
# #         body = {
# #             "messaging_product": "whatsapp",
# #             "to": to,
# #             "type": "text",
# #             "text": {
# #                 "body": f"Your verification code is {code}. Valid for 5 minutes.",
# #             },
# #         }
# #         code_http, data = await _http_json("POST", url, headers, body)
# #         if code_http >= 400:
# #             err = (data.get("error") if isinstance(data, dict) else None) or data
# #             msg = err.get("message") if isinstance(err, dict) else str(data)
# #             raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
# #         return data
# #
# #     body = {
# #         "messaging_product": "whatsapp",
# #         "recipient_type": "individual",
# #         "to": to,
# #         "type": "template",
# #         "template": template_obj,
# #     }
# #
# #     code_http, data = await _http_json("POST", url, headers, body)
# #     if code_http >= 400 and template_obj.get("components") and len(template_obj["components"]) > 1:
# #         # Retry body-only if button not accepted
# #         template_obj = {
# #             "name": template_obj["name"],
# #             "language": template_obj["language"],
# #             "components": [
# #                 {
# #                     "type": "body",
# #                     "parameters": [{"type": "text", "text": str(code)}],
# #                 }
# #             ],
# #         }
# #         body["template"] = template_obj
# #         code_http, data = await _http_json("POST", url, headers, body)
# #
# #     if code_http >= 400:
# #         err = (data.get("error") if isinstance(data, dict) else None) or data
# #         msg = err.get("message") if isinstance(err, dict) else str(data)
# #         raise HTTPException(status_code=502, detail=msg or "WhatsApp send failed")
# #     return data
# #
# #
# # @router.post("/auth/otp/send")
# # async def otp_send(data: OtpSendRequest, request: Request):
# #     db = request.scope["env"].DB
# #     mobile = _normalize_mobile(data.mobile)
# #     purpose = data.purpose
# #
# #     user = await db.prepare(
# #         "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
# #     ).bind(mobile, mobile.lstrip("+")).first()
# #
# #     if purpose == "login" and not user:
# #         raise HTTPException(
# #             status_code=404,
# #             detail="No account with this mobile. Please sign up.",
# #         )
# #     if purpose == "signup" and user:
# #         raise HTTPException(
# #             status_code=409,
# #             detail="Mobile already registered. Please login.",
# #         )
# #
# #     code = f"{secrets.randbelow(10**6):06d}"
# #     salt = secrets.token_hex(8)
# #     code_hash = _hash_otp(code, salt)
# #     expires = (datetime.utcnow() + timedelta(seconds=OTP_TTL_SEC)).isoformat()
# #     otp_id = secrets.token_hex(8)
# #
# #     await db.prepare(
# #         """
# #         UPDATE otp_codes SET consumed = 1
# #         WHERE mobile = ? AND purpose = ? AND consumed = 0
# #         """
# #     ).bind(mobile, purpose).run()
# #
# #     await db.prepare(
# #         """
# #         INSERT INTO otp_codes (id, mobile, purpose, code_hash, expires_at, attempts, consumed)
# #         VALUES (?, ?, ?, ?, ?, 0, 0)
# #         """
# #     ).bind(otp_id, mobile, purpose, f"{salt}:{code_hash}", expires).run()
# #
# #     await _send_whatsapp_otp(request, mobile, code)
# #
# #     return {
# #         "message": "OTP sent on WhatsApp",
# #         "mobile": mobile,
# #         "purpose": purpose,
# #         "expires_in": OTP_TTL_SEC,
# #     }
# #
# #
# # @router.post("/auth/otp/verify")
# # async def otp_verify(data: OtpVerifyRequest, request: Request):
# #     db = request.scope["env"].DB
# #     mobile = _normalize_mobile(data.mobile)
# #     purpose = data.purpose
# #     otp = (data.otp or "").strip()
# #
# #     row = await db.prepare(
# #         """
# #         SELECT * FROM otp_codes
# #         WHERE mobile = ? AND purpose = ? AND consumed = 0
# #         ORDER BY created_at DESC LIMIT 1
# #         """
# #     ).bind(mobile, purpose).first()
# #     if not row:
# #         raise HTTPException(
# #             status_code=400,
# #             detail="OTP expired or not found. Request a new one.",
# #         )
# #
# #     r = dict(row)
# #     if int(r.get("attempts") or 0) >= OTP_MAX_ATTEMPTS:
# #         raise HTTPException(
# #             status_code=429,
# #             detail="Too many attempts. Request a new OTP.",
# #         )
# #
# #     exp = datetime.fromisoformat(str(r["expires_at"]).replace("Z", ""))
# #     if datetime.utcnow() > exp:
# #         raise HTTPException(
# #             status_code=400,
# #             detail="OTP expired. Request a new one.",
# #         )
# #
# #     salt, stored_hash = str(r["code_hash"]).split(":", 1)
# #     if not hmac.compare_digest(_hash_otp(otp, salt), stored_hash):
# #         await db.prepare(
# #             "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ?"
# #         ).bind(r["id"]).run()
# #         raise HTTPException(status_code=400, detail="Invalid OTP")
# #
# #     await db.prepare(
# #         "UPDATE otp_codes SET consumed = 1 WHERE id = ?"
# #     ).bind(r["id"]).run()
# #
# #     if purpose == "login":
# #         user = await db.prepare(
# #             "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
# #         ).bind(mobile, mobile.lstrip("+")).first()
# #         if not user:
# #             raise HTTPException(status_code=404, detail="User not found")
# #         u = dict(user)
# #     else:
# #         existing = await db.prepare(
# #             "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
# #         ).bind(mobile, mobile.lstrip("+")).first()
# #         if existing:
# #             raise HTTPException(status_code=409, detail="Mobile already registered")
# #
# #         full_name = (data.fullName or data.name or "User").strip()
# #         user_id = secrets.token_hex(4).upper()
# #         digits = _digits_only(mobile)
# #         email = (data.email or f"{digits}@otp.local").strip()
# #         want_to = data.want_to or "finder"
# #
# #         await db.prepare(
# #             """
# #             INSERT INTO users (
# #                 id, full_name, email, mobile, country, city, pincode,
# #                 gender, want_to, password_hash, lat, lng
# #             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
# #             """
# #         ).bind(
# #             user_id,
# #             full_name,
# #             email,
# #             mobile,
# #             data.country or "India",
# #             data.city or "",
# #             data.pincode or "",
# #             data.gender or "",
# #             want_to,
# #             secrets.token_hex(16),
# #             data.lat,
# #             data.lng,
# #         ).run()
# #
# #         user = await db.prepare(
# #             "SELECT * FROM users WHERE id = ?"
# #         ).bind(user_id).first()
# #         u = dict(user)
# #
# #     token = create_access_token({"sub": u["id"]})
# #     return {
# #         "access_token": token,
# #         "token": token,
# #         "token_type": "bearer",
# #         "user": {
# #             "id": u["id"],
# #             "account_id": u["id"],
# #             "fullName": u.get("full_name"),
# #             "name": u.get("full_name"),
# #             "email": u.get("email"),
# #             "mobile": u.get("mobile"),
# #             "want_to": u.get("want_to"),
# #             "role": u.get("want_to"),
# #             "city": u.get("city"),
# #         },
# #     }
#
#
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
#     # Required for signup — used for later mobile + password login
#     password: Optional[str] = Field(None, min_length=6, max_length=128)
#     fullName: Optional[str] = None
#     name: Optional[str] = None
#     email: Optional[str] = None
#     country: Optional[str] = "India"
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
#     await db.prepare(
#         "UPDATE otp_codes SET consumed = 1 WHERE id = ?"
#     ).bind(r["id"]).run()
#
#     if purpose == "login":
#         # OTP-only login (optional). Prefer mobile+password via /api/auth/login.
#         user = await db.prepare(
#             "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
#         ).bind(mobile, mobile.lstrip("+")).first()
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
#         u = dict(user)
#     else:
#         existing = await db.prepare(
#             "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
#         ).bind(mobile, mobile.lstrip("+")).first()
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
#         user_id = secrets.token_hex(4).upper()
#         digits = _digits_only(mobile)
#         email = (data.email or f"{digits}@otp.local").strip()
#         want_to = data.want_to or "finder"
#         password_hash = hash_password(plain)
#
#         await db.prepare(
#             """
#             INSERT INTO users (
#                 id, full_name, email, mobile, country, city, pincode,
#                 gender, want_to, password_hash, lat, lng
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#             """
#         ).bind(
#             user_id,
#             full_name,
#             email,
#             mobile,
#             data.country or "India",
#             data.city or "",
#             data.pincode or "",
#             data.gender or "",
#             want_to,
#             password_hash,
#             data.lat,
#             data.lng,
#         ).run()
#
#         user = await db.prepare(
#             "SELECT * FROM users WHERE id = ?"
#         ).bind(user_id).first()
#         u = dict(user)
#
#     token = create_access_token({"sub": u["id"]})
#     return {
#         "access_token": token,
#         "token": token,
#         "token_type": "bearer",
#         "user": {
#             "id": u["id"],
#             "account_id": u["id"],
#             "fullName": u.get("full_name"),
#             "name": u.get("full_name"),
#             "email": u.get("email"),
#             "mobile": u.get("mobile"),
#             "want_to": u.get("want_to"),
#             "role": u.get("want_to"),
#             "city": u.get("city"),
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
    purpose: Literal["login", "signup"] = "login"


class OtpVerifyRequest(BaseModel):
    mobile: str
    otp: str = Field(..., min_length=4, max_length=8)
    purpose: Literal["login", "signup"] = "login"
    password: Optional[str] = Field(None, min_length=6, max_length=128)
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
    return re.sub(r"\D", "", mobile or "")


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


@router.post("/auth/otp/send")
async def otp_send(data: OtpSendRequest, request: Request):
    db = request.scope["env"].DB
    mobile = _normalize_mobile(data.mobile)
    purpose = data.purpose

    user = await db.prepare(
        "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
    ).bind(mobile, mobile.lstrip("+")).first()

    # Also match 10-digit storage from old register
    if not user:
        digits = _digits_only(mobile)
        last10 = digits[-10:] if len(digits) >= 10 else digits
        user = await db.prepare(
            "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
        ).bind(last10, digits).first()

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

    # Mark consumed only after OTP is valid
    await db.prepare(
        "UPDATE otp_codes SET consumed = 1 WHERE id = ?"
    ).bind(r["id"]).run()

    if purpose == "login":
        user = await db.prepare(
            "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
        ).bind(mobile, mobile.lstrip("+")).first()
        if not user:
            digits = _digits_only(mobile)
            last10 = digits[-10:] if len(digits) >= 10 else digits
            user = await db.prepare(
                "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
            ).bind(last10, digits).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        u = dict(user)
    else:
        # --- SIGNUP: create user (same columns as register_user) ---
        existing = await db.prepare(
            "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
        ).bind(mobile, mobile.lstrip("+")).first()
        if not existing:
            digits = _digits_only(mobile)
            last10 = digits[-10:] if len(digits) >= 10 else digits
            existing = await db.prepare(
                "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
            ).bind(last10, digits).first()
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
        email = (data.email or f"{digits}@otp.local").strip().lower()
        want_to = data.want_to or "finder"
        password_hashed = hash_password(plain)

        # Avoid unique email clash
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
            # Same shape as services/auth_service.register_user
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

        # Optional full_name if column exists
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

    token = create_access_token(
        data={"sub": u["id"], "email": u.get("email")}
    )
    return {
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "user": {
            "id": u["id"],
            "account_id": u["id"],
            "fullName": u.get("full_name") or full_name if purpose == "signup" else u.get("full_name"),
            "name": u.get("full_name") or (full_name if purpose == "signup" else None),
            "email": u.get("email"),
            "mobile": u.get("mobile"),
            "want_to": u.get("want_to"),
            "role": u.get("want_to"),
            "city": u.get("city"),
            "country": u.get("country"),
        },
    }