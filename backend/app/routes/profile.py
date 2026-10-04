# from fastapi import APIRouter, Request, Depends, HTTPException, status
# from models.user import ProfileUpdate
# from utils.security import decode_access_token
# import json
#
# router = APIRouter()
#
#
# def _parse_json_field(value, default=None):
#     if default is None:
#         default = []
#     if value is None:
#         return default
#     if isinstance(value, (list, dict)):
#         return value
#     try:
#         return json.loads(value)
#     except Exception:
#         return default
#
#
# async def get_current_user(request: Request):
#     auth_header = request.headers.get("Authorization")
#     if not auth_header or not auth_header.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Not authenticated")
#
#     token = auth_header.split(" ")[1]
#     payload = decode_access_token(token)
#     user_id = payload.get("sub")
#     if not user_id:
#         raise HTTPException(status_code=401, detail="Invalid token")
#
#     db = request.scope["env"].DB
#     user = await db.prepare("SELECT * FROM users WHERE id = ?").bind(user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     return dict(user)
#
#
# @router.get("/profile")
# async def get_profile(current_user: dict = Depends(get_current_user)):
#     return {
#         "id": current_user["id"],
#         "fullName": current_user.get("full_name") or "",
#         "email": current_user["email"],
#         "phone": current_user.get("mobile") or "",
#         "city": current_user.get("city") or "",
#         "gender": current_user.get("gender") or "",
#         "price": current_user.get("price") or 1500,
#         "bio": current_user.get("bio") or "",
#         "image": current_user.get("image") or "",  # R2 URL
#         "isAvailable": bool(current_user.get("is_available", 1)),
#         "availableTime": current_user.get("available_time") or "",
#         "languages": _parse_json_field(current_user.get("languages"), []),
#         "interests": _parse_json_field(current_user.get("interests"), []),
#         "services": _parse_json_field(current_user.get("services"), []),
#         "gallery": _parse_json_field(current_user.get("gallery"), []),  # R2 URLs
#         "lat": current_user.get("lat"),
#         "lng": current_user.get("lng"),
#     }
#
# @router.patch("/profile")
# @router.put("/profile")
# async def update_profile(
#     data: ProfileUpdate,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#
#     updates = []
#     values = []
#
#     if data.fullName is not None:
#         updates.append("full_name = ?")
#         values.append(data.fullName)
#     if data.phone is not None:
#         updates.append("mobile = ?")
#         values.append(data.phone)
#     if data.city is not None:
#         updates.append("city = ?")
#         values.append(data.city)
#     if data.gender is not None:
#         updates.append("gender = ?")
#         values.append(data.gender)
#     if data.price is not None:
#         updates.append("price = ?")
#         values.append(data.price)
#     if data.bio is not None:
#         updates.append("bio = ?")
#         values.append(data.bio)
#     if data.image is not None:
#         updates.append("image = ?")
#         values.append(data.image)
#     if data.isAvailable is not None:
#         updates.append("is_available = ?")
#         values.append(1 if data.isAvailable else 0)
#     if data.availableTime is not None:
#         updates.append("available_time = ?")
#         values.append(
#             data.availableTime
#             if isinstance(data.availableTime, str)
#             else json.dumps(data.availableTime)
#         )
#     if data.languages is not None:
#         updates.append("languages = ?")
#         values.append(
#             data.languages
#             if isinstance(data.languages, str)
#             else json.dumps(data.languages)
#         )
#     if data.interests is not None:
#         updates.append("interests = ?")
#         values.append(
#             data.interests
#             if isinstance(data.interests, str)
#             else json.dumps(data.interests)
#         )
#     if data.lat is not None:
#         updates.append("lat = ?")
#         values.append(data.lat)
#     if data.lng is not None:
#         updates.append("lng = ?")
#         values.append(data.lng)
#     if data.services is not None:
#         updates.append("services = ?")
#         serialized = []
#         for s in data.services:
#             if hasattr(s, "model_dump"):
#                 serialized.append(s.model_dump())
#             elif isinstance(s, dict):
#                 serialized.append(s)
#             else:
#                 serialized.append({"name": str(s)})
#         values.append(json.dumps(serialized))
#     if data.gallery is not None:
#         updates.append("gallery = ?")
#         values.append(json.dumps(data.gallery))
#
#     if not updates:
#         raise HTTPException(status_code=400, detail="No fields to update")
#
#     values.append(user_id)
#     query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
#     await db.prepare(query).bind(*values).run()
#
#     return {"message": "Profile updated successfully"}


from fastapi import APIRouter, Request, Depends, HTTPException, status, Query
from models.user import ProfileUpdate
from utils.security import decode_access_token
import json
import uuid

router = APIRouter()

R2_PUBLIC_URL = "https://pub-da3163e6bec745449d684b720f3a6b4c.r2.dev"


def _parse_json_field(value, default=None):
    if default is None:
        default = []
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _ext_from_content_type(content_type: str) -> str:
    if "png" in content_type:
        return "png"
    if "webp" in content_type:
        return "webp"
    if "gif" in content_type:
        return "gif"
    return "jpg"


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
        "languages": _parse_json_field(current_user.get("languages"), []),
        "interests": _parse_json_field(current_user.get("interests"), []),
        "services": _parse_json_field(current_user.get("services"), []),
        "gallery": _parse_json_field(current_user.get("gallery"), []),
        "lat": current_user.get("lat"),
        "lng": current_user.get("lng"),
    }


@router.patch("/profile")
@router.put("/profile")
async def update_profile(
    data: ProfileUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Partial update — only fields sent in body are changed (PATCH-safe)."""
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
        values.append(
            data.availableTime
            if isinstance(data.availableTime, str)
            else json.dumps(data.availableTime)
        )
    if data.languages is not None:
        updates.append("languages = ?")
        values.append(
            data.languages
            if isinstance(data.languages, str)
            else json.dumps(data.languages)
        )
    if data.interests is not None:
        updates.append("interests = ?")
        values.append(
            data.interests
            if isinstance(data.interests, str)
            else json.dumps(data.interests)
        )
    if data.lat is not None:
        updates.append("lat = ?")
        values.append(data.lat)
    if data.lng is not None:
        updates.append("lng = ?")
        values.append(data.lng)
    if data.services is not None:
        updates.append("services = ?")
        serialized = []
        for s in data.services:
            if hasattr(s, "model_dump"):
                serialized.append(s.model_dump())
            elif isinstance(s, dict):
                serialized.append(s)
            else:
                serialized.append({"name": str(s)})
        values.append(json.dumps(serialized))
    if data.gallery is not None:
        updates.append("gallery = ?")
        values.append(json.dumps(data.gallery))

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    values.append(user_id)
    query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
    await db.prepare(query).bind(*values).run()

    return {"message": "Profile updated successfully"}


@router.post("/profile/photo")
async def upload_profile_photo(
    request: Request,
    current_user: dict = Depends(get_current_user),
    type: str = Query("avatar", pattern="^(avatar|gallery)$"),
):
    """
    Single photo upload:
      POST /api/profile/photo?type=avatar
      POST /api/profile/photo?type=gallery
    Body = raw image bytes
    """
    content_type = request.headers.get("content-type", "image/jpeg")
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="No file received")

    user_id = current_user["id"]
    ext = _ext_from_content_type(content_type)
    images = request.scope["env"].IMAGES
    db = request.scope["env"].DB

    if type == "avatar":
        key = f"profiles/{user_id}/avatar.{ext}"
        await images.put(key, body, httpMetadata={"contentType": content_type})
        image_url = f"{R2_PUBLIC_URL}/{key}"

        await db.prepare(
            "UPDATE users SET image = ? WHERE id = ?"
        ).bind(image_url, user_id).run()

        return {
            "type": "avatar",
            "image": image_url,
            "message": "Avatar uploaded successfully",
        }

    file_id = str(uuid.uuid4())[:8]
    key = f"profiles/{user_id}/gallery/{file_id}.{ext}"
    await images.put(key, body, httpMetadata={"contentType": content_type})
    image_url = f"{R2_PUBLIC_URL}/{key}"

    row = await db.prepare(
        "SELECT gallery FROM users WHERE id = ?"
    ).bind(user_id).first()

    gallery = []
    if row:
        raw = dict(row).get("gallery")
        if raw:
            try:
                gallery = json.loads(raw) if isinstance(raw, str) else list(raw)
            except Exception:
                gallery = []

    if image_url not in gallery:
        gallery.append(image_url)
    gallery = gallery[-6:]

    await db.prepare(
        "UPDATE users SET gallery = ? WHERE id = ?"
    ).bind(json.dumps(gallery), user_id).run()

    return {
        "type": "gallery",
        "url": image_url,
        "gallery": gallery,
        "message": "Gallery image uploaded successfully",
    }