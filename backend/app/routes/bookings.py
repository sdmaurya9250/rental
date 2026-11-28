
from fastapi import APIRouter, Request, Depends, HTTPException, status
from models.user import BookingCreate, BookingReject, VerifyOtpRequest
from routes.profile import get_current_user
from routes.notifications import create_notification
from pydantic import BaseModel, Field
from typing import Optional
import secrets
import random
import json
from datetime import datetime

from utils.booking_rules import find_service, validate_venue

router = APIRouter()

PLATFORM_FEE_RATE = 0.10  # 10%
PENDING_EXPIRY_HOURS = 24     # unanswered request -> expired + refunded
MAX_OTP_ATTEMPTS = 5          # wrong OTP tries per booking
REQUIRE_COMPANION_KYC = True  # companion must have verified ID

class VerifyOtpRequest(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6)

def _generate_otp() -> str:
    return f"{random.randint(100000, 999999)}"

def _calc_fees(price: int | float) -> tuple[int, int, int]:
    """
    price            = service amount
    platform_fee     = 10% of price
    total_amount     = price + fee  (finder pays / held)
    companion_earning = price - fee  (companion receives on complete)
    """
    price = int(price or 0)
    if price < 0:
        price = 0
    platform_fee = int(round(price * PLATFORM_FEE_RATE))
    total_amount = price + platform_fee
    companion_earning = max(price - platform_fee, 0)
    return price, platform_fee, total_amount, companion_earning

async def _get_balances(db, user_id: str) -> tuple[float, float]:
    row = await db.prepare(
        "SELECT wallet_balance, wallet_held FROM users WHERE id = ?"
    ).bind(user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    u = dict(row)
    return float(u.get("wallet_balance") or 0), float(u.get("wallet_held") or 0)

async def hold_for_booking(
    db,
    user_id: str,
    amount: float,
    booking_id: str,
    person_name: str = "",
):
    """available → held. Fails with structured error if insufficient."""
    amount = float(amount or 0)
    if amount <= 0:
        return None

    existing = await db.prepare(
        """
        SELECT id FROM wallet_transactions
        WHERE booking_id = ? AND user_id = ? AND category = 'Held'
        LIMIT 1
        """
    ).bind(booking_id, user_id).first()
    if existing:
        return dict(existing).get("id")

    available, _held = await _get_balances(db, user_id)
    if available < amount:
        need = round(amount - available, 2)
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INSUFFICIENT_BALANCE",
                "message": "Insufficient wallet balance",
                "booking_amount": amount,
                "available_balance": available,
                "amount_needed": need,
            },
        )

    # Conditional update: two parallel requests cannot spend the same money.
    moved = await db.prepare(
        """
        UPDATE users
        SET wallet_balance = COALESCE(wallet_balance, 0) - ?,
            wallet_held = COALESCE(wallet_held, 0) + ?,
            total_spent = COALESCE(total_spent, 0) + ?
        WHERE id = ? AND COALESCE(wallet_balance, 0) >= ?
        RETURNING id
        """
    ).bind(amount, amount, amount, user_id, amount).first()
    if not moved:
        available, _held = await _get_balances(db, user_id)
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INSUFFICIENT_BALANCE",
                "message": "Insufficient wallet balance",
                "booking_amount": amount,
                "available_balance": available,
                "amount_needed": round(max(amount - available, 0), 2),
            },
        )

    tx_id = secrets.token_hex(8)
    await db.prepare(
        """
        INSERT INTO wallet_transactions
            (id, user_id, type, subtitle, amount, category, booking_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
    ).bind(
        tx_id,
        user_id,
        "Booking Hold",
        f"Held for booking with {person_name}" if person_name else "Booking amount held",
        -abs(amount),
        "Held",
        booking_id,
    ).run()
    return tx_id

async def release_to_companion(
    db,
    finder_id: str,
    companion_id: str,
    amount: float,
    platform_fee: float,
    booking_id: str,
):
    """
    Clear full hold (amount) from finder.
    Credit companion: amount - platform_fee.
    Idempotent.
    """
    amount = float(amount or 0)
    platform_fee = float(platform_fee or 0)
    earning = max(amount - platform_fee, 0)
    if amount <= 0:
        return None

    existing = await db.prepare(
        """
        SELECT id FROM wallet_transactions
        WHERE booking_id = ? AND category = 'Released'
        LIMIT 1
        """
    ).bind(booking_id).first()
    if existing:
        return None

    _, held = await _get_balances(db, finder_id)
    release_amt = min(amount, held)

    await db.prepare(
        """
        UPDATE users
        SET wallet_held = MAX(COALESCE(wallet_held, 0) - ?, 0)
        WHERE id = ?
        """
    ).bind(release_amt, finder_id).run()

    if earning > 0:
        await db.prepare(
            """
            UPDATE users
            SET wallet_balance = COALESCE(wallet_balance, 0) + ?
            WHERE id = ?
            """
        ).bind(earning, companion_id).run()

        tx_id = secrets.token_hex(8)
        await db.prepare(
            """
            INSERT INTO wallet_transactions
                (id, user_id, type, subtitle, amount, category, booking_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
        ).bind(
            tx_id,
            companion_id,
            "Booking Earning",
            "Payment released to companion",
            abs(earning),
            "Released",
            booking_id,
        ).run()
    return True

async def refund_hold(
    db,
    user_id: str,
    amount: float,
    booking_id: str,
    reason: str = "Booking rejected — amount refunded",
):
    """held → available. Idempotent."""
    amount = float(amount or 0)
    if amount <= 0:
        return None

    existing = await db.prepare(
        """
        SELECT id FROM wallet_transactions
        WHERE booking_id = ? AND user_id = ? AND category = 'Refunded'
        LIMIT 1
        """
    ).bind(booking_id, user_id).first()
    if existing:
        return None

    _, held = await _get_balances(db, user_id)
    refund_amt = min(amount, held)

    await db.prepare(
        """
        UPDATE users
        SET wallet_held = MAX(COALESCE(wallet_held, 0) - ?, 0),
            wallet_balance = COALESCE(wallet_balance, 0) + ?,
            total_spent = MAX(COALESCE(total_spent, 0) - ?, 0)
        WHERE id = ?
        """
    ).bind(refund_amt, refund_amt, refund_amt, user_id).run()

    tx_id = secrets.token_hex(8)
    await db.prepare(
        """
        INSERT INTO wallet_transactions
            (id, user_id, type, subtitle, amount, category, booking_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
    ).bind(
        tx_id,
        user_id,
        "Booking Refund",
        reason,
        abs(refund_amt),
        "Refunded",
        booking_id,
    ).run()
    return tx_id

async def _companion_kyc_verified(db, user_id: str) -> bool:
    try:
        row = await db.prepare(
            "SELECT status FROM kyc WHERE user_id = ? ORDER BY rowid DESC LIMIT 1"
        ).bind(user_id).first()
    except Exception:
        return False
    return bool(row) and str(dict(row).get("status") or "").lower() == "verified"


def _age_hours(created_at) -> float:
    try:
        t = datetime.strptime(str(created_at)[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return 0.0
    return (datetime.utcnow() - t).total_seconds() / 3600.0


async def _expire_if_stale(db, booking: dict) -> bool:
    """Pending too long -> expired + refund. True if it expired now."""
    if booking.get("status") != "pending":
        return False
    if _age_hours(booking.get("created_at")) < PENDING_EXPIRY_HOURS:
        return False
    done = await db.prepare(
        "UPDATE bookings SET status = ?, payment_status = ? WHERE id = ? AND status = ? RETURNING id"
    ).bind("expired", "refunded", booking["id"], "pending").first()
    if not done:
        return False
    await refund_hold(
        db,
        user_id=booking["customer_id"],
        amount=float(booking.get("total_amount") or 0),
        booking_id=booking["id"],
        reason="Booking expired - amount refunded",
    )
    try:
        await create_notification(
            db,
            user_id=booking["customer_id"],
            title="Booking expired",
            body="The companion did not respond in time. Your money was refunded.",
            type="booking",
            data={"booking_id": booking["id"]},
        )
    except Exception:
        pass
    booking["status"] = "expired"
    booking["payment_status"] = "refunded"
    return True


def _format_booking(row: dict, current_user_id: str) -> dict:
    is_incoming = row.get("rent_person_id") == current_user_id
    direction = "incoming" if is_incoming else "outgoing"

    if is_incoming:
        person_name = row.get("customer_name") or "Customer"
        person_image = row.get("customer_image") or ""
    else:
        person_name = row.get("rent_person_name") or "RentPeople"
        person_image = row.get("rent_person_image") or ""

    status_val = row.get("status") or "pending"
    otp = row.get("otp") or ""
    otp_verified = bool(row.get("otp_verified", 0)) or status_val == "completed"
    show_otp = status_val == "approved" and bool(otp) and not otp_verified

    price = float(row.get("price") or 0)
    platform_fee = float(row.get("platform_fee") or 0)
    total_amount = float(row.get("total_amount") or 0)
    companion_earning = max(price - platform_fee, 0)

    return {
        "id": row["id"],
        "direction": direction,
        "booking_status": status_val,
        "payment_status": row.get("payment_status") or "none",
        "booking_date": row.get("booking_date"),
        "start_time": row.get("start_time"),
        "end_time": row.get("end_time"),
        "duration_minutes": row.get("duration_minutes") or 0,
        "location_type": row.get("location_type"),
        "location": row.get("location") or "",
        "timezone": row.get("timezone") or "Asia/Kolkata",
        "service_id": row.get("service_id"),
        "service_name": row.get("service_name") or "Service",
        "price": price,
        "platform_fee": platform_fee,
        "platform_fee_percent": 10,
        "total_amount": total_amount,
        "companion_earning": companion_earning,
        "special_requirements": row.get("special_requirements") or "",
        "customer_note": row.get("customer_note") or "",
        "rejection_message": row.get("rejection_message") or "",
        "cancellation_message": row.get("cancellation_message") or "",
        "person_name": person_name,
        "person_image": person_image,
        "customer_id": row.get("customer_id"),
        "rent_person_id": row.get("rent_person_id"),
        "created_at": row.get("created_at"),
        "otp": otp if show_otp else None,
        "otp_verified": otp_verified,
        "show_otp": (not is_incoming) and show_otp,
        "needs_otp_entry": is_incoming and show_otp,
    }

def _create_response(b: dict, replay: bool = False) -> dict:
    price = float(b.get("price") or 0)
    fee = float(b.get("platform_fee") or 0)
    return {
        "id": b["id"],
        "status": b.get("status") or "pending",
        "booking_status": b.get("status") or "pending",
        "payment_status": b.get("payment_status") or "held",
        "message": "Booking already created." if replay else "Booking created. Amount held from wallet.",
        "booking_date": b.get("booking_date"),
        "start_time": b.get("start_time"),
        "end_time": b.get("end_time"),
        "price": price,
        "platform_fee": fee,
        "platform_fee_percent": 10,
        "total_amount": b.get("total_amount") or 0,
        "companion_earning": max(price - fee, 0),
        "rent_person_id": b.get("rent_person_id"),
    }


@router.post("/bookings", status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    customer_id = current_user["id"]

    if data.rent_person_id == customer_id:
        raise HTTPException(status_code=400, detail="You cannot book yourself")

    # Same key again = same booking. Protects against double taps and retries.
    key = (data.idempotency_key or "").strip() or None
    if key:
        prev = await db.prepare(
            "SELECT * FROM bookings WHERE customer_id = ? AND idempotency_key = ?"
        ).bind(customer_id, key).first()
        if prev:
            return _create_response(dict(prev), replay=True)

    person = await db.prepare(
        "SELECT id, full_name, services FROM users WHERE id = ?"
    ).bind(data.rent_person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="RentPeople not found")

    person = dict(person)

    if data.duration_minutes < 60 or data.duration_minutes > 240:
        raise HTTPException(status_code=400, detail="Duration must be 1 to 4 hours")

    if data.location_type == "in_person" and not (data.location or "").strip():
        raise HTTPException(
            status_code=400,
            detail="Location is required for in-person bookings",
        )

    if REQUIRE_COMPANION_KYC and not await _companion_kyc_verified(db, data.rent_person_id):
        raise HTTPException(
            status_code=400,
            detail="This companion has not completed ID verification yet.",
        )

    # Price comes from the companion's saved service, never from the client.
    try:
        services = json.loads(person.get("services") or "[]")
    except Exception:
        services = []
    service = find_service(services if isinstance(services, list) else [], data.service_id, data.service_name)
    if not service:
        raise HTTPException(status_code=400, detail="This service is not offered by the companion")
    try:
        rate = float(service.get("price") or 0)
    except (TypeError, ValueError):
        rate = 0
    if rate <= 0:
        raise HTTPException(status_code=400, detail="This companion has not set a price for this service")

    validate_venue(data, service)

    price, platform_fee, total_amount, companion_earning = _calc_fees(
        round(rate * data.duration_minutes / 60.0)
    )

    booking_id = secrets.token_hex(8)
    person_name = person.get("full_name") or "Companion"

    await hold_for_booking(
        db,
        user_id=customer_id,
        amount=float(total_amount),
        booking_id=booking_id,
        person_name=person_name,
    )

    try:
        await db.prepare(
            """
            INSERT INTO bookings (
                id, customer_id, rent_person_id, service_id, service_name,
                booking_date, start_time, end_time, timezone, duration_minutes,
                location_type, location, special_requirements, customer_note,
                price, platform_fee, total_amount, status, payment_status,
                location_lat, location_lng, location_category, idempotency_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        ).bind(
            booking_id,
            customer_id,
            data.rent_person_id,
            service.get("id") or data.service_id,
            service.get("name") or data.service_name,
            data.booking_date,
            data.start_time,
            data.end_time,
            data.timezone or "Asia/Kolkata",
            data.duration_minutes,
            data.location_type,
            data.location,
            data.special_requirements,
            data.customer_note,
            price,
            platform_fee,
            total_amount,
            "pending",
            "held",
            data.location_lat,
            data.location_lng,
            data.location_category,
            key,
        ).run()
    except Exception:
        # Insert failed (e.g. same key raced in). Give the money back.
        await refund_hold(db, user_id=customer_id, amount=float(total_amount),
                          booking_id=booking_id, reason="Booking failed - amount refunded")
        if key:
            prev = await db.prepare(
                "SELECT * FROM bookings WHERE customer_id = ? AND idempotency_key = ?"
            ).bind(customer_id, key).first()
            if prev:
                return _create_response(dict(prev), replay=True)
        raise HTTPException(status_code=500, detail="Could not create booking")

    customer_name = current_user.get("full_name") or "Someone"
    try:
        await create_notification(
            db,
            user_id=data.rent_person_id,
            title="New booking request",
            body=f"{customer_name} requested a booking for {data.booking_date}.",
            type="booking",
            data={"booking_id": booking_id},
        )
    except Exception:
        pass

    row = {
        "id": booking_id, "booking_date": data.booking_date,
        "start_time": data.start_time, "end_time": data.end_time,
        "price": price, "platform_fee": platform_fee, "total_amount": total_amount,
        "rent_person_id": data.rent_person_id,
        "status": "pending", "payment_status": "held",
    }
    return _create_response(row)


@router.get("/bookings")
async def my_bookings(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    outgoing = await db.prepare(
        """
        SELECT b.*,
               u.full_name AS rent_person_name,
               u.image AS rent_person_image
        FROM bookings b
        LEFT JOIN users u ON u.id = b.rent_person_id
        WHERE b.customer_id = ?
        ORDER BY b.created_at DESC
        """
    ).bind(user_id).all()

    incoming = await db.prepare(
        """
        SELECT b.*,
               u.full_name AS customer_name,
               u.image AS customer_image
        FROM bookings b
        LEFT JOIN users u ON u.id = b.customer_id
        WHERE b.rent_person_id = ?
        ORDER BY b.created_at DESC
        """
    ).bind(user_id).all()

    def to_list(rows):
        items = rows.results if hasattr(rows, "results") else rows
        return [dict(r) for r in items]

    out_rows, in_rows = to_list(outgoing), to_list(incoming)
    for row in out_rows + in_rows:
        try:
            await _expire_if_stale(db, row)
        except Exception:
            pass

    bookings = []
    for row in out_rows:
        bookings.append(_format_booking(row, user_id))
    for row in in_rows:
        bookings.append(_format_booking(row, user_id))

    bookings.sort(
        key=lambda b: b.get("created_at") or b.get("booking_date") or "",
        reverse=True,
    )

    return {"bookings": bookings, "count": len(bookings)}

@router.get("/bookings/{booking_id}")
async def get_booking(
    booking_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        """
        SELECT b.*,
               c.full_name AS customer_name, c.image AS customer_image,
               r.full_name AS rent_person_name, r.image AS rent_person_image
        FROM bookings b
        LEFT JOIN users c ON c.id = b.customer_id
        LEFT JOIN users r ON r.id = b.rent_person_id
        WHERE b.id = ?
        """
    ).bind(booking_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)
    if booking["customer_id"] != user_id and booking["rent_person_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    return _format_booking(booking, user_id)

@router.post("/bookings/{booking_id}/approve")
async def approve_booking(
    booking_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Approve only — amount already held. No debit."""
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT * FROM bookings WHERE id = ?"
    ).bind(booking_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)

    if booking["rent_person_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only the companion can approve this booking",
        )

    if await _expire_if_stale(db, booking):
        raise HTTPException(status_code=400, detail="This request expired and was refunded")

    if booking.get("status") != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve booking with status: {booking.get('status')}",
        )

    if REQUIRE_COMPANION_KYC and not await _companion_kyc_verified(db, user_id):
        raise HTTPException(status_code=403, detail="Complete ID verification to accept bookings")

    otp = _generate_otp()
    await db.prepare(
        """
        UPDATE bookings
        SET status = ?, otp = ?, otp_verified = 0, responded_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
    ).bind("approved", otp, booking_id).run()

    try:
        await create_notification(
            db,
            user_id=booking["customer_id"],
            title="Booking approved",
            body="Your booking was approved. Open My Bookings to see the OTP.",
            type="booking",
            data={"booking_id": booking_id},
        )
    except Exception:
        pass

    price = float(booking.get("price") or 0)
    platform_fee = float(booking.get("platform_fee") or 0)

    return {
        "id": booking_id,
        "booking_status": "approved",
        "payment_status": booking.get("payment_status") or "held",
        "otp": otp,
        "otp_verified": False,
        "price": price,
        "platform_fee": platform_fee,
        "platform_fee_percent": 10,
        "total_amount": booking.get("total_amount") or 0,
        "companion_earning": max(price - platform_fee, 0),
        "message": "Booking approved. Payment remains held. OTP generated.",
    }

@router.post("/bookings/{booking_id}/verify-otp")
async def verify_booking_otp(
    booking_id: str,
    data: VerifyOtpRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Complete → clear full hold from finder.
    Credit companion: price − 10% fee (90% of service price).
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT * FROM bookings WHERE id = ?"
    ).bind(booking_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)

    if booking["rent_person_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only the companion can verify the OTP",
        )

    if booking.get("status") == "completed":
        return {
            "id": booking_id,
            "booking_status": "completed",
            "payment_status": booking.get("payment_status") or "released",
            "otp_verified": True,
            "message": "Booking already completed",
        }

    if booking.get("status") != "approved":
        raise HTTPException(
            status_code=400,
            detail="Booking must be approved before OTP verification",
        )

    attempts = int(booking.get("otp_attempts") or 0)
    if attempts >= MAX_OTP_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Too many wrong OTP attempts. Please contact support or cancel the booking.",
        )

    if not booking.get("otp") or str(data.otp).strip() != str(booking["otp"]):
        await db.prepare(
            "UPDATE bookings SET otp_attempts = COALESCE(otp_attempts, 0) + 1 WHERE id = ?"
        ).bind(booking_id).run()
        left = MAX_OTP_ATTEMPTS - attempts - 1
        raise HTTPException(
            status_code=400,
            detail=f"Invalid OTP. {left} tries left." if left > 0 else "Invalid OTP. No tries left.",
        )

    price = float(booking.get("price") or 0)
    platform_fee = float(booking.get("platform_fee") or 0)
    total = float(booking.get("total_amount") or 0)
    provider_earning = max(price - platform_fee, 0)

    platform_cut = total - provider_earning

    await db.prepare(
        """
        UPDATE bookings
        SET otp_verified = 1, status = ?, payment_status = ?
        WHERE id = ?
        """
    ).bind("completed", "released", booking_id).run()

    await release_to_companion(
        db,
        finder_id=booking["customer_id"],
        companion_id=booking["rent_person_id"],
        amount=total,
        platform_fee=platform_cut,
        booking_id=booking_id,
    )

    try:
        await create_notification(
            db,
            user_id=booking["customer_id"],
            title="Booking completed",
            body="Meetup verified. You can rate your experience.",
            type="booking",
            data={"booking_id": booking_id},
        )
        await create_notification(
            db,
            user_id=booking["rent_person_id"],
            title="Earning received",
            body=f"₹{int(provider_earning)} credited to your wallet.",
            type="wallet",
            data={"booking_id": booking_id},
        )
    except Exception:
        pass

    return {
        "id": booking_id,
        "booking_status": "completed",
        "payment_status": "released",
        "otp_verified": True,
        "price": price,
        "platform_fee": platform_fee,
        "platform_fee_percent": 10,
        "total_amount": total,
        "provider_earning": provider_earning,
        "companion_earning": provider_earning,
        "message": "OTP verified. Booking completed. Payment released to companion.",
    }

@router.post("/bookings/{booking_id}/reject")
async def reject_booking(
    booking_id: str,
    data: BookingReject,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT * FROM bookings WHERE id = ?"
    ).bind(booking_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)

    if booking["rent_person_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only the companion can reject this booking",
        )

    if booking.get("status") != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject booking with status: {booking.get('status')}",
        )

    msg = (data.rejection_message or "").strip()

    await db.prepare(
        """
        UPDATE bookings
        SET status = ?, rejection_message = ?, payment_status = ?,
            responded_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
    ).bind("rejected", msg, "refunded", booking_id).run()

    if (booking.get("payment_status") or "") == "held":
        await refund_hold(
            db,
            user_id=booking["customer_id"],
            amount=float(booking.get("total_amount") or 0),
            booking_id=booking_id,
            reason="Booking rejected — amount refunded",
        )

    try:
        await create_notification(
            db,
            user_id=booking["customer_id"],
            title="Booking rejected",
            body=msg or "Your booking was rejected. Amount refunded to wallet.",
            type="booking",
            data={"booking_id": booking_id},
        )
    except Exception:
        pass

    return {
        "id": booking_id,
        "booking_status": "rejected",
        "payment_status": "refunded",
        "rejection_message": msg,
        "message": "Booking rejected. Held amount refunded to customer.",
    }

@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT * FROM bookings WHERE id = ?"
    ).bind(booking_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)

    if booking["customer_id"] != user_id and booking["rent_person_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if booking.get("status") in ("completed", "cancelled", "rejected"):
        raise HTTPException(status_code=400, detail="Cannot cancel this booking")

    prev_status = booking.get("status")
    pay = booking.get("payment_status") or ""

    await db.prepare(
        """
        UPDATE bookings
        SET status = ?, cancellation_message = ?, payment_status = ?
        WHERE id = ?
        """
    ).bind(
        "cancelled",
        "Cancelled by user",
        "refunded" if pay == "held" else pay,
        booking_id,
    ).run()

    refunded = False
    if prev_status in ("pending", "approved") and pay == "held":
        await refund_hold(
            db,
            user_id=booking["customer_id"],
            amount=float(booking.get("total_amount") or 0),
            booking_id=booking_id,
            reason="Booking cancelled — amount refunded",
        )
        refunded = True

    other_id = (
        booking["rent_person_id"]
        if user_id == booking["customer_id"]
        else booking["customer_id"]
    )
    try:
        await create_notification(
            db,
            user_id=other_id,
            title="Booking cancelled",
            body="A booking was cancelled.",
            type="booking",
            data={"booking_id": booking_id},
        )
    except Exception:
        pass

    return {
        "id": booking_id,
        "booking_status": "cancelled",
        "payment_status": "refunded" if refunded else pay,
        "message": "Booking cancelled",
        "refunded": refunded,
    }