from fastapi import APIRouter, Request, Depends, HTTPException, status
from models.user import ProfileUpdate
from utils.security import decode_access_token
import json

router = APIRouter()


async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = request.scope["env"].DB
    user = await db.prepare("SELECT * FROM users WHERE id = ?").bind(user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return dict(user)


@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "fullName": current_user.get("full_name") or "",
        "email": current_user["email"],
        "phone": current_user.get("mobile") or "",
        "city": current_user.get("city") or "",
        "gender": current_user.get("gender") or "",
        "price": current_user.get("price") or 1500,
        "bio": current_user.get("bio") or "",
        "image": current_user.get("image") or "",
        "isAvailable": bool(current_user.get("is_available", 1)),
        "availableTime": current_user.get("available_time") or "",
        "languages": current_user.get("languages") or "",
        "interests": current_user.get("interests") or "",
        "services": json.loads(current_user.get("services") or "[]"),
        "gallery": json.loads(current_user.get("gallery") or "[]"),
        "lat": current_user.get("lat"),
        "lng": current_user.get("lng"),
    }


@router.put("/profile")
async def update_profile(
    data: ProfileUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    updates = []
    values = []

    if data.fullName is not None:
        updates.append("full_name = ?")
        values.append(data.fullName)
    if data.phone is not None:
        updates.append("mobile = ?")
        values.append(data.phone)
    if data.city is not None:
        updates.append("city = ?")
        values.append(data.city)
    if data.gender is not None:
        updates.append("gender = ?")
        values.append(data.gender)
    if data.price is not None:
        updates.append("price = ?")
        values.append(data.price)
    if data.bio is not None:
        updates.append("bio = ?")
        values.append(data.bio)
    if data.image is not None:
        updates.append("image = ?")
        values.append(data.image)
    if data.isAvailable is not None:
        updates.append("is_available = ?")
        values.append(1 if data.isAvailable else 0)
    if data.availableTime is not None:
        updates.append("available_time = ?")
        values.append(data.availableTime)
    if data.languages is not None:
        updates.append("languages = ?")
        values.append(data.languages)
    if data.interests is not None:
        updates.append("interests = ?")
        values.append(data.interests)

    if data.lat is not None:
        updates.append("lat = ?")
        values.append(data.lat)
    if data.lng is not None:
        updates.append("lng = ?")
        values.append(data.lng)

    # Fixed: properly handle list of ServiceItem objects
    if data.services is not None:
        updates.append("services = ?")
        values.append(json.dumps([s.model_dump() for s in data.services]))

    if data.gallery is not None:
        updates.append("gallery = ?")
        values.append(json.dumps(data.gallery))

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(user_id)
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"

    await db.prepare(query).bind(*values).run()

    return {"message": "Profile updated successfully"}