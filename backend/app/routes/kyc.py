# from fastapi import APIRouter, Request, Depends, HTTPException, status
# from routes.profile import get_current_user
# import secrets
# import json
#
# router = APIRouter()
# R2_PUBLIC_URL = "https://pub-da3163e6bec745449d684b720f3a6b4c.r2.dev"
#
#
# @router.get("/kyc/status")
# async def kyc_status(
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     row = await db.prepare(
#         "SELECT status, rejection_reason, updated_at FROM kyc WHERE user_id = ?"
#     ).bind(current_user["id"]).first()
#
#     if not row:
#         return {
#             "status": "none",
#             "verified": False,
#             "rejection_reason": None,
#         }
#
#     r = dict(row)
#     st = (r.get("status") or "none").lower()
#     return {
#         "status": st,  # none | pending | verified | rejected
#         "verified": st == "verified",
#         "rejection_reason": r.get("rejection_reason"),
#         "updated_at": r.get("updated_at"),
#     }
#
#
# @router.post("/kyc", status_code=status.HTTP_201_CREATED)
# async def submit_kyc(
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     """
#     Flutter multipart: doc_type, doc_number, document, selfie
#     If multipart is hard on Workers, accept JSON + prior R2 URLs:
#     { "doc_type", "doc_number", "document_url", "selfie_url" }
#     """
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#     content_type = (request.headers.get("content-type") or "").lower()
#
#     doc_type = doc_number = document_url = selfie_url = None
#
#     if "application/json" in content_type:
#         body = await request.json()
#         doc_type = (body.get("doc_type") or body.get("docType") or "").strip()
#         doc_number = (body.get("doc_number") or body.get("docNumber") or "").strip()
#         document_url = body.get("document_url") or body.get("documentUrl")
#         selfie_url = body.get("selfie_url") or body.get("selfieUrl")
#     else:
#         # Raw fallback: require JSON until multipart is wired
#         raise HTTPException(
#             status_code=400,
#             detail="Send JSON: doc_type, doc_number, document_url, selfie_url (upload files to R2 first)",
#         )
#
#     if not doc_type or not doc_number:
#         raise HTTPException(status_code=400, detail="doc_type and doc_number are required")
#
#     existing = await db.prepare(
#         "SELECT id, status FROM kyc WHERE user_id = ?"
#     ).bind(user_id).first()
#
#     kyc_id = secrets.token_hex(8)
#     status_val = "pending"
#
#     if existing:
#         await db.prepare(
#             """
#             UPDATE kyc SET
#                 doc_type = ?, doc_number = ?, document_url = ?, selfie_url = ?,
#                 status = ?, rejection_reason = NULL, updated_at = CURRENT_TIMESTAMP
#             WHERE user_id = ?
#             """
#         ).bind(
#             doc_type, doc_number, document_url, selfie_url, status_val, user_id
#         ).run()
#     else:
#         await db.prepare(
#             """
#             INSERT INTO kyc (
#                 id, user_id, doc_type, doc_number, document_url, selfie_url, status
#             ) VALUES (?, ?, ?, ?, ?, ?, ?)
#             """
#         ).bind(
#             kyc_id, user_id, doc_type, doc_number, document_url, selfie_url, status_val
#         ).run()
#
#     return {
#         "status": "pending",
#         "verified": False,
#         "message": "KYC submitted successfully",
#     }


from fastapi import APIRouter, Request, Depends, HTTPException, status
from routes.profile import get_current_user
from pydantic import BaseModel, Field
from typing import Optional
import secrets

router = APIRouter()


class KycSubmitRequest(BaseModel):
    doc_type: str = Field(..., min_length=1)       # aadhaar | pan | passport | driving_license
    doc_number: str = Field(..., min_length=1)
    document_url: Optional[str] = None
    selfie_url: Optional[str] = None
    # Flutter aliases
    docType: Optional[str] = None
    docNumber: Optional[str] = None
    documentUrl: Optional[str] = None
    selfieUrl: Optional[str] = None


@router.get("/kyc/status")
async def kyc_status(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Flutter: GET /api/kyc/status
    Returns: { status, verified }
    status: none | pending | verified | rejected
    """
    db = request.scope["env"].DB
    row = await db.prepare(
        """
        SELECT status, rejection_reason, doc_type, updated_at, created_at
        FROM kyc WHERE user_id = ?
        """
    ).bind(current_user["id"]).first()

    if not row:
        return {
            "status": "none",
            "verified": False,
            "rejection_reason": None,
        }

    r = dict(row)
    st = (r.get("status") or "none").lower()
    return {
        "status": st,
        "verified": st == "verified",
        "rejection_reason": r.get("rejection_reason"),
        "doc_type": r.get("doc_type"),
        "updated_at": r.get("updated_at") or r.get("created_at"),
    }


@router.post("/kyc", status_code=status.HTTP_201_CREATED)
async def submit_kyc(
    data: KycSubmitRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Flutter: POST /api/kyc
    JSON body (upload images via /api/profile/photo first, then send URLs):
    {
      "doc_type": "aadhaar",
      "doc_number": "XXXX-XXXX-XXXX",
      "document_url": "https://pub-....r2.dev/...",
      "selfie_url": "https://pub-....r2.dev/..."
    }
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]

    doc_type = (data.doc_type or data.docType or "").strip()
    doc_number = (data.doc_number or data.docNumber or "").strip()
    document_url = data.document_url or data.documentUrl
    selfie_url = data.selfie_url or data.selfieUrl

    if not doc_type or not doc_number:
        raise HTTPException(
            status_code=400,
            detail="doc_type and doc_number are required",
        )

    existing = await db.prepare(
        "SELECT id, status FROM kyc WHERE user_id = ?"
    ).bind(user_id).first()

    if existing and dict(existing).get("status") == "verified":
        raise HTTPException(
            status_code=400,
            detail="KYC already verified",
        )

    if existing:
        await db.prepare(
            """
            UPDATE kyc SET
                doc_type = ?,
                doc_number = ?,
                document_url = ?,
                selfie_url = ?,
                status = 'pending',
                rejection_reason = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """
        ).bind(
            doc_type,
            doc_number,
            document_url,
            selfie_url,
            user_id,
        ).run()
    else:
        kyc_id = secrets.token_hex(8)
        await db.prepare(
            """
            INSERT INTO kyc (
                id, user_id, doc_type, doc_number,
                document_url, selfie_url, status
            ) VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """
        ).bind(
            kyc_id,
            user_id,
            doc_type,
            doc_number,
            document_url,
            selfie_url,
        ).run()

    return {
        "status": "pending",
        "verified": False,
        "message": "KYC submitted successfully",
    }


@router.post("/kyc/verify")
async def admin_verify_kyc(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Optional admin/test helper: mark own KYC verified.
    Remove or protect in production.
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT id FROM kyc WHERE user_id = ?"
    ).bind(user_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="No KYC submission found")

    await db.prepare(
        """
        UPDATE kyc
        SET status = 'verified', rejection_reason = NULL,
            updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """
    ).bind(user_id).run()

    return {"status": "verified", "verified": True, "message": "KYC verified"}