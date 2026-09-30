from fastapi import APIRouter, Request, Depends, HTTPException, status
from models.user import BookingCreate, BookingReject
from routes.profile import get_current_user
import secrets

router = APIRouter()


def _format_booking(row: dict, current_user_id: str) -> dict:
    is_incoming = row.get("rent_person_id") == current_user_id
    direction = "incoming" if is_incoming else "outgoing"

    if is_incoming:
        person_name = row.get("customer_name") or "Customer"
        person_image = row.get("customer_image") or ""
    else:
        person_name = row.get("rent_person_name") or "RentPeople"
        person_image = row.get("rent_person_image") or ""

    return {
        "id": row["id"],
        "direction": direction,
        "booking_status": row.get("status") or "pending",
        "booking_date": row.get("booking_date"),
        "start_time": row.get("start_time"),
        "end_time": row.get("end_time"),
        "duration_minutes": row.get("duration_minutes") or 0,
        "location_type": row.get("location_type"),
        "location": row.get("location") or "",
        "timezone": row.get("timezone") or "Asia/Kolkata",
        "service_id": row.get("service_id"),
        "service_name": row.get("service_name") or "Service",
        "total_amount": row.get("total_amount") or 0,
        "price": row.get("price") or 0,
        "platform_fee": row.get("platform_fee") or 0,
        "special_requirements": row.get("special_requirements") or "",
        "customer_note": row.get("customer_note") or "",
        "rejection_message": row.get("rejection_message") or "",
        "cancellation_message": row.get("cancellation_message") or "",
        "person_name": person_name,
        "person_image": person_image,
        "customer_id": row.get("customer_id"),
        "rent_person_id": row.get("rent_person_id"),
        "created_at": row.get("created_at"),
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

    person = await db.prepare(
        "SELECT id, full_name FROM users WHERE id = ?"
    ).bind(data.rent_person_id).first()

    if not person:
        raise HTTPException(status_code=404, detail="RentPeople not found")

    if data.duration_minutes <= 0:
        raise HTTPException(status_code=400, detail="Invalid duration")

    if data.location_type == "in_person" and not (data.location or "").strip():
        raise HTTPException(status_code=400, detail="Location is required for in-person bookings")

    booking_id = secrets.token_hex(8)

    await db.prepare(
        """
        INSERT INTO bookings (
            id, customer_id, rent_person_id, service_id, service_name,
            booking_date, start_time, end_time, timezone, duration_minutes,
            location_type, location, special_requirements, customer_note,
            price, platform_fee, total_amount, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    ).bind(
        booking_id,
        customer_id,
        data.rent_person_id,
        data.service_id,
        data.service_name,
        data.booking_date,
        data.start_time,
        data.end_time,
        data.timezone or "Asia/Kolkata",
        data.duration_minutes,
        data.location_type,
        data.location,
        data.special_requirements,
        data.customer_note,
        data.price,
        data.platform_fee,
        data.total_amount,
        "pending",
    ).run()

    return {
        "id": booking_id,
        "status": "pending",
        "booking_status": "pending",
        "message": "Booking request created successfully",
        "booking_date": data.booking_date,
        "start_time": data.start_time,
        "end_time": data.end_time,
        "total_amount": data.total_amount,
        "rent_person_id": data.rent_person_id,
    }


@router.get("/bookings")
async def my_bookings(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Returns a flat list for BookingsList.jsx
    Frontend accepts: data (array) OR data.bookings
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]

    # Outgoing = I am customer
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

    # Incoming = I am rent person
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

    # Sort by date desc
    bookings.sort(key=lambda b: b.get("created_at") or b.get("booking_date") or "", reverse=True)

    return {
        "bookings": bookings,
        "count": len(bookings),
    }


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
    """Only the RentPeople (provider) can approve incoming pending bookings."""
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare("SELECT * FROM bookings WHERE id = ?").bind(booking_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)
    if booking["rent_person_id"] != user_id:
        raise HTTPException(status_code=403, detail="Only the RentPeople can approve this booking")

    if booking.get("status") != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot approve booking with status: {booking.get('status')}")

    await db.prepare(
        "UPDATE bookings SET status = ? WHERE id = ?"
    ).bind("approved", booking_id).run()

    return {"id": booking_id, "booking_status": "approved", "message": "Booking approved"}


@router.post("/bookings/{booking_id}/reject")
async def reject_booking(
    booking_id: str,
    data: BookingReject,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Only the RentPeople (provider) can reject incoming pending bookings."""
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare("SELECT * FROM bookings WHERE id = ?").bind(booking_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)
    if booking["rent_person_id"] != user_id:
        raise HTTPException(status_code=403, detail="Only the RentPeople can reject this booking")

    if booking.get("status") != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot reject booking with status: {booking.get('status')}")

    msg = (data.rejection_message or "").strip()

    await db.prepare(
        "UPDATE bookings SET status = ?, rejection_message = ? WHERE id = ?"
    ).bind("rejected", msg, booking_id).run()

    return {
        "id": booking_id,
        "booking_status": "rejected",
        "rejection_message": msg,
        "message": "Booking rejected",
    }


@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Customer or provider can cancel (if still pending/approved)."""
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare("SELECT * FROM bookings WHERE id = ?").bind(booking_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)
    if booking["customer_id"] != user_id and booking["rent_person_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if booking.get("status") in ("completed", "cancelled", "rejected"):
        raise HTTPException(status_code=400, detail="Cannot cancel this booking")

    await db.prepare(
        "UPDATE bookings SET status = ?, cancellation_message = ? WHERE id = ?"
    ).bind("cancelled", "Cancelled by user", booking_id).run()

    return {"id": booking_id, "booking_status": "cancelled", "message": "Booking cancelled"}