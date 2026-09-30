from fastapi import APIRouter, Request, Depends, HTTPException, status
from models.user import BookingCreate
from routes.profile import get_current_user
import secrets

router = APIRouter()


@router.post("/bookings", status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    customer_id = current_user["id"]

    # Cannot book yourself
    if data.rent_person_id == customer_id:
        raise HTTPException(status_code=400, detail="You cannot book yourself")

    # Check rent person exists
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
            id, customer_id, rent_person_id, service_id,
            booking_date, start_time, end_time, timezone, duration_minutes,
            location_type, location, special_requirements, customer_note,
            price, platform_fee, total_amount, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    ).bind(
        booking_id,
        customer_id,
        data.rent_person_id,
        data.service_id,
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
    db = request.scope["env"].DB
    user_id = current_user["id"]

    # Bookings I made (as customer)
    as_customer = await db.prepare(
        """
        SELECT b.*, u.full_name as rent_person_name, u.image as rent_person_image, u.city as rent_person_city
        FROM bookings b
        LEFT JOIN users u ON u.id = b.rent_person_id
        WHERE b.customer_id = ?
        ORDER BY b.created_at DESC
        """
    ).bind(user_id).all()

    # Bookings I received (as RentPeople)
    as_provider = await db.prepare(
        """
        SELECT b.*, u.full_name as customer_name, u.image as customer_image, u.city as customer_city
        FROM bookings b
        LEFT JOIN users u ON u.id = b.customer_id
        WHERE b.rent_person_id = ?
        ORDER BY b.created_at DESC
        """
    ).bind(user_id).all()

    def rows_to_list(rows):
        items = rows.results if hasattr(rows, "results") else rows
        return [dict(r) for r in items]

    return {
        "as_customer": rows_to_list(as_customer),
        "as_provider": rows_to_list(as_provider),
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
        "SELECT * FROM bookings WHERE id = ?"
    ).bind(booking_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)

    if booking["customer_id"] != user_id and booking["rent_person_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    return booking