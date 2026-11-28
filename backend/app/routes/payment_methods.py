from fastapi import APIRouter, Request, Depends, HTTPException, status
from routes.profile import get_current_user
from pydantic import BaseModel, Field
from typing import Optional, Literal
import secrets
import re

router = APIRouter()


class PaymentMethodCreate(BaseModel):
    type: Literal["upi", "card"]
    upi_id: Optional[str] = None
    # Card: client sends last4 + brand only (or full number we mask)
    card_number: Optional[str] = None
    card_last4: Optional[str] = None
    card_brand: Optional[str] = None
    card_holder: Optional[str] = None
    is_default: Optional[bool] = False


def _detect_brand(num: str) -> str:
    n = re.sub(r"\D", "", num)
    if n.startswith("4"):
        return "Visa"
    if n.startswith("5") or n.startswith("2"):
        return "Mastercard"
    if n.startswith("6"):
        return "RuPay"
    return "Card"


def _format_method(row: dict) -> dict:
    t = (row.get("type") or "").lower()
    if t == "upi":
        label = row.get("upi_id") or "UPI"
    else:
        brand = row.get("card_brand") or "Card"
        last4 = row.get("card_last4") or "****"
        label = f"{brand} ·••• {last4}"

    return {
        "id": row["id"],
        "type": t,
        "upi_id": row.get("upi_id"),
        "card_last4": row.get("card_last4"),
        "card_brand": row.get("card_brand"),
        "card_holder": row.get("card_holder"),
        "is_default": bool(row.get("is_default", 0)),
        "created_at": row.get("created_at"),
        "label": label,
    }


@router.get("/payment-methods")
async def list_payment_methods(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Finder: saved UPI / cards for paying."""
    db = request.scope["env"].DB
    user_id = current_user["id"]

    rows = await db.prepare(
        """
        SELECT * FROM payment_methods
        WHERE user_id = ?
        ORDER BY is_default DESC, created_at DESC
        """
    ).bind(user_id).all()

    items = rows.results if hasattr(rows, "results") else rows
    methods = [_format_method(dict(r)) for r in items]

    return {
        "count": len(methods),
        "methods": methods,
        "data": methods,
    }


@router.post("/payment-methods", status_code=status.HTTP_201_CREATED)
async def add_payment_method(
    data: PaymentMethodCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Add UPI or card (masked).
    { "type": "upi", "upi_id": "user@upi", "is_default": true }
    { "type": "card", "card_number": "4111111111111111", "card_holder": "Pavan", "is_default": true }
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]
    method_type = data.type.lower()

    upi_id = card_last4 = card_brand = card_holder = None

    if method_type == "upi":
        upi = (data.upi_id or "").strip()
        if not upi or "@" not in upi:
            raise HTTPException(status_code=400, detail="Valid upi_id required")
        upi_id = upi
    else:
        raw = re.sub(r"\D", "", data.card_number or "")
        last4 = (data.card_last4 or "").strip()
        if raw and len(raw) >= 4:
            card_last4 = raw[-4:]
            card_brand = data.card_brand or _detect_brand(raw)
        elif last4 and len(last4) == 4:
            card_last4 = last4
            card_brand = data.card_brand or "Card"
        else:
            raise HTTPException(
                status_code=400,
                detail="card_number or card_last4 required",
            )
        card_holder = (data.card_holder or "").strip() or None

    method_id = secrets.token_hex(8)
    is_default = 1 if data.is_default else 0

    if is_default:
        await db.prepare(
            "UPDATE payment_methods SET is_default = 0 WHERE user_id = ?"
        ).bind(user_id).run()

    existing = await db.prepare(
        "SELECT COUNT(*) AS cnt FROM payment_methods WHERE user_id = ?"
    ).bind(user_id).first()
    cnt = int(dict(existing).get("cnt") or 0) if existing else 0
    if cnt == 0:
        is_default = 1

    await db.prepare(
        """
        INSERT INTO payment_methods (
            id, user_id, type, upi_id, card_last4, card_brand, card_holder, is_default
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
    ).bind(
        method_id,
        user_id,
        method_type,
        upi_id,
        card_last4,
        card_brand,
        card_holder,
        is_default,
    ).run()

    row = await db.prepare(
        "SELECT * FROM payment_methods WHERE id = ?"
    ).bind(method_id).first()

    return {
        "message": "Payment method added",
        "method": _format_method(dict(row)),
    }


@router.post("/payment-methods/{method_id}/default")
async def set_default_payment(
    method_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT id FROM payment_methods WHERE id = ? AND user_id = ?"
    ).bind(method_id, user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Payment method not found")

    await db.prepare(
        "UPDATE payment_methods SET is_default = 0 WHERE user_id = ?"
    ).bind(user_id).run()
    await db.prepare(
        "UPDATE payment_methods SET is_default = 1 WHERE id = ?"
    ).bind(method_id).run()

    return {"message": "Default payment method updated", "id": method_id}


@router.delete("/payment-methods/{method_id}")
async def delete_payment_method(
    method_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT id, is_default FROM payment_methods WHERE id = ? AND user_id = ?"
    ).bind(method_id, user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Payment method not found")

    await db.prepare(
        "DELETE FROM payment_methods WHERE id = ? AND user_id = ?"
    ).bind(method_id, user_id).run()

    if int(dict(row).get("is_default") or 0) == 1:
        nxt = await db.prepare(
            """
            SELECT id FROM payment_methods
            WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
            """
        ).bind(user_id).first()
        if nxt:
            await db.prepare(
                "UPDATE payment_methods SET is_default = 1 WHERE id = ?"
            ).bind(dict(nxt)["id"]).run()

    return {"message": "Payment method removed", "id": method_id}