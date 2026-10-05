from fastapi import APIRouter, Request, Depends, HTTPException, status
from routes.profile import get_current_user
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import secrets

router = APIRouter()


class WalletTopUpRequest(BaseModel):
    amount: float = Field(..., ge=100)
    method: Optional[str] = "UPI"


def _format_date(iso_str: str | None) -> str:
    if not iso_str:
        return ""
    try:
        # D1 CURRENT_TIMESTAMP style
        dt = datetime.fromisoformat(iso_str.replace("Z", ""))
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(iso_str)


def _tx_row(row: dict) -> dict:
    amount = float(row.get("amount") or 0)
    category = row.get("category") or ("Added" if amount > 0 else "Spent")
    return {
        "id": row["id"],
        "type": row.get("type") or "Wallet Transaction",
        "subtitle": row.get("subtitle") or "",
        "date": _format_date(row.get("created_at")),
        "created_at": row.get("created_at"),
        "amount": amount,
        "category": category,
        "booking_id": row.get("booking_id"),
    }


@router.get("/wallet")
async def get_wallet(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Wallet balance + stats + transactions for WalletPage.jsx
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]

    user = await db.prepare(
        """
        SELECT id, wallet_balance, total_added, total_spent, want_to
        FROM users WHERE id = ?
        """
    ).bind(user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    u = dict(user)
    balance = float(u.get("wallet_balance") or 0)
    total_added = float(u.get("total_added") or 0)
    total_spent = float(u.get("total_spent") or 0)

    rows = await db.prepare(
        """
        SELECT * FROM wallet_transactions
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
        """
    ).bind(user_id).all()

    items = rows.results if hasattr(rows, "results") else rows
    transactions = [_tx_row(dict(r)) for r in items]

    last_added_note = ""
    for t in transactions:
        if t["category"] == "Added" and t["amount"] > 0:
            last_added_note = f"+ ₹{int(t['amount']):,} added on {t['date'].split(',')[0] if t['date'] else ''}".strip()
            break

    return {
        "wallet_balance": balance,
        "walletBalance": balance,
        "total_added": total_added,
        "totalAdded": total_added,
        "total_spent": total_spent,
        "totalSpent": total_spent,
        "last_added_note": last_added_note or None,
        "want_to": u.get("want_to") or "",
        "transactions": transactions,
        "wallet": {
            "balance": balance,
            "transactions": transactions,
        },
    }


@router.post("/wallet/top-up", status_code=status.HTTP_201_CREATED)
async def wallet_top_up(
    data: WalletTopUpRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Add money to wallet (simulated — no real payment gateway yet).
    Frontend: amount >= 100
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]
    amount = float(data.amount)

    if amount < 100:
        raise HTTPException(status_code=400, detail="Minimum top-up is ₹100")

    method = (data.method or "UPI").strip() or "UPI"
    tx_id = secrets.token_hex(8)

    # Credit balance
    await db.prepare(
        """
        UPDATE users
        SET wallet_balance = COALESCE(wallet_balance, 0) + ?,
            total_added = COALESCE(total_added, 0) + ?
        WHERE id = ?
        """
    ).bind(amount, amount, user_id).run()

    await db.prepare(
        """
        INSERT INTO wallet_transactions (id, user_id, type, subtitle, amount, category)
        VALUES (?, ?, ?, ?, ?, ?)
        """
    ).bind(
        tx_id,
        user_id,
        "Wallet Top Up",
        f"Added via {method}",
        amount,
        "Added",
    ).run()

    user = await db.prepare(
        "SELECT wallet_balance, total_added, total_spent FROM users WHERE id = ?"
    ).bind(user_id).first()
    u = dict(user) if user else {}

    return {
        "message": "Money added successfully",
        "transaction_id": tx_id,
        "amount": amount,
        "wallet_balance": float(u.get("wallet_balance") or 0),
        "total_added": float(u.get("total_added") or 0),
        "total_spent": float(u.get("total_spent") or 0),
    }


@router.get("/wallet/transactions")
async def wallet_transactions(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    rows = await db.prepare(
        """
        SELECT * FROM wallet_transactions
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 100
        """
    ).bind(user_id).all()

    items = rows.results if hasattr(rows, "results") else rows
    transactions = [_tx_row(dict(r)) for r in items]

    return {"count": len(transactions), "transactions": transactions}