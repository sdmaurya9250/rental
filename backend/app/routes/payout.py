from fastapi import APIRouter, Request, Depends, HTTPException, status
from routes.profile import get_current_user
from pydantic import BaseModel, Field
from typing import Optional, Literal
import secrets
import re

router = APIRouter()


class PayoutMethodCreate(BaseModel):
    type: Literal["upi", "bank"]
    upi_id: Optional[str] = None
    account_holder: Optional[str] = None
    account_number: Optional[str] = None
    ifsc: Optional[str] = None
    bank_name: Optional[str] = None
    is_default: Optional[bool] = False


def _mask_account(num: str | None) -> str:
    if not num:
        return ""
    n = re.sub(r"\s+", "", num)
    if len(n) <= 4:
        return "****"
    return "X" * (len(n) - 4) + n[-4:]


def _format_method(row: dict) -> dict:
    t = (row.get("type") or "").lower()
    return {
        "id": row["id"],
        "type": t,
        "upi_id": row.get("upi_id") or None,
        "account_holder": row.get("account_holder") or None,
        "account_number": _mask_account(row.get("account_number")),
        "account_number_full": None,  # never return full number in list
        "ifsc": row.get("ifsc") or None,
        "bank_name": row.get("bank_name") or None,
        "is_default": bool(row.get("is_default", 0)),
        "created_at": row.get("created_at"),
        # display label for UI
        "label": (
            row.get("upi_id")
            if t == "upi"
            else f"{row.get('bank_name') or 'Bank'} · {_mask_account(row.get('account_number'))}"
        ),
    }


@router.get("/payout-methods")
async def list_payout_methods(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Companion: list saved UPI / bank accounts for withdraw."""
    db = request.scope["env"].DB
    user_id = current_user["id"]

    rows = await db.prepare(
        """
        SELECT * FROM payout_methods
        WHERE user_id = ?
        ORDER BY is_default DESC, created_at DESC
        """
    ).bind(user_id).all()

    items = rows.results if hasattr(rows, "results") else rows
    methods = [_format_method(dict(r)) for r in items]

    return {
        "count": len(methods),
        "methods": methods,
        "data": methods,  # Flutter-friendly alias
    }


@router.post("/payout-methods", status_code=status.HTTP_201_CREATED)
async def add_payout_method(
    data: PayoutMethodCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Add UPI or bank account.
    Body examples:
      { "type": "upi", "upi_id": "user@upi", "is_default": true }
      { "type": "bank", "account_holder": "Pavan", "account_number": "1234567890",
        "ifsc": "HDFC0001234", "bank_name": "HDFC", "is_default": true }
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]
    method_type = data.type.lower()

    if method_type == "upi":
        upi = (data.upi_id or "").strip()
        if not upi or "@" not in upi:
            raise HTTPException(status_code=400, detail="Valid upi_id is required (e.g. name@upi)")
        account_holder = account_number = ifsc = bank_name = None
        upi_id = upi
    else:
        account_holder = (data.account_holder or "").strip()
        account_number = re.sub(r"\s+", "", data.account_number or "")
        ifsc = (data.ifsc or "").strip().upper()
        bank_name = (data.bank_name or "").strip()
        upi_id = None

        if not account_holder or not account_number or not ifsc:
            raise HTTPException(
                status_code=400,
                detail="account_holder, account_number and ifsc are required for bank",
            )
        if len(ifsc) < 4:
            raise HTTPException(status_code=400, detail="Invalid IFSC")

    method_id = secrets.token_hex(8)
    is_default = 1 if data.is_default else 0

    # If default, clear other defaults
    if is_default:
        await db.prepare(
            "UPDATE payout_methods SET is_default = 0 WHERE user_id = ?"
        ).bind(user_id).run()

    # If first method, force default
    existing = await db.prepare(
        "SELECT COUNT(*) AS cnt FROM payout_methods WHERE user_id = ?"
    ).bind(user_id).first()
    cnt = int(dict(existing).get("cnt") or 0) if existing else 0
    if cnt == 0:
        is_default = 1

    await db.prepare(
        """
        INSERT INTO payout_methods (
            id, user_id, type, upi_id, account_holder,
            account_number, ifsc, bank_name, is_default
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    ).bind(
        method_id,
        user_id,
        method_type,
        upi_id,
        account_holder,
        account_number,
        ifsc,
        bank_name,
        is_default,
    ).run()

    row = await db.prepare(
        "SELECT * FROM payout_methods WHERE id = ?"
    ).bind(method_id).first()

    return {
        "message": "Payout method added",
        "method": _format_method(dict(row)),
    }


@router.post("/payout-methods/{method_id}/default")
async def set_default_payout(
    method_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT id FROM payout_methods WHERE id = ? AND user_id = ?"
    ).bind(method_id, user_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Payout method not found")

    await db.prepare(
        "UPDATE payout_methods SET is_default = 0 WHERE user_id = ?"
    ).bind(user_id).run()

    await db.prepare(
        "UPDATE payout_methods SET is_default = 1 WHERE id = ?"
    ).bind(method_id).run()

    return {"message": "Default payout method updated", "id": method_id}


@router.delete("/payout-methods/{method_id}")
async def delete_payout_method(
    method_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT id, is_default FROM payout_methods WHERE id = ? AND user_id = ?"
    ).bind(method_id, user_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Payout method not found")

    await db.prepare(
        "DELETE FROM payout_methods WHERE id = ? AND user_id = ?"
    ).bind(method_id, user_id).run()

    # If deleted was default, set another as default
    if int(dict(row).get("is_default") or 0) == 1:
        nxt = await db.prepare(
            """
            SELECT id FROM payout_methods
            WHERE user_id = ?
            ORDER BY created_at DESC LIMIT 1
            """
        ).bind(user_id).first()
        if nxt:
            await db.prepare(
                "UPDATE payout_methods SET is_default = 1 WHERE id = ?"
            ).bind(dict(nxt)["id"]).run()

    return {"message": "Payout method removed", "id": method_id}