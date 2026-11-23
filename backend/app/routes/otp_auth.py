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
# # # def _hash_otp(code: str, salt: str) -> str:
# # #     return hashlib.sha256(f"{salt}:{code}".encode()).hexdigest()
# # #
# # #
# # # def _digits_only(mobile: str) -> str:
# # #     """Meta 'to' field: digits only, no +."""
# # #     return re.sub(r"\D", "", mobile or "")
# # #
# # #
# # # async def _http_json(
# # #     method: str,
# # #     url: str,
# # #     headers: dict,
# # #     body: dict | None = None,
# # # ) -> tuple[int, dict]:
# # #     """Workers fetch first; urllib fallback for local."""
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
# # # async def _send_whatsapp_otp(request: Request, mobile: str, code: str):
# # #     """
# # #     Template from WHATSAPP_OTP_TEMPLATE.
# # #     - hello_world: en_US, no components (does NOT include OTP digits)
# # #     - real OTP template: body {{1}} = code
# # #     """
# # #     env = request.scope["env"]
# # #     token = (getattr(env, "WHATSAPP_TOKEN", None) or "").strip()
# # #     phone_id = (getattr(env, "WHATSAPP_PHONE_NUMBER_ID", None) or "").strip()
# # #     template = (getattr(env, "WHATSAPP_OTP_TEMPLATE", None) or "login_otp").strip()
# # #     lang = (getattr(env, "WHATSAPP_OTP_LANG", None) or "en_US").strip()
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
# # #
# # #     if template.lower() in ("login_otp", "hello world"):
# # #         body = {
# # #             "messaging_product": "whatsapp",
# # #             "to": to,
# # #             "type": "template",
# # #             "template": {
# # #                 "name": "login_otp",
# # #                 "language": {"code": "en_US"},
# # #             },
# # #         }
# # #     elif template:
# # #         body = {
# # #             "messaging_product": "whatsapp",
# # #             "to": to,
# # #             "type": "template",
# # #             "template": {
# # #                 "name": template,
# # #                 "language": {"code": lang},
# # #                 "components": [
# # #                     {
# # #                         "type": "body",
# # #                         "parameters": [{"type": "text", "text": code}],
# # #                     }
# # #                 ],
# # #             },
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
# # #
# # #     code_http, data = await _http_json("POST", url, headers, body)
# # #     if code_http >= 400:
# # #         err = {}
# # #         if isinstance(data, dict):
# # #             err = data.get("error") or data
# # #         msg = err.get("message") if isinstance(err, dict) else str(data)
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
# # #     user = await db.prepare(
# # #         "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
# # #     ).bind(mobile, mobile.lstrip("+")).first()
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
# # #     exp = datetime.fromisoformat(str(r["expires_at"]).replace("Z", ""))
# # #     if datetime.utcnow() > exp:
# # #         raise HTTPException(
# # #             status_code=400,
# # #             detail="OTP expired. Request a new one.",
# # #         )
# # #
# # #     salt, stored_hash = str(r["code_hash"]).split(":", 1)
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
# # #     if purpose == "login":
# # #         user = await db.prepare(
# # #             "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
# # #         ).bind(mobile, mobile.lstrip("+")).first()
# # #         if not user:
# # #             raise HTTPException(status_code=404, detail="User not found")
# # #         u = dict(user)
# # #     else:
# # #         existing = await db.prepare(
# # #             "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
# # #         ).bind(mobile, mobile.lstrip("+")).first()
# # #         if existing:
# # #             raise HTTPException(
# # #                 status_code=409,
# # #                 detail="Mobile already registered",
# # #             )
# # #
# # #         full_name = (data.fullName or data.name or "User").strip()
# # #         user_id = secrets.token_hex(4).upper()
# # #         digits = _digits_only(mobile)
# # #         email = (data.email or f"{digits}@otp.local").strip()
# # #         want_to = data.want_to or "finder"
# # #
# # #         await db.prepare(
# # #             """
# # #             INSERT INTO users (
# # #                 id, full_name, email, mobile, country, city, pincode,
# # #                 gender, want_to, password_hash, lat, lng
# # #             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
# # #             """
# # #         ).bind(
# # #             user_id,
# # #             full_name,
# # #             email,
# # #             mobile,
# # #             data.country or "India",
# # #             data.city or "",
# # #             data.pincode or "",
# # #             data.gender or "",
# # #             want_to,
# # #             secrets.token_hex(16),
# # #             data.lat,
# # #             data.lng,
# # #         ).run()
# # #
# # #         user = await db.prepare(
# # #             "SELECT * FROM users WHERE id = ?"
# # #         ).bind(user_id).first()
# # #         u = dict(user)
# # #
# # #     token = create_access_token({"sub": u["id"]})
# # #     return {
# # #         "access_token": token,
# # #         "token": token,
# # #         "token_type": "bearer",
# # #         "user": {
# # #             "id": u["id"],
# # #             "account_id": u["id"],
# # #             "fullName": u.get("full_name"),
# # #             "name": u.get("full_name"),
# # #             "email": u.get("email"),
# # #             "mobile": u.get("mobile"),
# # #             "want_to": u.get("want_to"),
# # #             "role": u.get("want_to"),
# # #             "city": u.get("city"),
# # #         },
# # #     }
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
# # # Templates that do NOT take body parameters (Meta sample)
# # NO_PARAM_TEMPLATES = {"hello_world", "hello world"}
# #
# # # Auth / OTP templates that take {{1}} = code (+ copy-code button)
# # AUTH_OTP_TEMPLATES = {
# #     "logn_otp",
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
# #     """Meta 'to' field: digits only, no +."""
# #     return re.sub(r"\D", "", mobile or "")
# #
# #
# # async def _http_json(
# #     method: str,
# #     url: str,
# #     headers: dict,
# #     body: dict | None = None,
# # ) -> tuple[int, dict]:
# #     """Workers fetch first; urllib fallback for local."""
# #     import json as _json
# #
# #     payload = _json.dumps(body) if body is not None else None
# #
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
# #     """
# #     Authentication template send payload (Meta docs).
# #     - BODY parameter {{1}} = OTP
# #     - BUTTON (copy code / OTP) also needs the same code
# #     """
# #     return {
# #         "name": name,
# #         "language": {"code": lang},
# #         "components": [
# #             {
# #                 "type": "body",
# #                 "parameters": [
# #                     {"type": "text", "text": str(code)},
# #                 ],
# #             },
# #             {
# #                 "type": "button",
# #                 "sub_type": "url",
# #                 "index": "0",
# #                 "parameters": [
# #                     {"type": "text", "text": str(code)},
# #                 ],
# #             },
# #         ],
# #     }
# #
# #
# # async def _send_whatsapp_otp(request: Request, mobile: str, code: str):
# #     """
# #     WHATSAPP_OTP_TEMPLATE:
# #       - hello_world → sample, no params (does not show OTP)
# #       - login_otp / auth names → Authentication body+button with code
# #       - other → body {{1}} only
# #       - empty → session text (only works inside 24h window)
# #     """
# #     env = request.scope["env"]
# #     token = (getattr(env, "WHATSAPP_TOKEN", None) or "").strip()
# #     phone_id = (getattr(env, "WHATSAPP_PHONE_NUMBER_ID", None) or "").strip()
# #     template = (getattr(env, "WHATSAPP_OTP_TEMPLATE", None) or "logn_otp").strip()
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
# #         # Meta sample — no OTP in message
# #         template_obj = {
# #             "name": "hello_world",
# #             "language": {"code": "en"},
# #         }
# #     elif t_lower in AUTH_OTP_TEMPLATES or t_lower.endswith("_otp") or "otp" in t_lower:
# #         # Authentication OTP (login_otp, etc.)
# #         template_obj = _build_auth_otp_template(template, lang, code)
# #     elif template:
# #         # Generic utility with single body param
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
# #         # Session free-text (user must have messaged you in last 24h)
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
# #     if code_http >= 400:
# #         err = {}
# #         if isinstance(data, dict):
# #             err = data.get("error") or data
# #         msg = err.get("message") if isinstance(err, dict) else str(data)
# #         # If button component not accepted (template has no button), retry body-only
# #         if (
# #             code_http >= 400
# #             and isinstance(err, dict)
# #             and template_obj.get("components")
# #             and len(template_obj["components"]) > 1
# #         ):
# #             template_obj = {
# #                 "name": template_obj["name"],
# #                 "language": template_obj["language"],
# #                 "components": [
# #                     {
# #                         "type": "body",
# #                         "parameters": [{"type": "text", "text": str(code)}],
# #                     }
# #                 ],
# #             }
# #             body["template"] = template_obj
# #             code_http, data = await _http_json("POST", url, headers, body)
# #             if code_http < 400:
# #                 return data
# #             err = (data.get("error") if isinstance(data, dict) else None) or data
# #             msg = err.get("message") if isinstance(err, dict) else str(data)
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
# #             raise HTTPException(
# #                 status_code=409,
# #                 detail="Mobile already registered",
# #             )
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
# from utils.security import create_access_token
#
# router = APIRouter()
#
# OTP_TTL_SEC = 300
# OTP_MAX_ATTEMPTS = 5
#
# NO_PARAM_TEMPLATES = {"hello_world", "hello world"}
#
# AUTH_OTP_TEMPLATES = {
#     "login_otp",  # fixed typo (was logn_otp)
#     "logn_otp",   # keep alias if secret still has old name
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
# async def _http_json(
#     method: str,
#     url: str,
#     headers: dict,
#     body: dict | None = None,
# ) -> tuple[int, dict]:
#     import json as _json
#
#     payload = _json.dumps(body) if body is not None else None
#
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
#             "language": {"code": lang or "en"},
#         }
#     elif t_lower in AUTH_OTP_TEMPLATES or t_lower.endswith("_otp") or "otp" in t_lower:
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
#     if code_http >= 400:
#         err = {}
#         if isinstance(data, dict):
#             err = data.get("error") or data
#         msg = err.get("message") if isinstance(err, dict) else str(data)
#         if (
#             code_http >= 400
#             and isinstance(err, dict)
#             and template_obj.get("components")
#             and len(template_obj["components"]) > 1
#         ):
#             template_obj = {
#                 "name": template_obj["name"],
#                 "language": template_obj["language"],
#                 "components": [
#                     {
#                         "type": "body",
#                         "parameters": [{"type": "text", "text": str(code)}],
#                     }
#                 ],
#             }
#             body["template"] = template_obj
#             code_http, data = await _http_json("POST", url, headers, body)
#             if code_http < 400:
#                 return data
#             err = (data.get("error") if isinstance(data, dict) else None) or data
#             msg = err.get("message") if isinstance(err, dict) else str(data)
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
#     try:
#         exp = datetime.fromisoformat(str(r["expires_at"]).replace("Z", ""))
#     except Exception:
#         raise HTTPException(status_code=400, detail="OTP expired. Request a new one.")
#
#     if datetime.utcnow() > exp:
#         raise HTTPException(
#             status_code=400,
#             detail="OTP expired. Request a new one.",
#         )
#
#     try:
#         salt, stored_hash = str(r["code_hash"]).split(":", 1)
#     except Exception:
#         raise HTTPException(status_code=400, detail="Invalid OTP record. Request a new one.")
#
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
#     try:
#         if purpose == "login":
#             user = await db.prepare(
#                 "SELECT * FROM users WHERE mobile = ? OR mobile = ?"
#             ).bind(mobile, mobile.lstrip("+")).first()
#             if not user:
#                 raise HTTPException(status_code=404, detail="User not found")
#             u = dict(user)
#         else:
#             # Mobile already registered
#             existing = await db.prepare(
#                 "SELECT id FROM users WHERE mobile = ? OR mobile = ?"
#             ).bind(mobile, mobile.lstrip("+")).first()
#             if existing:
#                 raise HTTPException(
#                     status_code=409,
#                     detail="Mobile already registered. Please login.",
#                 )
#
#             full_name = (data.fullName or data.name or "User").strip() or "User"
#             user_id = secrets.token_hex(4).upper()
#             digits = _digits_only(mobile)
#             email = (data.email or f"{digits}@otp.local").strip()
#             want_to = data.want_to or "finder"
#             gender = (data.gender or "").strip()
#             city = (data.city or "").strip()
#             pincode = (data.pincode or "").strip()
#             country = (data.country or "India").strip()
#
#             # Email unique → clear 409 instead of DB 500
#             if email and not email.endswith("@otp.local"):
#                 em = await db.prepare(
#                     "SELECT id FROM users WHERE LOWER(email) = LOWER(?)"
#                 ).bind(email).first()
#                 if em:
#                     raise HTTPException(
#                         status_code=409,
#                         detail="Email already registered. Use another email or login.",
#                     )
#
#             try:
#                 await db.prepare(
#                     """
#                     INSERT INTO users (
#                         id, full_name, email, mobile, country, city, pincode,
#                         gender, want_to, password_hash, lat, lng
#                     ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                     """
#                 ).bind(
#                     user_id,
#                     full_name,
#                     email,
#                     mobile,
#                     country,
#                     city,
#                     pincode,
#                     gender,
#                     want_to,
#                     secrets.token_hex(16),
#                     data.lat,
#                     data.lng,
#                 ).run()
#             except Exception as e:
#                 msg = str(e).lower()
#                 if "unique" in msg or "constraint" in msg:
#                     if "email" in msg:
#                         raise HTTPException(
#                             status_code=409,
#                             detail="Email already registered. Use another email or login.",
#                         )
#                     if "mobile" in msg:
#                         raise HTTPException(
#                             status_code=409,
#                             detail="Mobile already registered. Please login.",
#                         )
#                     raise HTTPException(
#                         status_code=409,
#                         detail="Account already exists. Please login.",
#                     )
#                 raise HTTPException(
#                     status_code=500,
#                     detail=f"Signup failed: {type(e).__name__}: {e}",
#                 )
#
#             user = await db.prepare(
#                 "SELECT * FROM users WHERE id = ?"
#             ).bind(user_id).first()
#             if not user:
#                 raise HTTPException(
#                     status_code=500,
#                     detail="Signup failed: user not found after insert",
#                 )
#             u = dict(user)
#
#         token = create_access_token({"sub": u["id"]})
#         return {
#             "access_token": token,
#             "token": token,
#             "token_type": "bearer",
#             "user": {
#                 "id": u["id"],
#                 "account_id": u["id"],
#                 "fullName": u.get("full_name"),
#                 "name": u.get("full_name"),
#                 "email": u.get("email"),
#                 "mobile": u.get("mobile"),
#                 "want_to": u.get("want_to"),
#                 "role": u.get("want_to"),
#                 "city": u.get("city"),
#             },
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Verify failed: {type(e).__name__}: {e}",
#         )


from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional, Literal
import secrets
import hashlib
import hmac
import re
from datetime import datetime, timedelta, timezone
from utils.security import create_access_token

router = APIRouter()

OTP_TTL_SEC = 300
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SEC = 45

NO_PARAM_TEMPLATES = {"hello_world", "hello world"}

AUTH_OTP_TEMPLATES = {
    "login_otp",
    "logn_otp",
    "verify_code",
    "verify_code_1",
    "authentication_code",
    "otp_verification",
    "signup_verification_otp",
}


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


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _utcnow() -> datetime:
    """Naive UTC datetime (keeps compatibility with already-stored values)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_dt(value) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", ""))
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        return None


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


def _hash_otp(code: str, salt: str, secret: str = "") -> str:
    """HMAC with server secret if OTP_SECRET is set, else salted SHA-256."""
    msg = f"{salt}:{code}".encode()
    if secret:
        return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    return hashlib.sha256(msg).hexdigest()


def _otp_secret(request: Request) -> str:
    env = request.scope["env"]
    return (getattr(env, "OTP_SECRET", None) or "").strip()


def _digits_only(mobile: str) -> str:
    return re.sub(r"\D", "", mobile or "")


def _wa_error(data) -> tuple[Optional[int], str]:
    """Extract (code, message) from a Graph API error payload."""
    err = {}
    if isinstance(data, dict):
        err = data.get("error") or data
    if isinstance(err, dict):
        code = err.get("code")
        msg = err.get("message") or "WhatsApp send failed"
        details = (err.get("error_data") or {}).get("details")
        if details:
            msg = f"{msg} - {details}"
        if code:
            msg = f"({code}) {msg}"
        return code, msg
    return None, str(data) or "WhatsApp send failed"


async def _http_json(
    method: str,
    url: str,
    headers: dict,
    body: dict | None = None,
) -> tuple[int, dict]:
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
    # Authentication templates need BOTH the body param and the
    # copy-code / URL button param.
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


async def _send_whatsapp_otp(request: Request, mobile: str, code: str) -> Optional[str]:
    """Send OTP over WhatsApp. Returns the WhatsApp message id (wamid)."""
    env = request.scope["env"]
    token = (getattr(env, "WHATSAPP_TOKEN", None) or "").strip()
    phone_id = (getattr(env, "WHATSAPP_PHONE_NUMBER_ID", None) or "").strip()
    template = (getattr(env, "WHATSAPP_OTP_TEMPLATE", None) or "login_otp").strip()
    # Must match the template's language EXACTLY as shown in Meta (en vs en_US)
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
            "language": {"code": lang or "en"},
        }
    elif t_lower in AUTH_OTP_TEMPLATES or t_lower.endswith("_otp") or "otp" in t_lower:
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
            _, msg = _wa_error(data)
            print(f"WA send FAILED (text) to={to} http={code_http} resp={data}")
            raise HTTPException(status_code=502, detail=msg)
        wa_id = ((data.get("messages") or [{}])[0]).get("id") if isinstance(data, dict) else None
        print(f"WA send ok (text) to={to} wamid={wa_id}")
        return wa_id

    body = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "template",
        "template": template_obj,
    }

    code_http, data = await _http_json("POST", url, headers, body)
    if code_http >= 400:
        # No silent fallback: auth templates REQUIRE the button component,
        # so retrying with body-only would only hide the real error.
        err_code, msg = _wa_error(data)
        print(
            f"WA send FAILED template={template_obj['name']} "
            f"lang={template_obj['language']['code']} to={to} "
            f"http={code_http} resp={data}"
        )
        if err_code == 132001:
            msg += (
                f" [template '{template_obj['name']}' / language "
                f"'{template_obj['language']['code']}' not found for this phone "
                f"number's WhatsApp Business Account]"
            )
        raise HTTPException(status_code=502, detail=msg)

    wa_id = ((data.get("messages") or [{}])[0]).get("id") if isinstance(data, dict) else None
    print(f"WA send ok template={template_obj['name']} to={to} wamid={wa_id}")
    return wa_id


# --------------------------------------------------------------------------
# WhatsApp webhook (verification + delivery status)
# --------------------------------------------------------------------------

@router.get("/webhook/whatsapp")
async def whatsapp_webhook_verify(request: Request):
    q = request.query_params
    env = request.scope["env"]
    verify_token = (getattr(env, "WHATSAPP_VERIFY_TOKEN", None) or "").strip()
    if (
        q.get("hub.mode") == "subscribe"
        and verify_token
        and q.get("hub.verify_token") == verify_token
    ):
        return PlainTextResponse(q.get("hub.challenge") or "")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook_events(request: Request):
    try:
        body = await request.json()
    except Exception:
        return {"ok": True}

    try:
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for st in value.get("statuses", []):
                    status = st.get("status")  # sent / delivered / read / failed
                    print(
                        f"WA status wamid={st.get('id')} to={st.get('recipient_id')} "
                        f"status={status}"
                    )
                    if status == "failed":
                        print(f"WA delivery FAILED errors={st.get('errors')}")
    except Exception as e:
        print(f"WA webhook parse error: {e}")

    # Always 200 quickly, otherwise Meta keeps retrying
    return {"ok": True}


# --------------------------------------------------------------------------
# OTP endpoints
# --------------------------------------------------------------------------

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

    # ---- Resend cooldown (prevents WhatsApp spam / cost abuse) ----
    last = await db.prepare(
        """
        SELECT created_at FROM otp_codes
        WHERE mobile = ? AND purpose = ?
        ORDER BY created_at DESC LIMIT 1
        """
    ).bind(mobile, purpose).first()
    if last:
        last_dt = _parse_dt(dict(last).get("created_at"))
        if last_dt:
            elapsed = (_utcnow() - last_dt).total_seconds()
            if 0 <= elapsed < OTP_RESEND_COOLDOWN_SEC:
                wait = int(OTP_RESEND_COOLDOWN_SEC - elapsed) + 1
                raise HTTPException(
                    status_code=429,
                    detail=f"Please wait {wait}s before requesting another OTP.",
                )

    now = _utcnow()
    code = f"{secrets.randbelow(10**6):06d}"
    salt = secrets.token_hex(8)
    code_hash = _hash_otp(code, salt, _otp_secret(request))
    expires = (now + timedelta(seconds=OTP_TTL_SEC)).isoformat()
    otp_id = secrets.token_hex(8)

    await db.prepare(
        """
        UPDATE otp_codes SET consumed = 1
        WHERE mobile = ? AND purpose = ? AND consumed = 0
        """
    ).bind(mobile, purpose).run()

    await db.prepare(
        """
        INSERT INTO otp_codes (id, mobile, purpose, code_hash, expires_at, attempts, consumed, created_at)
        VALUES (?, ?, ?, ?, ?, 0, 0, ?)
        """
    ).bind(otp_id, mobile, purpose, f"{salt}:{code_hash}", expires, now.isoformat()).run()

    try:
        wa_id = await _send_whatsapp_otp(request, mobile, code)
    except Exception:
        # Send failed: invalidate this OTP so it can't linger unused
        try:
            await db.prepare(
                "UPDATE otp_codes SET consumed = 1 WHERE id = ?"
            ).bind(otp_id).run()
        except Exception:
            pass
        raise

    return {
        "message": "OTP sent on WhatsApp",
        "mobile": mobile,
        "purpose": purpose,
        "expires_in": OTP_TTL_SEC,
        "resend_after": OTP_RESEND_COOLDOWN_SEC,
        "wa_message_id": wa_id,
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

    exp = _parse_dt(r.get("expires_at"))
    if exp is None:
        raise HTTPException(status_code=400, detail="OTP expired. Request a new one.")

    if _utcnow() > exp:
        raise HTTPException(
            status_code=400,
            detail="OTP expired. Request a new one.",
        )

    try:
        salt, stored_hash = str(r["code_hash"]).split(":", 1)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP record. Request a new one.",
        )

    if not hmac.compare_digest(_hash_otp(otp, salt, _otp_secret(request)), stored_hash):
        await db.prepare(
            "UPDATE otp_codes SET attempts = attempts + 1 WHERE id = ?"
        ).bind(r["id"]).run()
        raise HTTPException(status_code=400, detail="Invalid OTP")

    await db.prepare(
        "UPDATE otp_codes SET consumed = 1 WHERE id = ?"
    ).bind(r["id"]).run()

    try:
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
                    detail="Mobile already registered. Please login.",
                )

            full_name = (data.fullName or data.name or "User").strip() or "User"
            user_id = secrets.token_hex(4).upper()
            digits = _digits_only(mobile)
            email = (data.email or f"{digits}@otp.local").strip()
            want_to = data.want_to or "finder"
            gender = (data.gender or "").strip()
            city = (data.city or "").strip()
            pincode = (data.pincode or "").strip()
            country = (data.country or "India").strip()

            if email and not email.endswith("@otp.local"):
                em = await db.prepare(
                    "SELECT id FROM users WHERE LOWER(email) = LOWER(?)"
                ).bind(email).first()
                if em:
                    raise HTTPException(
                        status_code=409,
                        detail="Email already registered. Use another email or login.",
                    )

            # No password_hash — column does not exist on users table
            try:
                await db.prepare(
                    """
                    INSERT INTO users (
                        id, full_name, email, mobile, country, city, pincode,
                        gender, want_to, lat, lng
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                ).bind(
                    user_id,
                    full_name,
                    email,
                    mobile,
                    country,
                    city,
                    pincode,
                    gender,
                    want_to,
                    data.lat,
                    data.lng,
                ).run()
            except Exception as e:
                msg = str(e).lower()
                if "unique" in msg or "constraint" in msg:
                    if "email" in msg:
                        raise HTTPException(
                            status_code=409,
                            detail="Email already registered. Use another email or login.",
                        )
                    if "mobile" in msg:
                        raise HTTPException(
                            status_code=409,
                            detail="Mobile already registered. Please login.",
                        )
                    raise HTTPException(
                        status_code=409,
                        detail="Account already exists. Please login.",
                    )
                raise HTTPException(
                    status_code=500,
                    detail=f"Signup failed: {type(e).__name__}: {e}",
                )

            user = await db.prepare(
                "SELECT * FROM users WHERE id = ?"
            ).bind(user_id).first()
            if not user:
                raise HTTPException(
                    status_code=500,
                    detail="Signup failed: user not found after insert",
                )
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Verify failed: {type(e).__name__}: {e}",
        )