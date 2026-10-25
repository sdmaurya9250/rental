# from fastapi import APIRouter, Request, Depends, HTTPException, Query
# from routes.profile import get_current_user
# from datetime import datetime, timedelta
# from typing import Optional
#
# router = APIRouter()
#
#
# def _parse_dt(value: str | None) -> datetime | None:
#     if not value:
#         return None
#     try:
#         return datetime.fromisoformat(str(value).replace("Z", ""))
#     except Exception:
#         return None
#
#
# def _compute_stats(rows: list, window_days: int = 30) -> dict:
#     """
#     responded = status in approved, rejected, completed, cancelled (after action)
#     pending still open = not responded
#     """
#     now = datetime.utcnow()
#     cutoff = now - timedelta(days=window_days)
#
#     total = 0
#     responded = 0
#     response_minutes = []
#
#     for row in rows:
#         r = dict(row)
#         created = _parse_dt(r.get("created_at"))
#         if not created:
#             continue
#         if created < cutoff:
#             continue
#
#         total += 1
#         status = (r.get("status") or "").lower()
#
#         # Still waiting → not a response yet
#         if status == "pending":
#             continue
#
#         responded += 1
#         responded_at = _parse_dt(r.get("responded_at")) or created
#         delta = (responded_at - created).total_seconds() / 60.0
#         if delta >= 0:
#             response_minutes.append(delta)
#
#     rate = round((responded / total) * 100, 1) if total else 0.0
#     avg_min = round(sum(response_minutes) / len(response_minutes), 1) if response_minutes else None
#
#     # Human label
#     if avg_min is None:
#         label = "New"
#     elif avg_min <= 60:
#         label = "Usually responds within an hour"
#     elif avg_min <= 180:
#         label = "Usually responds within a few hours"
#     elif avg_min <= 1440:
#         label = "Usually responds within a day"
#     else:
#         label = "May take longer to respond"
#
#     return {
#         "response_rate": rate,
#         "response_rate_pct": rate,
#         "total_requests": total,
#         "responded_count": responded,
#         "pending_count": max(total - responded, 0),
#         "avg_response_minutes": avg_min,
#         "response_label": label,
#         "window_days": window_days,
#     }
#
#
# async def _load_incoming(db, companion_id: str):
#     rows = await db.prepare(
#         """
#         SELECT id, status, created_at, responded_at
#         FROM bookings
#         WHERE rent_person_id = ?
#         ORDER BY created_at DESC
#         LIMIT 200
#         """
#     ).bind(companion_id).all()
#     items = rows.results if hasattr(rows, "results") else rows
#     return [dict(r) for r in items]
#
#
# @router.get("/people/{user_id}/response-rate")
# async def public_response_rate(
#     user_id: str,
#     request: Request,
#     days: int = Query(30, ge=7, le=90),
# ):
#     """
#     Public: show on companion profile / people card.
#     GET /api/people/{id}/response-rate?days=30
#     """
#     db = request.scope["env"].DB
#
#     user = await db.prepare(
#         "SELECT id, full_name, want_to FROM users WHERE id = ?"
#     ).bind(user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     rows = await _load_incoming(db, user_id)
#     stats = _compute_stats(rows, window_days=days)
#
#     return {
#         "user_id": user_id,
#         **stats,
#     }
#
#
# @router.get("/response-rate/me")
# async def my_response_rate(
#     request: Request,
#     current_user: dict = Depends(get_current_user),
#     days: int = Query(30, ge=7, le=90),
# ):
#     """Companion dashboard: GET /api/response-rate/me"""
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#     rows = await _load_incoming(db, user_id)
#     stats = _compute_stats(rows, window_days=days)
#     return {"user_id": user_id, **stats}


from fastapi import APIRouter, Request, Depends, HTTPException, Query
from routes.profile import get_current_user
from datetime import datetime, timedelta
from typing import Optional, List, Any

router = APIRouter()

# Statuses that count as "companion responded"
RESPONDED_STATUSES = {
    "approved",
    "accepted",
    "rejected",
    "completed",
    "cancelled",
    "canceled",
    "declined",
}


def _parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        s = str(value).strip().replace("Z", "")
        # "2026-10-25 12:00:00" → iso-friendly
        if " " in s and "T" not in s:
            s = s.replace(" ", "T", 1)
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _compute_stats(rows: List[dict], window_days: int = 30) -> dict:
    """
    total   = bookings in window (companion is rent_person_id)
    responded = status not pending (approved/rejected/etc.)
    rate    = responded / total * 100
    avg time = mean(responded_at - created_at) in minutes
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(days=window_days)

    total = 0
    responded = 0
    pending = 0
    response_minutes: List[float] = []

    for r in rows:
        created = _parse_dt(r.get("created_at"))
        if not created:
            continue
        if created < cutoff:
            continue

        total += 1
        status = (r.get("status") or "").strip().lower()

        if status == "pending" or status not in RESPONDED_STATUSES:
            if status == "pending":
                pending += 1
            # unknown status → treat as not responded
            if status != "pending" and status not in RESPONDED_STATUSES:
                pending += 1
            continue

        responded += 1
        responded_at = (
            _parse_dt(r.get("responded_at"))
            or _parse_dt(r.get("updated_at"))
            or created
        )
        delta_min = (responded_at - created).total_seconds() / 60.0
        if delta_min < 0:
            delta_min = 0.0
        response_minutes.append(delta_min)

    rate = round((responded / total) * 100.0, 1) if total else 0.0
    avg_min = (
        round(sum(response_minutes) / len(response_minutes), 1)
        if response_minutes
        else None
    )

    if total == 0:
        label = "New"
    elif avg_min is None:
        label = "New"
    elif avg_min <= 60:
        label = "Usually responds within an hour"
    elif avg_min <= 180:
        label = "Usually responds within a few hours"
    elif avg_min <= 1440:
        label = "Usually responds within a day"
    else:
        label = "May take longer to respond"

    return {
        "response_rate": rate,
        "response_rate_pct": rate,
        "total_requests": total,
        "responded_count": responded,
        "pending_count": pending,
        "avg_response_minutes": avg_min,
        "response_label": label,
        "window_days": window_days,
    }


async def _load_incoming(db, companion_id: str) -> List[dict]:
    try:
        rows = await db.prepare(
            """
            SELECT id, status, created_at, responded_at, updated_at
            FROM bookings
            WHERE rent_person_id = ?
            ORDER BY created_at DESC
            LIMIT 300
            """
        ).bind(companion_id).all()
    except Exception:
        # older schema without responded_at / updated_at
        rows = await db.prepare(
            """
            SELECT id, status, created_at
            FROM bookings
            WHERE rent_person_id = ?
            ORDER BY created_at DESC
            LIMIT 300
            """
        ).bind(companion_id).all()

    items = rows.results if hasattr(rows, "results") else rows
    return [dict(r) for r in items]


@router.get("/people/{user_id}/response-rate")
async def public_response_rate(
    user_id: str,
    request: Request,
    days: int = Query(30, ge=7, le=90),
):
    """
    Public — companion profile / card
    GET /api/people/{id}/response-rate?days=30
    """
    db = request.scope["env"].DB

    user = await db.prepare(
        "SELECT id FROM users WHERE id = ?"
    ).bind(user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    rows = await _load_incoming(db, user_id)
    stats = _compute_stats(rows, window_days=days)

    return {
        "user_id": user_id,
        **stats,
    }


@router.get("/response-rate/me")
async def my_response_rate(
    request: Request,
    current_user: dict = Depends(get_current_user),
    days: int = Query(30, ge=7, le=90),
):
    """
    Companion dashboard
    GET /api/response-rate/me?days=30
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]
    rows = await _load_incoming(db, user_id)
    stats = _compute_stats(rows, window_days=days)

    return {
        "user_id": user_id,
        **stats,
    }