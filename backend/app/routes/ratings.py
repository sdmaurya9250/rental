from fastapi import APIRouter, Request, Depends, HTTPException, status
from routes.profile import get_current_user
from pydantic import BaseModel, Field
from typing import Optional
import secrets

router = APIRouter()


class RatingCreate(BaseModel):
    stars: int = Field(..., ge=1, le=5)
    message: Optional[str] = Field(None, max_length=1000)


async def _refresh_user_rating(db, user_id: str):
    """Update users.rating_avg and rating_count."""
    row = await db.prepare(
        """
        SELECT AVG(stars) AS avg_stars, COUNT(*) AS cnt
        FROM ratings WHERE to_user_id = ?
        """
    ).bind(user_id).first()

    if not row:
        return

    r = dict(row)
    avg = float(r.get("avg_stars") or 0)
    cnt = int(r.get("cnt") or 0)

    await db.prepare(
        """
        UPDATE users
        SET rating_avg = ?, rating_count = ?
        WHERE id = ?
        """
    ).bind(round(avg, 2), cnt, user_id).run()


@router.post("/bookings/{booking_id}/rating", status_code=status.HTTP_201_CREATED)
async def submit_booking_rating(
    booking_id: str,
    data: RatingCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Finder rates RentPeople after completed booking.
    Body: { "stars": 1-5, "message": "optional" }
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT * FROM bookings WHERE id = ?"
    ).bind(booking_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking = dict(row)

    if booking.get("status") != "completed":
        raise HTTPException(
            status_code=400,
            detail="You can only rate completed bookings",
        )

    # Only the finder (customer) rates the provider
    if booking["customer_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="Only the customer can rate this booking",
        )

    # One rating per booking
    existing = await db.prepare(
        "SELECT id FROM ratings WHERE booking_id = ?"
    ).bind(booking_id).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="You already rated this booking",
        )

    to_user_id = booking["rent_person_id"]
    message = (data.message or "").strip() or None
    rating_id = secrets.token_hex(8)

    await db.prepare(
        """
        INSERT INTO ratings (id, booking_id, from_user_id, to_user_id, stars, message)
        VALUES (?, ?, ?, ?, ?, ?)
        """
    ).bind(
        rating_id,
        booking_id,
        user_id,
        to_user_id,
        data.stars,
        message,
    ).run()

    await _refresh_user_rating(db, to_user_id)

    return {
        "id": rating_id,
        "booking_id": booking_id,
        "stars": data.stars,
        "message": message,
        "to_user_id": to_user_id,
        "message_text": "Rating submitted successfully",
    }


@router.get("/bookings/{booking_id}/rating")
async def get_booking_rating(
    booking_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Check if this booking already has a rating (for UI)."""
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

    rating = await db.prepare(
        "SELECT * FROM ratings WHERE booking_id = ?"
    ).bind(booking_id).first()

    if not rating:
        return {"rated": False, "rating": None}

    r = dict(rating)
    return {
        "rated": True,
        "rating": {
            "id": r["id"],
            "stars": r["stars"],
            "message": r.get("message") or "",
            "created_at": r.get("created_at"),
        },
    }


@router.get("/people/{user_id}/ratings")
async def list_user_ratings(
    user_id: str,
    request: Request,
    limit: int = 20,
):
    """Public list of ratings for a RentPeople profile."""
    db = request.scope["env"].DB

    rows = await db.prepare(
        """
        SELECT r.id, r.stars, r.message, r.created_at,
               u.full_name AS from_name, u.image AS from_image
        FROM ratings r
        LEFT JOIN users u ON u.id = r.from_user_id
        WHERE r.to_user_id = ?
        ORDER BY r.created_at DESC
        LIMIT ?
        """
    ).bind(user_id, limit).all()

    items = rows.results if hasattr(rows, "results") else rows
    ratings = []
    for row in items:
        r = dict(row)
        ratings.append({
            "id": r["id"],
            "stars": r["stars"],
            "message": r.get("message") or "",
            "created_at": r.get("created_at"),
            "from_name": r.get("from_name") or "User",
            "from_image": r.get("from_image") or "",
        })

    stats = await db.prepare(
        "SELECT rating_avg, rating_count FROM users WHERE id = ?"
    ).bind(user_id).first()

    s = dict(stats) if stats else {}

    return {
        "user_id": user_id,
        "rating_avg": float(s.get("rating_avg") or 0),
        "rating_count": int(s.get("rating_count") or 0),
        "ratings": ratings,
    }