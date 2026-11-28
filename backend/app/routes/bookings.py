
from fastapi import APIRouter, Request, Depends, HTTPException, status
from models.user import BookingCreate, BookingReject, VerifyOtpRequest
from routes.profile import get_current_user
from routes.notifications import create_notification
from pydantic import BaseModel, Field
from typing import Optional
import json
import re
import secrets
import random
from datetime import datetime, timedelta, timezone

from routes.safety import (
    ensure_tables,
    is_blocked_between,
    is_kyc_verified,
    is_suspended,
    place_is_blocked,
)

router = APIRouter()

PLATFORM_FEE_RATE = 0.10  # 10%

IST = timezone(timedelta(hours=5, minutes=30))
MIN_LEAD_MINUTES = 120          # same-day allowed, but at least 2h from now
MAX_DAYS_AHEAD = 60
DAY_START_MIN = 10 * 60         # 10:00
DAY_END_MIN = 22 * 60           # 22:00
MIN_DURATION_MIN = 60
MAX_DURATION_MIN = 240
RESPONSE_HOURS = 2              # companion must reply, else auto-refund
MAX_OTP_ATTEMPTS = 5


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

    await db.prepare(
        """
        UPDATE users
        SET wallet_balance = COALESCE(wallet_balance, 0) - ?,
            wallet_held = COALESCE(wallet_held, 0) + ?,
            total_spent = COALESCE(total_spent, 0) + ?
        WHERE id = ?
        """
    ).bind(amount, amount, amount, user_id).run()

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


def _slug(text: str) -> str:
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", (text or "").lower()))


def _parse_services(raw) -> list:
    if isinstance(raw, list):
        return raw
    try:
        parsed = json.loads(raw or "[]")
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _find_service(services: list, service_id, service_name):
    sid = (service_id or "").strip()
    name = (service_name or "").strip().lower()
    for sv in services:
        if isinstance(sv, dict) and sid and str(sv.get("id") or "") == sid:
            return sv
    for sv in services:
        if not isinstance(sv, dict):
            continue
        n = str(sv.get("name") or sv.get("title") or "").strip().lower()
        if name and n == name:
            return sv
        if sid and _slug(n) == sid:
            return sv
    return None


def _hm_to_min(value: str) -> int:
    h, m = str(value).strip().split(":")[:2]
    return int(h) * 60 + int(m)


def _min_to_hm(total: int) -> str:
    return f"{total // 60:02d}:{total % 60:02d}"


def _start_dt(booking_date: str, start_time: str) -> datetime:
    day = datetime.strptime(booking_date, "%Y-%m-%d").replace(tzinfo=IST)
    return day + timedelta(minutes=_hm_to_min(start_time))


def _validate_schedule(data) -> tuple[int, int]:
    """Returns (start_min, end_min). Raises 400 on any rule break."""
    try:
        start_min = _hm_to_min(data.start_time)
        start_dt = _start_dt(data.booking_date, data.start_time)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date or time")

    dur = int(data.duration_minutes)
    if dur < MIN_DURATION_MIN:
        raise HTTPException(status_code=400, detail="Minimum booking is 1 hour")
    if dur > MAX_DURATION_MIN:
        raise HTTPException(status_code=400, detail="Maximum booking is 4 hours")

    end_min = start_min + dur
    if start_min < DAY_START_MIN or end_min > DAY_END_MIN:
        raise HTTPException(
            status_code=400,
            detail="Meetups must be between 10:00 AM and 10:00 PM",
        )

    now = datetime.now(IST)
    if start_dt < now + timedelta(minutes=MIN_LEAD_MINUTES):
        raise HTTPException(
            status_code=400,
            detail=f"Please book at least {MIN_LEAD_MINUTES // 60} hours ahead",
        )
    if start_dt > now + timedelta(days=MAX_DAYS_AHEAD):
        raise HTTPException(status_code=400, detail="That date is too far ahead")
    return start_min, end_min


def _create_response(
    booking_id: str,
    *,
    status_text: str = "pending",
    payment_status: str = "held",
    booking_date=None,
    start_time=None,
    end_time=None,
    price=0,
    platform_fee=0,
    total_amount=0,
    companion_earning=0,
    rent_person_id=None,
    message: str = "Booking created. Amount held from wallet.",
) -> dict:
    return {
        "id": booking_id,
        "status": status_text,
        "booking_status": status_text,
        "payment_status": payment_status,
        "message": message,
        "booking_date": booking_date,
        "start_time": start_time,
        "end_time": end_time,
        "price": price,
        "platform_fee": platform_fee,
        "platform_fee_percent": 10,
        "total_amount": total_amount,
        "companion_earning": companion_earning,
        "rent_person_id": rent_person_id,
        "response_deadline_hours": RESPONSE_HOURS,
    }


async def _existing_booking_response(db, booking_id: str) -> dict:
    row = await db.prepare("SELECT * FROM bookings WHERE id = ?").bind(booking_id).first()
    if not row:
        raise HTTPException(status_code=409, detail="This booking is already being processed")
    b = dict(row)
    price = float(b.get("price") or 0)
    fee = float(b.get("platform_fee") or 0)
    return _create_response(
        booking_id,
        status_text=b.get("status") or "pending",
        payment_status=b.get("payment_status") or "held",
        booking_date=b.get("booking_date"),
        start_time=b.get("start_time"),
        end_time=b.get("end_time"),
        price=price,
        platform_fee=fee,
        total_amount=b.get("total_amount") or 0,
        companion_earning=max(price - fee, 0),
        rent_person_id=b.get("rent_person_id"),
        message="Booking already created.",
    )


async def expire_stale_bookings(db, user_id: str | None = None) -> int:
    """Pending requests nobody answered within RESPONSE_HOURS are cancelled and refunded."""
    sql = (
        "SELECT id, customer_id, rent_person_id, total_amount FROM bookings "
        "WHERE status = 'pending' AND created_at <= datetime('now', ?)"
    )
    params = [f"-{RESPONSE_HOURS} hours"]
    if user_id:
        sql += " AND (customer_id = ? OR rent_person_id = ?)"
        params += [user_id, user_id]
    rows = await db.prepare(sql).bind(*params).all()
    items = rows.results if hasattr(rows, "results") else rows

    done = 0
    for r in items:
        b = dict(r)
        try:
            await db.prepare(
                "UPDATE bookings SET status = 'cancelled', payment_status = 'refunded', "
                "cancellation_message = ? WHERE id = ? AND status = 'pending'"
            ).bind("Expired: companion did not respond in time", b["id"]).run()
            await refund_hold(
                db,
                user_id=b["customer_id"],
                amount=float(b.get("total_amount") or 0),
                booking_id=b["id"],
                reason="Request expired — amount refunded",
            )
            try:
                await create_notification(
                    db,
                    user_id=b["customer_id"],
                    title="Request expired",
                    body="The companion did not reply in time. Your money was refunded.",
                    type="booking",
                    data={"booking_id": b["id"]},
                )
            except Exception:
                pass
            done += 1
        except Exception:
            continue
    return done


@router.post("/bookings", status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    await ensure_tables(db)
    customer_id = current_user["id"]

    if data.rent_person_id == customer_id:
        raise HTTPException(status_code=400, detail="You cannot book yourself")

    if await is_suspended(db, customer_id):
        raise HTTPException(
            status_code=403,
            detail="Your account is under review. Please contact support.",
        )

    person = await db.prepare(
        "SELECT id, full_name, want_to, services FROM users WHERE id = ?"
    ).bind(data.rent_person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="RentPeople not found")
    person = dict(person)

    # Retry of the same request (double tap / connection drop): return the same booking.
    idem = (data.idempotency_key or "").strip()[:120] or None
    if idem:
        existing = await db.prepare(
            "SELECT booking_id FROM booking_idempotency WHERE idem_key = ? AND user_id = ?"
        ).bind(idem, customer_id).first()
        if existing:
            bid = dict(existing).get("booking_id")
            if bid:
                return await _existing_booking_response(db, bid)
            raise HTTPException(status_code=409, detail="This booking is already being processed")

    # ── who can be booked ──
    role = str(person.get("want_to") or "").strip().lower()
    if not (role in ("companion", "both") or "become" in role):
        raise HTTPException(status_code=400, detail="This user is not a companion")
    if not await is_kyc_verified(db, data.rent_person_id):
        raise HTTPException(
            status_code=400,
            detail="This companion is not ID-verified yet",
        )
    if await is_suspended(db, data.rent_person_id):
        raise HTTPException(status_code=400, detail="This companion is not available")
    if await is_blocked_between(db, customer_id, data.rent_person_id):
        raise HTTPException(status_code=403, detail="You cannot book this companion")

    # ── when ──
    start_min, end_min = _validate_schedule(data)
    start_time = _min_to_hm(start_min)
    end_time = _min_to_hm(end_min)

    clash = await db.prepare(
        "SELECT start_time, end_time FROM bookings "
        "WHERE rent_person_id = ? AND booking_date = ? "
        "AND status IN ('pending', 'approved')"
    ).bind(data.rent_person_id, data.booking_date).all()
    for r in (clash.results if hasattr(clash, "results") else clash):
        c = dict(r)
        try:
            if start_min < _hm_to_min(c["end_time"]) and _hm_to_min(c["start_time"]) < end_min:
                raise HTTPException(
                    status_code=400,
                    detail="The companion already has a booking at this time",
                )
        except HTTPException:
            raise
        except Exception:
            continue

    # ── what and how much (server decides, phone values are ignored) ──
    services = _parse_services(person.get("services"))
    svc = _find_service(services, data.service_id, data.service_name)
    if not svc:
        raise HTTPException(status_code=400, detail="This service is not offered by the companion")
    try:
        rate = int(svc.get("price") or 0)
    except (TypeError, ValueError):
        rate = 0
    if rate <= 0:
        raise HTTPException(status_code=400, detail="This companion has no price set yet")
    price, platform_fee, total_amount, companion_earning = _calc_fees(
        int(rate * int(data.duration_minutes) / 60 + 0.5)
    )
    service_name = str(svc.get("name") or svc.get("title") or data.service_name or "")
    service_id = str(svc.get("id") or data.service_id or "")

    # ── where ──
    location = (data.location or "").strip()
    if data.location_type == "in_person":
        if not location:
            raise HTTPException(status_code=400, detail="Location is required for in-person bookings")
        if place_is_blocked(location, data.place_category):
            raise HTTPException(
                status_code=400,
                detail="Please choose a public place such as a cafe, mall or park",
            )
        preferred = [
            str(x.get("name") or "").strip().lower()
            for x in (svc.get("preferred_locations") or [])
            if isinstance(x, dict)
        ]
        has_coords = (
            data.place_lat is not None
            and data.place_lng is not None
            and -90 <= data.place_lat <= 90
            and -180 <= data.place_lng <= 180
        )
        if not has_coords and location.lower() not in preferred:
            raise HTTPException(
                status_code=400,
                detail="Please choose a meeting place from the list",
            )

    booking_id = secrets.token_hex(8)
    person_name = person.get("full_name") or "Companion"

    if idem:
        try:
            await db.prepare(
                "INSERT INTO booking_idempotency (idem_key, user_id, booking_id) VALUES (?, ?, NULL)"
            ).bind(idem, customer_id).run()
        except Exception:
            raise HTTPException(status_code=409, detail="This booking is already being processed")

    held = False
    try:
        await hold_for_booking(
            db,
            user_id=customer_id,
            amount=float(total_amount),
            booking_id=booking_id,
            person_name=person_name,
        )
        held = True

        await db.prepare(
            """
            INSERT INTO bookings (
                id, customer_id, rent_person_id, service_id, service_name,
                booking_date, start_time, end_time, timezone, duration_minutes,
                location_type, location, special_requirements, customer_note,
                price, platform_fee, total_amount, status, payment_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        ).bind(
            booking_id,
            customer_id,
            data.rent_person_id,
            service_id,
            service_name,
            data.booking_date,
            start_time,
            end_time,
            "Asia/Kolkata",
            int(data.duration_minutes),
            data.location_type,
            location,
            data.special_requirements,
            data.customer_note,
            price,
            platform_fee,
            total_amount,
            "pending",
            "held",
        ).run()

        if idem:
            await db.prepare(
                "UPDATE booking_idempotency SET booking_id = ? WHERE idem_key = ? AND user_id = ?"
            ).bind(booking_id, idem, customer_id).run()
    except Exception:
        # Undo: release the reservation (so a retry after top-up works) and any hold.
        if held:
            try:
                await refund_hold(
                    db,
                    user_id=customer_id,
                    amount=float(total_amount),
                    booking_id=booking_id,
                    reason="Booking failed — amount refunded",
                )
            except Exception:
                pass
        if idem:
            try:
                await db.prepare(
                    "DELETE FROM booking_idempotency WHERE idem_key = ? AND user_id = ? AND booking_id IS NULL"
                ).bind(idem, customer_id).run()
            except Exception:
                pass
        raise

    customer_name = current_user.get("full_name") or "Someone"
    try:
        await create_notification(
            db,
            user_id=data.rent_person_id,
            title="New booking request",
            body=f"{customer_name} requested a booking for {data.booking_date}. Reply within {RESPONSE_HOURS} hours.",
            type="booking",
            data={"booking_id": booking_id},
        )
    except Exception:
        pass

    return _create_response(
        booking_id,
        booking_date=data.booking_date,
        start_time=start_time,
        end_time=end_time,
        price=price,
        platform_fee=platform_fee,
        total_amount=total_amount,
        companion_earning=companion_earning,
        rent_person_id=data.rent_person_id,
    )


@router.get("/bookings")
async def my_bookings(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]
    await ensure_tables(db)
    try:
        await expire_stale_bookings(db, user_id)
    except Exception:
        pass

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

    bookings = []
    for row in to_list(outgoing):
        bookings.append(_format_booking(row, user_id))
    for row in to_list(incoming):
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
    await ensure_tables(db)
    try:
        await expire_stale_bookings(db, user_id)
    except Exception:
        pass

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
    await ensure_tables(db)
    try:
        await expire_stale_bookings(db, user_id)
    except Exception:
        pass

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

    if booking.get("status") != "pending":
        if "expired" in str(booking.get("cancellation_message") or "").lower():
            raise HTTPException(status_code=400, detail="This request has expired")
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve booking with status: {booking.get('status')}",
        )

    if not await is_kyc_verified(db, user_id):
        raise HTTPException(
            status_code=403,
            detail="Complete your ID verification before accepting bookings",
        )
    if await is_suspended(db, user_id):
        raise HTTPException(
            status_code=403,
            detail="Your account is under review. Please contact support.",
        )

    # Too late to accept once the meetup time has passed: cancel and refund.
    try:
        started = _start_dt(booking["booking_date"], booking["start_time"]) <= datetime.now(IST)
    except Exception:
        started = False
    if started:
        await db.prepare(
            "UPDATE bookings SET status = 'cancelled', payment_status = 'refunded', "
            "cancellation_message = ? WHERE id = ? AND status = 'pending'"
        ).bind("Expired: meetup time passed", booking_id).run()
        await refund_hold(
            db,
            user_id=booking["customer_id"],
            amount=float(booking.get("total_amount") or 0),
            booking_id=booking_id,
            reason="Meetup time passed — amount refunded",
        )
        raise HTTPException(status_code=400, detail="The meetup time has already passed")

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

    await ensure_tables(db)
    att_row = await db.prepare(
        "SELECT attempts FROM otp_attempts WHERE booking_id = ?"
    ).bind(booking_id).first()
    attempts = int(dict(att_row).get("attempts") or 0) if att_row else 0
    if attempts >= MAX_OTP_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Too many wrong codes. Please contact support to complete this booking.",
        )

    if not booking.get("otp") or not secrets.compare_digest(
        str(data.otp).strip(), str(booking["otp"])
    ):
        await db.prepare(
            "INSERT INTO otp_attempts (booking_id, attempts) VALUES (?, 1) "
            "ON CONFLICT(booking_id) DO UPDATE SET attempts = attempts + 1"
        ).bind(booking_id).run()
        left = max(MAX_OTP_ATTEMPTS - (attempts + 1), 0)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid OTP. {left} tries left." if left else "Invalid OTP. No tries left.",
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