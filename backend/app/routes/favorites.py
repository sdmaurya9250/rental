from fastapi import APIRouter, Request, Depends, HTTPException, status
from routes.profile import get_current_user
import secrets
import json

router = APIRouter()


def _parse_list(value, default=None):
    if default is None:
        default = []
    if value is None:
        return default
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
    except Exception:
        pass
    if isinstance(value, str) and value.strip():
        return [x.strip() for x in value.split(",") if x.strip()]
    return default


def _format_person(r: dict) -> dict:
    price = int(r.get("price") or 1500)
    services = _parse_list(r.get("services"), [])
    tags = []
    for s in services:
        if isinstance(s, dict) and s.get("name"):
            tags.append(s["name"])
        elif isinstance(s, str):
            tags.append(s)
    if not tags:
        tags = _parse_list(r.get("interests"), [])

    return {
        "id": r["id"],
        "name": r.get("full_name") or "User",
        "location": r.get("city") or "",
        "price": f"₹{price:,}/hr",
        "priceValue": price,
        "isOnline": bool(r.get("is_available", 0)),
        "tags": tags[:4],
        "image": r.get("image") or "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=600&auto=format&fit=crop",
        "gender": r.get("gender") or "",
        "bio": r.get("bio") or "",
    }


@router.get("/favorites")
async def list_favorites(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """List people I have favorited."""
    db = request.scope["env"].DB
    user_id = current_user["id"]

    rows = await db.prepare(
        """
        SELECT u.id, u.full_name, u.city, u.gender, u.price, u.bio, u.image,
               u.is_available, u.services, u.interests
        FROM favorites f
        JOIN users u ON u.id = f.favorite_user_id
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC
        """
    ).bind(user_id).all()

    items = rows.results if hasattr(rows, "results") else rows
    people = [_format_person(dict(row)) for row in items]

    return {
        "count": len(people),
        "people": people,
        "favorites": people,  # alias for frontend flexibility
    }


@router.post("/favorites/{favorite_user_id}", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite_user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Add a person to my favorites."""
    db = request.scope["env"].DB
    user_id = current_user["id"]

    if favorite_user_id == user_id:
        raise HTTPException(status_code=400, detail="You cannot favorite yourself")

    # Check person exists
    person = await db.prepare(
        "SELECT id FROM users WHERE id = ?"
    ).bind(favorite_user_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    # Already favorited?
    existing = await db.prepare(
        "SELECT id FROM favorites WHERE user_id = ? AND favorite_user_id = ?"
    ).bind(user_id, favorite_user_id).first()
    if existing:
        return {"message": "Already in favorites", "favorite_user_id": favorite_user_id}

    fav_id = secrets.token_hex(8)
    await db.prepare(
        "INSERT INTO favorites (id, user_id, favorite_user_id) VALUES (?, ?, ?)"
    ).bind(fav_id, user_id, favorite_user_id).run()

    return {
        "id": fav_id,
        "message": "Added to favorites",
        "favorite_user_id": favorite_user_id,
    }


@router.delete("/favorites/{favorite_user_id}")
async def remove_favorite(
    favorite_user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Remove a person from my favorites."""
    db = request.scope["env"].DB
    user_id = current_user["id"]

    result = await db.prepare(
        "DELETE FROM favorites WHERE user_id = ? AND favorite_user_id = ?"
    ).bind(user_id, favorite_user_id).run()

    # D1 run() may not return changes count the same way — still OK
    return {
        "message": "Removed from favorites",
        "favorite_user_id": favorite_user_id,
    }


@router.get("/favorites/check/{favorite_user_id}")
async def check_favorite(
    favorite_user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Check if a person is in my favorites (for heart icon)."""
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT id FROM favorites WHERE user_id = ? AND favorite_user_id = ?"
    ).bind(user_id, favorite_user_id).first()

    return {
        "is_favorite": row is not None,
        "favorite_user_id": favorite_user_id,
    }