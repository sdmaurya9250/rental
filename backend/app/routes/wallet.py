

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

class WalletWithdrawRequest(BaseModel):
    amount: float = Field(..., ge=100)
    note: Optional[str] = None

def _format_date(iso_str: str | None) -> str:
    if not iso_str:
        return ""
    try:
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
    Available balance = wallet_balance (can spend / withdraw)
    Held balance     = wallet_held (locked for pending/approved bookings)
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]

    user = await db.prepare(
        """
        SELECT id, wallet_balance, wallet_held, total_added, total_spent, want_to
        FROM users WHERE id = ?
        """
    ).bind(user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    u = dict(user)
    available = float(u.get("wallet_balance") or 0)
    held = float(u.get("wallet_held") or 0)
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
            day = t["date"].split(",")[0] if t["date"] else ""
            last_added_note = f"+ ₹{int(t['amount']):,} added on {day}".strip()
            break

    return {
        "wallet_balance": available,
        "walletBalance": available,
        "available_balance": available,
        "availableBalance": available,
        "wallet_held": held,
        "walletHeld": held,
        "held_balance": held,
        "heldBalance": held,
        "total_balance": available + held,
        "totalBalance": available + held,
        "total_added": total_added,
        "totalAdded": total_added,
        "total_spent": total_spent,
        "totalSpent": total_spent,
        "last_added_note": last_added_note or None,
        "want_to": u.get("want_to") or "",
        "transactions": transactions,
        "wallet": {
            "balance": available,
            "available": available,
            "held": held,
            "transactions": transactions,
        },
    }

@router.post("/wallet/top-up", status_code=status.HTTP_410_GONE)
async def wallet_top_up(
    data: WalletTopUpRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Disabled. It used to credit the wallet with no payment. Money is added
    only through the payment gateway flow (/api/payments/...)."""
    raise HTTPException(
        status_code=410,
        detail="Direct top-up is disabled. Add money through the payment flow.",
    )


@router.post("/wallet/withdraw")
async def wallet_withdraw(
    data: WalletWithdrawRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Withdraw from available balance only (not held).
    Flutter: POST /api/wallet/withdraw  { "amount": 500 }
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]
    amount = float(data.amount)

    if amount < 100:
        raise HTTPException(status_code=400, detail="Minimum withdraw is ₹100")

    user = await db.prepare(
        "SELECT wallet_balance, wallet_held, want_to FROM users WHERE id = ?"
    ).bind(user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    u = dict(user)
    available = float(u.get("wallet_balance") or 0)
    held = float(u.get("wallet_held") or 0)

    if available < amount:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Insufficient available balance. "
                f"Available ₹{int(available)}, held ₹{int(held)}. "
                "Held funds cannot be withdrawn until booking is completed or cancelled."
            ),
        )

    await db.prepare(
        """
        UPDATE users
        SET wallet_balance = COALESCE(wallet_balance, 0) - ?
        WHERE id = ?
        """
    ).bind(amount, user_id).run()

    tx_id = secrets.token_hex(8)
    note = (data.note or "Withdrawal request").strip() or "Withdrawal"

    await db.prepare(
        """
        INSERT INTO wallet_transactions
            (id, user_id, type, subtitle, amount, category)
        VALUES (?, ?, ?, ?, ?, ?)
        """
    ).bind(
        tx_id,
        user_id,
        "Wallet Withdraw",
        note,
        -abs(amount),
        "Spent",
    ).run()

    row = await db.prepare(
        "SELECT wallet_balance, wallet_held FROM users WHERE id = ?"
    ).bind(user_id).first()
    r = dict(row) if row else {}
    new_available = float(r.get("wallet_balance") or 0)
    new_held = float(r.get("wallet_held") or 0)

    return {
        "message": "Withdrawal successful",
        "transaction_id": tx_id,
        "amount": amount,
        "wallet_balance": new_available,
        "available_balance": new_available,
        "wallet_held": new_held,
        "held_balance": new_held,
        "status": "completed",
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