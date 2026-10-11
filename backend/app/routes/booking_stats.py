from fastapi import APIRouter, Request, Depends, HTTPException, Query
from routes.profile import get_current_user
from typing import Optional

router = APIRouter()


async def _count_completed(db, user_id: str, as_role: str = "both") -> dict:
    """
    as_role:
      companion → rent_person_id (services delivered)
      finder    → customer_id (bookings made)
      both      → both counts
    """
    as_companion = 0
    as_finder = 0

    if as_role in ("companion", "both"):
        row = await db.prepare(
            """
            SELECT COUNT(*) AS cnt FROM bookings
            WHERE rent_person_id = ? AND status = 'completed'
            """
        ).bind(user_id).first()
        as_companion = int(dict(row).get("cnt") or 0) if row else 0

    if as_role in ("finder", "both"):
        row = await db.prepare(
            """
            SELECT COUNT(*) AS cnt FROM bookings
            WHERE customer_id = ? AND status = 'completed'
            """
        ).bind(user_id).first()
        as_finder = int(dict(row).get("cnt") or 0) if row else 0

    return {
        "completed_as_companion": as_companion,
        "completed_as_finder": as_finder,
        "completed_total": as_companion + as_finder,
        # aliases for app
        "completed_count": as_companion,  # main number on companion profile
        "booking_completed_count": as_companion,
    }


@router.get("/people/{user_id}/completed-count")
async def public_completed_count(
    user_id: str,
    request: Request,
):
    """
    Public — companion profile / people card.
    GET /api/people/{id}/completed-count
    """
    db = request.scope["env"].DB

    user = await db.prepare(
        "SELECT id FROM users WHERE id = ?"
    ).bind(user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stats = await _count_completed(db, user_id, as_role="both")
    return {
        "user_id": user_id,
        **stats,
    }


@router.get("/bookings/completed-count")
async def my_completed_count(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    Logged-in user dashboard.
    GET /api/bookings/completed-count
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]
    stats = await _count_completed(db, user_id, as_role="both")
    return {
        "user_id": user_id,
        **stats,
    }