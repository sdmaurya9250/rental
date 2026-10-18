# from fastapi import APIRouter, Request, Depends, HTTPException, status, Query
# from routes.profile import get_current_user
# from pydantic import BaseModel, Field
# from typing import Optional, List
# import secrets
# import json
# import re
# import uuid
#
# router = APIRouter()
#
# R2_PUBLIC_URL = "https://pub-da3163e6bec745449d684b720f3a6b4c.r2.dev"
#
# ALLOWED_DOC_TYPES = {"aadhaar", "pan", "passport", "driving_license"}
#
#
# # ─────────────────────────────────────────────
# # Models
# # ─────────────────────────────────────────────
# class KycSubmitRequest(BaseModel):
#     # Core
#     doc_type: Optional[str] = None
#     doc_number: Optional[str] = None
#     name_on_document: Optional[str] = None
#     date_of_birth: Optional[str] = None  # YYYY-MM-DD
#
#     # Images (prefer kyc/* R2 paths)
#     document_url: Optional[str] = None          # front (legacy alias)
#     document_front_url: Optional[str] = None
#     document_back_url: Optional[str] = None
#     selfie_url: Optional[str] = None
#
#     # Address helpers
#     address_line: Optional[str] = None
#     pincode: Optional[str] = None
#     document_expiry: Optional[str] = None  # YYYY-MM-DD if passport/DL
#
#     declaration_accepted: Optional[bool] = True
#
#     # Optional OCR / on-device scan results (app sends after scanning image)
#     extracted_name: Optional[str] = None
#     extracted_doc_number: Optional[str] = None
#     extracted_dob: Optional[str] = None
#
#     # Flutter camelCase aliases
#     docType: Optional[str] = None
#     docNumber: Optional[str] = None
#     nameOnDocument: Optional[str] = None
#     dateOfBirth: Optional[str] = None
#     documentUrl: Optional[str] = None
#     documentFrontUrl: Optional[str] = None
#     documentBackUrl: Optional[str] = None
#     selfieUrl: Optional[str] = None
#     addressLine: Optional[str] = None
#     documentExpiry: Optional[str] = None
#     extractedName: Optional[str] = None
#     extractedDocNumber: Optional[str] = None
#     extractedDob: Optional[str] = None
#
#
# class KycRejectRequest(BaseModel):
#     rejection_reason: str = Field(..., min_length=3, max_length=500)
#     admin_note: Optional[str] = None
#
#
# class KycVerifyRequest(BaseModel):
#     admin_note: Optional[str] = None
#
#
# # ─────────────────────────────────────────────
# # Helpers
# # ─────────────────────────────────────────────
# def _norm(s: Optional[str]) -> str:
#     if not s:
#         return ""
#     s = str(s).strip().lower()
#     s = re.sub(r"[^a-z0-9]", "", s)
#     return s
#
#
# def _norm_name(s: Optional[str]) -> str:
#     if not s:
#         return ""
#     s = str(s).strip().lower()
#     s = re.sub(r"\s+", " ", s)
#     return s
#
#
# def _names_match(a: str, b: str) -> bool:
#     a, b = _norm_name(a), _norm_name(b)
#     if not a or not b:
#         return False
#     if a == b:
#         return True
#     # soft: all tokens of shorter name appear in longer
#     ta, tb = set(a.split()), set(b.split())
#     if not ta or not tb:
#         return False
#     shorter, longer = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
#     return shorter.issubset(longer)
#
#
# def _docs_match(a: str, b: str) -> bool:
#     return _norm(a) == _norm(b) and bool(_norm(a))
#
#
# def _dob_match(a: str, b: str) -> bool:
#     if not a or not b:
#         return False
#     return _norm(a) == _norm(b)
#
#
# def _build_match_report(
#     name_on_document: str,
#     doc_number: str,
#     date_of_birth: str,
#     extracted_name: str,
#     extracted_doc_number: str,
#     extracted_dob: str,
#     profile_name: str,
# ) -> dict:
#     """
#     Compare user-filled data vs optional OCR extract + profile name.
#     Does NOT read the image itself.
#     """
#     flags: List[str] = []
#     checks = {}
#
#     has_extract = bool(
#         extracted_name or extracted_doc_number or extracted_dob
#     )
#
#     name_vs_extract = (
#         _names_match(name_on_document, extracted_name) if extracted_name else None
#     )
#     number_vs_extract = (
#         _docs_match(doc_number, extracted_doc_number) if extracted_doc_number else None
#     )
#     dob_vs_extract = (
#         _dob_match(date_of_birth, extracted_dob) if extracted_dob else None
#     )
#     name_vs_profile = _names_match(name_on_document, profile_name) if profile_name else None
#
#     checks["name_matches_extract"] = name_vs_extract
#     checks["number_matches_extract"] = number_vs_extract
#     checks["dob_matches_extract"] = dob_vs_extract
#     checks["name_matches_profile"] = name_vs_profile
#
#     if has_extract:
#         if name_vs_extract is False:
#             flags.append("name_mismatch_scan")
#         if number_vs_extract is False:
#             flags.append("doc_number_mismatch_scan")
#         if dob_vs_extract is False:
#             flags.append("dob_mismatch_scan")
#
#     if name_vs_profile is False:
#         flags.append("name_mismatch_profile")
#
#     if not name_on_document:
#         flags.append("missing_name_on_document")
#     if not doc_number:
#         flags.append("missing_doc_number")
#     if not date_of_birth:
#         flags.append("missing_dob")
#
#     # Score for admin UI (0–100)
#     score_parts = []
#     for v in (name_vs_extract, number_vs_extract, dob_vs_extract, name_vs_profile):
#         if v is True:
#             score_parts.append(1)
#         elif v is False:
#             score_parts.append(0)
#     match_score = int(round(100 * sum(score_parts) / len(score_parts))) if score_parts else None
#
#     if flags and any(f.endswith("_scan") for f in flags):
#         match_status = "mismatch"
#     elif has_extract and not flags:
#         match_status = "matched"
#     elif not has_extract:
#         match_status = "manual_review"  # no OCR — admin checks images
#     else:
#         match_status = "partial"
#
#     return {
#         "has_extract": has_extract,
#         "match_status": match_status,
#         "match_score": match_score,
#         "checks": checks,
#         "flags": flags,
#     }
#
#
# def _ext_from_content_type(content_type: str) -> str:
#     ct = (content_type or "").lower()
#     if "png" in ct:
#         return "png"
#     if "webp" in ct:
#         return "webp"
#     if "gif" in ct:
#         return "gif"
#     return "jpg"
#
#
# async def _read_image_bytes(request: Request) -> tuple[bytes, str]:
#     content_type = (request.headers.get("content-type") or "").lower()
#
#     if "multipart/form-data" in content_type:
#         form = await request.form()
#         file = (
#             form.get("file")
#             or form.get("photo")
#             or form.get("image")
#             or form.get("document")
#         )
#         if file is None:
#             raise HTTPException(
#                 status_code=400,
#                 detail="No file field. Use: file | photo | image | document",
#             )
#         if hasattr(file, "read"):
#             body = await file.read()
#             ct = getattr(file, "content_type", None) or "image/jpeg"
#         else:
#             raise HTTPException(status_code=400, detail="Invalid file field")
#         if not body:
#             raise HTTPException(status_code=400, detail="Empty file")
#         if not str(ct).startswith("image/"):
#             ct = "image/jpeg"
#         return body, str(ct)
#
#     body = await request.body()
#     if not body:
#         raise HTTPException(status_code=400, detail="No file received")
#     ct = content_type if content_type.startswith("image/") else "image/jpeg"
#     return body, ct
#
#
# def _require_admin(request: Request, current_user: dict):
#     env = request.scope.get("env")
#     raw = (getattr(env, "ADMIN_USER_IDS", None) or "").strip()
#     allowed = {x.strip() for x in raw.split(",") if x.strip()}
#     if not allowed or current_user["id"] not in allowed:
#         raise HTTPException(status_code=403, detail="Admin only")
#
#
# def _row_to_status(r: dict) -> dict:
#     st = (r.get("status") or "none").lower()
#     match_report = {}
#     raw_match = r.get("match_report")
#     if raw_match:
#         try:
#             match_report = json.loads(raw_match) if isinstance(raw_match, str) else raw_match
#         except Exception:
#             match_report = {}
#
#     return {
#         "status": st,
#         "verified": st == "verified",
#         "rejection_reason": r.get("rejection_reason"),
#         "doc_type": r.get("doc_type"),
#         "doc_number": r.get("doc_number"),
#         "name_on_document": r.get("name_on_document"),
#         "date_of_birth": r.get("date_of_birth"),
#         "document_url": r.get("document_url") or r.get("document_front_url"),
#         "document_front_url": r.get("document_front_url") or r.get("document_url"),
#         "document_back_url": r.get("document_back_url"),
#         "selfie_url": r.get("selfie_url"),
#         "address_line": r.get("address_line"),
#         "pincode": r.get("pincode"),
#         "document_expiry": r.get("document_expiry"),
#         "match_status": r.get("match_status") or match_report.get("match_status"),
#         "match_score": r.get("match_score") if r.get("match_score") is not None else match_report.get("match_score"),
#         "match_flags": match_report.get("flags") or [],
#         "match_checks": match_report.get("checks") or {},
#         "updated_at": r.get("updated_at") or r.get("created_at"),
#         "created_at": r.get("created_at"),
#     }
#
#
# # ─────────────────────────────────────────────
# # Upload to kyc/* R2 path (not profile)
# # ─────────────────────────────────────────────
# @router.post("/kyc/upload")
# async def kyc_upload(
#     request: Request,
#     current_user: dict = Depends(get_current_user),
#     kind: str = Query("document", description="document | document_back | selfie"),
# ):
#     """
#     POST /api/kyc/upload?kind=document|document_back|selfie
#     multipart field: file | photo | image | document
#     """
#     kind = (kind or "document").lower().strip()
#     folder = {
#         "document": "document",
#         "front": "document",
#         "document_front": "document",
#         "document_back": "document_back",
#         "back": "document_back",
#         "selfie": "selfie",
#     }.get(kind)
#     if not folder:
#         raise HTTPException(
#             status_code=400,
#             detail="kind must be document | document_back | selfie",
#         )
#
#     body, content_type = await _read_image_bytes(request)
#     user_id = current_user["id"]
#     ext = _ext_from_content_type(content_type)
#     file_id = str(uuid.uuid4())[:8]
#     key = f"kyc/{user_id}/{folder}/{file_id}.{ext}"
#
#     images = request.scope["env"].IMAGES
#     await images.put(key, body, httpMetadata={"contentType": content_type})
#     url = f"{R2_PUBLIC_URL}/{key}"
#
#     return {
#         "kind": folder,
#         "url": url,
#         "message": f"KYC {folder} uploaded",
#     }
#
#
# # ─────────────────────────────────────────────
# # Status
# # ─────────────────────────────────────────────
# @router.get("/kyc/status")
# async def kyc_status(
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     row = await db.prepare(
#         "SELECT * FROM kyc WHERE user_id = ?"
#     ).bind(current_user["id"]).first()
#
#     if not row:
#         return {
#             "status": "none",
#             "verified": False,
#             "rejection_reason": None,
#         }
#
#     return _row_to_status(dict(row))
#
#
# # ─────────────────────────────────────────────
# # Submit / resubmit
# # ─────────────────────────────────────────────
# @router.post("/kyc", status_code=status.HTTP_201_CREATED)
# async def submit_kyc(
#     data: KycSubmitRequest,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     """
#     Submit KYC with filled fields + image URLs.
#     Optional extracted_* fields = on-device OCR / scan; server compares to filled data.
#     Does NOT auto-verify. Status stays pending for admin.
#     """
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#     profile_name = current_user.get("full_name") or ""
#
#     doc_type = (data.doc_type or data.docType or "").strip().lower()
#     doc_number = (data.doc_number or data.docNumber or "").strip()
#     name_on_document = (data.name_on_document or data.nameOnDocument or "").strip()
#     date_of_birth = (data.date_of_birth or data.dateOfBirth or "").strip()
#
#     document_front = (
#         data.document_front_url
#         or data.documentFrontUrl
#         or data.document_url
#         or data.documentUrl
#     )
#     document_back = data.document_back_url or data.documentBackUrl
#     selfie_url = data.selfie_url or data.selfieUrl
#     address_line = (data.address_line or data.addressLine or "").strip() or None
#     pincode = (data.pincode or "").strip() or None
#     document_expiry = (data.document_expiry or data.documentExpiry or "").strip() or None
#
#     extracted_name = (data.extracted_name or data.extractedName or "").strip()
#     extracted_doc_number = (data.extracted_doc_number or data.extractedDocNumber or "").strip()
#     extracted_dob = (data.extracted_dob or data.extractedDob or "").strip()
#
#     if not doc_type or doc_type not in ALLOWED_DOC_TYPES:
#         raise HTTPException(
#             status_code=400,
#             detail=f"doc_type must be one of: {', '.join(sorted(ALLOWED_DOC_TYPES))}",
#         )
#     if not doc_number:
#         raise HTTPException(status_code=400, detail="doc_number is required")
#     if not name_on_document:
#         raise HTTPException(status_code=400, detail="name_on_document is required")
#     if not date_of_birth:
#         raise HTTPException(status_code=400, detail="date_of_birth is required (YYYY-MM-DD)")
#     if not document_front:
#         raise HTTPException(status_code=400, detail="document_front_url is required")
#     if not selfie_url:
#         raise HTTPException(status_code=400, detail="selfie_url is required")
#     if data.declaration_accepted is False:
#         raise HTTPException(status_code=400, detail="declaration_accepted must be true")
#
#     # Aadhaar / DL: back recommended (soft flag only)
#     match_report = _build_match_report(
#         name_on_document=name_on_document,
#         doc_number=doc_number,
#         date_of_birth=date_of_birth,
#         extracted_name=extracted_name,
#         extracted_doc_number=extracted_doc_number,
#         extracted_dob=extracted_dob,
#         profile_name=profile_name,
#     )
#     if doc_type in ("aadhaar", "driving_license") and not document_back:
#         match_report.setdefault("flags", []).append("missing_document_back")
#         if match_report.get("match_status") == "matched":
#             match_report["match_status"] = "partial"
#
#     # Hard fail only when OCR provided AND critical mismatch
#     hard = [f for f in match_report.get("flags", []) if f.endswith("_scan")]
#     if hard:
#         # Still allow submit, but mark mismatch for admin (do not block user)
#         pass
#
#     existing = await db.prepare(
#         "SELECT id, status FROM kyc WHERE user_id = ?"
#     ).bind(user_id).first()
#
#     if existing and dict(existing).get("status") == "verified":
#         raise HTTPException(status_code=400, detail="KYC already verified")
#
#     match_json = json.dumps(match_report)
#     match_status = match_report.get("match_status")
#     match_score = match_report.get("match_score")
#
#     if existing:
#         await db.prepare(
#             """
#             UPDATE kyc SET
#                 doc_type = ?,
#                 doc_number = ?,
#                 name_on_document = ?,
#                 date_of_birth = ?,
#                 document_url = ?,
#                 document_front_url = ?,
#                 document_back_url = ?,
#                 selfie_url = ?,
#                 address_line = ?,
#                 pincode = ?,
#                 document_expiry = ?,
#                 match_status = ?,
#                 match_score = ?,
#                 match_report = ?,
#                 status = 'pending',
#                 rejection_reason = NULL,
#                 updated_at = CURRENT_TIMESTAMP
#             WHERE user_id = ?
#             """
#         ).bind(
#             doc_type,
#             doc_number,
#             name_on_document,
#             date_of_birth,
#             document_front,
#             document_front,
#             document_back,
#             selfie_url,
#             address_line,
#             pincode,
#             document_expiry,
#             match_status,
#             match_score,
#             match_json,
#             user_id,
#         ).run()
#     else:
#         kyc_id = secrets.token_hex(8)
#         await db.prepare(
#             """
#             INSERT INTO kyc (
#                 id, user_id, doc_type, doc_number,
#                 name_on_document, date_of_birth,
#                 document_url, document_front_url, document_back_url, selfie_url,
#                 address_line, pincode, document_expiry,
#                 match_status, match_score, match_report,
#                 status
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
#             """
#         ).bind(
#             kyc_id,
#             user_id,
#             doc_type,
#             doc_number,
#             name_on_document,
#             date_of_birth,
#             document_front,
#             document_front,
#             document_back,
#             selfie_url,
#             address_line,
#             pincode,
#             document_expiry,
#             match_status,
#             match_score,
#             match_json,
#         ).run()
#
#     return {
#         "status": "pending",
#         "verified": False,
#         "match_status": match_status,
#         "match_score": match_score,
#         "match_flags": match_report.get("flags") or [],
#         "message": "KYC submitted successfully. Pending admin review.",
#     }
#
#
# # ─────────────────────────────────────────────
# # Admin
# # ─────────────────────────────────────────────
# @router.get("/admin/kyc")
# async def admin_list_kyc(
#     request: Request,
#     current_user: dict = Depends(get_current_user),
#     status_filter: Optional[str] = Query(None, alias="status"),
#     limit: int = Query(50, ge=1, le=100),
# ):
#     _require_admin(request, current_user)
#     db = request.scope["env"].DB
#
#     sql = """
#         SELECT k.*, u.full_name, u.email, u.mobile, u.city, u.image
#         FROM kyc k
#         LEFT JOIN users u ON u.id = k.user_id
#         WHERE 1=1
#     """
#     params = []
#     if status_filter:
#         sql += " AND LOWER(k.status) = ?"
#         params.append(status_filter.lower().strip())
#     sql += " ORDER BY k.created_at DESC LIMIT ?"
#     params.append(limit)
#
#     rows = await db.prepare(sql).bind(*params).all()
#     items = rows.results if hasattr(rows, "results") else rows
#     out = []
#     for row in items:
#         r = dict(row)
#         item = _row_to_status(r)
#         item["user_id"] = r.get("user_id")
#         item["full_name"] = r.get("full_name")
#         item["email"] = r.get("email")
#         item["mobile"] = r.get("mobile")
#         item["city"] = r.get("city")
#         item["profile_image"] = r.get("image")
#         out.append(item)
#
#     return {"count": len(out), "items": out}
#
#
# @router.get("/admin/kyc/{user_id}")
# async def admin_get_kyc(
#     user_id: str,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     _require_admin(request, current_user)
#     db = request.scope["env"].DB
#
#     row = await db.prepare(
#         """
#         SELECT k.*, u.full_name, u.email, u.mobile, u.city, u.image
#         FROM kyc k
#         LEFT JOIN users u ON u.id = k.user_id
#         WHERE k.user_id = ?
#         """
#     ).bind(user_id).first()
#     if not row:
#         raise HTTPException(status_code=404, detail="KYC not found")
#
#     r = dict(row)
#     item = _row_to_status(r)
#     item["user_id"] = user_id
#     item["full_name"] = r.get("full_name")
#     item["email"] = r.get("email")
#     item["mobile"] = r.get("mobile")
#     item["city"] = r.get("city")
#     item["profile_image"] = r.get("image")
#     return item
#
#
# @router.post("/admin/kyc/{user_id}/verify")
# async def admin_verify_kyc(
#     user_id: str,
#     data: KycVerifyRequest,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     _require_admin(request, current_user)
#     db = request.scope["env"].DB
#
#     row = await db.prepare(
#         "SELECT id, status FROM kyc WHERE user_id = ?"
#     ).bind(user_id).first()
#     if not row:
#         raise HTTPException(status_code=404, detail="No KYC submission found")
#
#     await db.prepare(
#         """
#         UPDATE kyc
#         SET status = 'verified',
#             rejection_reason = NULL,
#             reviewed_by = ?,
#             reviewed_at = CURRENT_TIMESTAMP,
#             admin_note = ?,
#             updated_at = CURRENT_TIMESTAMP
#         WHERE user_id = ?
#         """
#     ).bind(current_user["id"], data.admin_note, user_id).run()
#
#     return {
#         "user_id": user_id,
#         "status": "verified",
#         "verified": True,
#         "message": "KYC verified",
#     }
#
#
# @router.post("/admin/kyc/{user_id}/reject")
# async def admin_reject_kyc(
#     user_id: str,
#     data: KycRejectRequest,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     _require_admin(request, current_user)
#     db = request.scope["env"].DB
#
#     row = await db.prepare(
#         "SELECT id FROM kyc WHERE user_id = ?"
#     ).bind(user_id).first()
#     if not row:
#         raise HTTPException(status_code=404, detail="No KYC submission found")
#
#     reason = data.rejection_reason.strip()
#     await db.prepare(
#         """
#         UPDATE kyc
#         SET status = 'rejected',
#             rejection_reason = ?,
#             reviewed_by = ?,
#             reviewed_at = CURRENT_TIMESTAMP,
#             admin_note = ?,
#             updated_at = CURRENT_TIMESTAMP
#         WHERE user_id = ?
#         """
#     ).bind(reason, current_user["id"], data.admin_note, user_id).run()
#
#     return {
#         "user_id": user_id,
#         "status": "rejected",
#         "verified": False,
#         "rejection_reason": reason,
#         "message": "KYC rejected",
#     }



from fastapi import APIRouter, Request, Depends, HTTPException, status, Query
from routes.profile import get_current_user
from pydantic import BaseModel, Field
from typing import Optional, List
import secrets
import json
import re
import uuid

router = APIRouter()

R2_PUBLIC_URL = "https://pub-da3163e6bec745449d684b720f3a6b4c.r2.dev"

ALLOWED_DOC_TYPES = {"aadhaar", "pan", "passport", "driving_license"}


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class KycSubmitRequest(BaseModel):
    doc_type: Optional[str] = None
    doc_number: Optional[str] = None
    name_on_document: Optional[str] = None
    date_of_birth: Optional[str] = None  # YYYY-MM-DD

    # Images — front + selfie only (no back)
    document_url: Optional[str] = None
    document_front_url: Optional[str] = None
    selfie_url: Optional[str] = None

    address_line: Optional[str] = None
    pincode: Optional[str] = None
    document_expiry: Optional[str] = None

    declaration_accepted: Optional[bool] = True

    extracted_name: Optional[str] = None
    extracted_doc_number: Optional[str] = None
    extracted_dob: Optional[str] = None

    # Flutter camelCase
    docType: Optional[str] = None
    docNumber: Optional[str] = None
    nameOnDocument: Optional[str] = None
    dateOfBirth: Optional[str] = None
    documentUrl: Optional[str] = None
    documentFrontUrl: Optional[str] = None
    selfieUrl: Optional[str] = None
    addressLine: Optional[str] = None
    documentExpiry: Optional[str] = None
    extractedName: Optional[str] = None
    extractedDocNumber: Optional[str] = None
    extractedDob: Optional[str] = None


class KycRejectRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=3, max_length=500)
    admin_note: Optional[str] = None


class KycVerifyRequest(BaseModel):
    admin_note: Optional[str] = None


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _norm(s: Optional[str]) -> str:
    if not s:
        return ""
    s = str(s).strip().lower()
    s = re.sub(r"[^a-z0-9]", "", s)
    return s


def _norm_name(s: Optional[str]) -> str:
    if not s:
        return ""
    s = str(s).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _names_match(a: str, b: str) -> bool:
    a, b = _norm_name(a), _norm_name(b)
    if not a or not b:
        return False
    if a == b:
        return True
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return False
    shorter, longer = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    return shorter.issubset(longer)


def _docs_match(a: str, b: str) -> bool:
    return _norm(a) == _norm(b) and bool(_norm(a))


def _dob_match(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return _norm(a) == _norm(b)


def _build_match_report(
    name_on_document: str,
    doc_number: str,
    date_of_birth: str,
    extracted_name: str,
    extracted_doc_number: str,
    extracted_dob: str,
    profile_name: str,
) -> dict:
    flags: List[str] = []
    checks = {}

    has_extract = bool(extracted_name or extracted_doc_number or extracted_dob)

    name_vs_extract = (
        _names_match(name_on_document, extracted_name) if extracted_name else None
    )
    number_vs_extract = (
        _docs_match(doc_number, extracted_doc_number) if extracted_doc_number else None
    )
    dob_vs_extract = (
        _dob_match(date_of_birth, extracted_dob) if extracted_dob else None
    )
    name_vs_profile = (
        _names_match(name_on_document, profile_name) if profile_name else None
    )

    checks["name_matches_extract"] = name_vs_extract
    checks["number_matches_extract"] = number_vs_extract
    checks["dob_matches_extract"] = dob_vs_extract
    checks["name_matches_profile"] = name_vs_profile

    if has_extract:
        if name_vs_extract is False:
            flags.append("name_mismatch_scan")
        if number_vs_extract is False:
            flags.append("doc_number_mismatch_scan")
        if dob_vs_extract is False:
            flags.append("dob_mismatch_scan")

    if name_vs_profile is False:
        flags.append("name_mismatch_profile")
    if not name_on_document:
        flags.append("missing_name_on_document")
    if not doc_number:
        flags.append("missing_doc_number")
    if not date_of_birth:
        flags.append("missing_dob")

    score_parts = []
    for v in (name_vs_extract, number_vs_extract, dob_vs_extract, name_vs_profile):
        if v is True:
            score_parts.append(1)
        elif v is False:
            score_parts.append(0)
    match_score = (
        int(round(100 * sum(score_parts) / len(score_parts))) if score_parts else None
    )

    if flags and any(f.endswith("_scan") for f in flags):
        match_status = "mismatch"
    elif has_extract and not flags:
        match_status = "matched"
    elif not has_extract:
        match_status = "manual_review"
    else:
        match_status = "partial"

    return {
        "has_extract": has_extract,
        "match_status": match_status,
        "match_score": match_score,
        "checks": checks,
        "flags": flags,
    }


def _ext_from_content_type(content_type: str) -> str:
    ct = (content_type or "").lower()
    if "png" in ct:
        return "png"
    if "webp" in ct:
        return "webp"
    if "gif" in ct:
        return "gif"
    return "jpg"


async def _read_image_bytes(request: Request) -> tuple[bytes, str]:
    content_type = (request.headers.get("content-type") or "").lower()

    if "multipart/form-data" in content_type:
        try:
            form = await request.form()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Multipart parse failed: {e}")

        file = (
            form.get("file")
            or form.get("photo")
            or form.get("image")
            or form.get("document")
        )
        if file is None:
            raise HTTPException(
                status_code=400,
                detail="No file field. Use: file | photo | image | document",
            )
        if hasattr(file, "read"):
            body = await file.read()
            ct = getattr(file, "content_type", None) or "image/jpeg"
        elif isinstance(file, (bytes, bytearray)):
            body = bytes(file)
            ct = "image/jpeg"
        else:
            raise HTTPException(status_code=400, detail="Invalid file field")
        if not body:
            raise HTTPException(status_code=400, detail="Empty file")
        if not str(ct).startswith("image/"):
            ct = "image/jpeg"
        return body, str(ct)

    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="No file received")
    ct = content_type if content_type.startswith("image/") else "image/jpeg"
    return body, ct


def _require_admin(request: Request, current_user: dict):
    env = request.scope.get("env")
    raw = (getattr(env, "ADMIN_USER_IDS", None) or "").strip()
    allowed = {x.strip() for x in raw.split(",") if x.strip()}
    if not allowed or current_user["id"] not in allowed:
        raise HTTPException(status_code=403, detail="Admin only")


def _row_to_status(r: dict) -> dict:
    st = (r.get("status") or "none").lower()
    match_report = {}
    raw_match = r.get("match_report")
    if raw_match:
        try:
            match_report = (
                json.loads(raw_match) if isinstance(raw_match, str) else raw_match
            )
        except Exception:
            match_report = {}

    doc_url = r.get("document_front_url") or r.get("document_url")

    return {
        "status": st,
        "verified": st == "verified",
        "rejection_reason": r.get("rejection_reason"),
        "doc_type": r.get("doc_type"),
        "doc_number": r.get("doc_number"),
        "name_on_document": r.get("name_on_document"),
        "date_of_birth": r.get("date_of_birth"),
        "document_url": doc_url,
        "document_front_url": doc_url,
        "selfie_url": r.get("selfie_url"),
        "address_line": r.get("address_line"),
        "pincode": r.get("pincode"),
        "document_expiry": r.get("document_expiry"),
        "match_status": r.get("match_status") or match_report.get("match_status"),
        "match_score": (
            r.get("match_score")
            if r.get("match_score") is not None
            else match_report.get("match_score")
        ),
        "match_flags": match_report.get("flags") or [],
        "match_checks": match_report.get("checks") or {},
        "updated_at": r.get("updated_at") or r.get("created_at"),
        "created_at": r.get("created_at"),
    }


# ─────────────────────────────────────────────
# Upload — document (front) | selfie only
# ─────────────────────────────────────────────
@router.post("/kyc/upload")
async def kyc_upload(
    request: Request,
    current_user: dict = Depends(get_current_user),
    kind: str = Query("document", description="document | selfie"),
):
    """
    POST /api/kyc/upload?kind=document|selfie
    multipart: file | photo | image | document
    """
    kind = (kind or "document").lower().strip()
    folder = {
        "document": "document",
        "front": "document",
        "document_front": "document",
        "selfie": "selfie",
    }.get(kind)
    if not folder:
        raise HTTPException(
            status_code=400,
            detail="kind must be document or selfie",
        )

    try:
        body, content_type = await _read_image_bytes(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read image: {e}")

    if not body:
        raise HTTPException(status_code=400, detail="Empty file")

    user_id = current_user["id"]
    ext = _ext_from_content_type(content_type)
    file_id = str(uuid.uuid4())[:8]
    key = f"kyc/{user_id}/{folder}/{file_id}.{ext}"

    env = request.scope.get("env")
    if env is None:
        raise HTTPException(status_code=500, detail="Worker env missing")

    images = getattr(env, "IMAGES", None)
    if images is None:
        raise HTTPException(status_code=500, detail="R2 IMAGES binding not configured")

    try:
        await images.put(
            key,
            body,
            httpMetadata={"contentType": content_type or "image/jpeg"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"R2 upload failed: {e}")

    url = f"{R2_PUBLIC_URL}/{key}"
    return {
        "kind": folder,
        "url": url,
        "message": f"KYC {folder} uploaded",
    }


# ─────────────────────────────────────────────
# Status
# ─────────────────────────────────────────────
@router.get("/kyc/status")
async def kyc_status(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    row = await db.prepare(
        "SELECT * FROM kyc WHERE user_id = ?"
    ).bind(current_user["id"]).first()

    if not row:
        return {
            "status": "none",
            "verified": False,
            "rejection_reason": None,
        }

    return _row_to_status(dict(row))


# ─────────────────────────────────────────────
# Submit
# ─────────────────────────────────────────────
@router.post("/kyc", status_code=status.HTTP_201_CREATED)
async def submit_kyc(
    data: KycSubmitRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]
    profile_name = current_user.get("full_name") or ""

    doc_type = (data.doc_type or data.docType or "").strip().lower()
    doc_number = (data.doc_number or data.docNumber or "").strip()
    name_on_document = (data.name_on_document or data.nameOnDocument or "").strip()
    date_of_birth = (data.date_of_birth or data.dateOfBirth or "").strip()

    document_front = (
        data.document_front_url
        or data.documentFrontUrl
        or data.document_url
        or data.documentUrl
    )
    selfie_url = data.selfie_url or data.selfieUrl
    address_line = (data.address_line or data.addressLine or "").strip() or None
    pincode = (data.pincode or "").strip() or None
    document_expiry = (data.document_expiry or data.documentExpiry or "").strip() or None

    extracted_name = (data.extracted_name or data.extractedName or "").strip()
    extracted_doc_number = (
        data.extracted_doc_number or data.extractedDocNumber or ""
    ).strip()
    extracted_dob = (data.extracted_dob or data.extractedDob or "").strip()

    if not doc_type or doc_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"doc_type must be one of: {', '.join(sorted(ALLOWED_DOC_TYPES))}",
        )
    if not doc_number:
        raise HTTPException(status_code=400, detail="doc_number is required")
    if not name_on_document:
        raise HTTPException(status_code=400, detail="name_on_document is required")
    if not date_of_birth:
        raise HTTPException(
            status_code=400, detail="date_of_birth is required (YYYY-MM-DD)"
        )
    if not document_front:
        raise HTTPException(status_code=400, detail="document_url is required")
    if not selfie_url:
        raise HTTPException(status_code=400, detail="selfie_url is required")
    if data.declaration_accepted is False:
        raise HTTPException(
            status_code=400, detail="declaration_accepted must be true"
        )

    match_report = _build_match_report(
        name_on_document=name_on_document,
        doc_number=doc_number,
        date_of_birth=date_of_birth,
        extracted_name=extracted_name,
        extracted_doc_number=extracted_doc_number,
        extracted_dob=extracted_dob,
        profile_name=profile_name,
    )

    existing = await db.prepare(
        "SELECT id, status FROM kyc WHERE user_id = ?"
    ).bind(user_id).first()

    if existing and dict(existing).get("status") == "verified":
        raise HTTPException(status_code=400, detail="KYC already verified")

    match_json = json.dumps(match_report)
    match_status = match_report.get("match_status")
    match_score = match_report.get("match_score")

    if existing:
        await db.prepare(
            """
            UPDATE kyc SET
                doc_type = ?,
                doc_number = ?,
                name_on_document = ?,
                date_of_birth = ?,
                document_url = ?,
                document_front_url = ?,
                document_back_url = NULL,
                selfie_url = ?,
                address_line = ?,
                pincode = ?,
                document_expiry = ?,
                match_status = ?,
                match_score = ?,
                match_report = ?,
                status = 'pending',
                rejection_reason = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """
        ).bind(
            doc_type,
            doc_number,
            name_on_document,
            date_of_birth,
            document_front,
            document_front,
            selfie_url,
            address_line,
            pincode,
            document_expiry,
            match_status,
            match_score,
            match_json,
            user_id,
        ).run()
    else:
        kyc_id = secrets.token_hex(8)
        await db.prepare(
            """
            INSERT INTO kyc (
                id, user_id, doc_type, doc_number,
                name_on_document, date_of_birth,
                document_url, document_front_url, document_back_url, selfie_url,
                address_line, pincode, document_expiry,
                match_status, match_score, match_report,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """
        ).bind(
            kyc_id,
            user_id,
            doc_type,
            doc_number,
            name_on_document,
            date_of_birth,
            document_front,
            document_front,
            selfie_url,
            address_line,
            pincode,
            document_expiry,
            match_status,
            match_score,
            match_json,
        ).run()

    return {
        "status": "pending",
        "verified": False,
        "match_status": match_status,
        "match_score": match_score,
        "match_flags": match_report.get("flags") or [],
        "message": "KYC submitted successfully. Pending admin review.",
    }


# ─────────────────────────────────────────────
# Admin
# ─────────────────────────────────────────────
@router.get("/admin/kyc")
async def admin_list_kyc(
    request: Request,
    current_user: dict = Depends(get_current_user),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
):
    _require_admin(request, current_user)
    db = request.scope["env"].DB

    sql = """
        SELECT k.*, u.full_name, u.email, u.mobile, u.city, u.image
        FROM kyc k
        LEFT JOIN users u ON u.id = k.user_id
        WHERE 1=1
    """
    params = []
    if status_filter:
        sql += " AND LOWER(k.status) = ?"
        params.append(status_filter.lower().strip())
    sql += " ORDER BY k.created_at DESC LIMIT ?"
    params.append(limit)

    rows = await db.prepare(sql).bind(*params).all()
    items = rows.results if hasattr(rows, "results") else rows
    out = []
    for row in items:
        r = dict(row)
        item = _row_to_status(r)
        item["user_id"] = r.get("user_id")
        item["full_name"] = r.get("full_name")
        item["email"] = r.get("email")
        item["mobile"] = r.get("mobile")
        item["city"] = r.get("city")
        item["profile_image"] = r.get("image")
        out.append(item)

    return {"count": len(out), "items": out}


@router.get("/admin/kyc/{user_id}")
async def admin_get_kyc(
    user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    _require_admin(request, current_user)
    db = request.scope["env"].DB

    row = await db.prepare(
        """
        SELECT k.*, u.full_name, u.email, u.mobile, u.city, u.image
        FROM kyc k
        LEFT JOIN users u ON u.id = k.user_id
        WHERE k.user_id = ?
        """
    ).bind(user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="KYC not found")

    r = dict(row)
    item = _row_to_status(r)
    item["user_id"] = user_id
    item["full_name"] = r.get("full_name")
    item["email"] = r.get("email")
    item["mobile"] = r.get("mobile")
    item["city"] = r.get("city")
    item["profile_image"] = r.get("image")
    return item


@router.post("/admin/kyc/{user_id}/verify")
async def admin_verify_kyc(
    user_id: str,
    data: KycVerifyRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    _require_admin(request, current_user)
    db = request.scope["env"].DB

    row = await db.prepare(
        "SELECT id, status FROM kyc WHERE user_id = ?"
    ).bind(user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="No KYC submission found")

    await db.prepare(
        """
        UPDATE kyc
        SET status = 'verified',
            rejection_reason = NULL,
            reviewed_by = ?,
            reviewed_at = CURRENT_TIMESTAMP,
            admin_note = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """
    ).bind(current_user["id"], data.admin_note, user_id).run()

    return {
        "user_id": user_id,
        "status": "verified",
        "verified": True,
        "message": "KYC verified",
    }


@router.post("/admin/kyc/{user_id}/reject")
async def admin_reject_kyc(
    user_id: str,
    data: KycRejectRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    _require_admin(request, current_user)
    db = request.scope["env"].DB

    row = await db.prepare(
        "SELECT id FROM kyc WHERE user_id = ?"
    ).bind(user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="No KYC submission found")

    reason = data.rejection_reason.strip()
    await db.prepare(
        """
        UPDATE kyc
        SET status = 'rejected',
            rejection_reason = ?,
            reviewed_by = ?,
            reviewed_at = CURRENT_TIMESTAMP,
            admin_note = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """
    ).bind(reason, current_user["id"], data.admin_note, user_id).run()

    return {
        "user_id": user_id,
        "status": "rejected",
        "verified": False,
        "rejection_reason": reason,
        "message": "KYC rejected",
    }