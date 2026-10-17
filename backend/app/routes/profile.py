# from fastapi import APIRouter, Request, Depends, HTTPException, status, Query
# from models.user import ProfileUpdate
# from utils.security import decode_access_token
# import json
# import uuid
#
# router = APIRouter()
#
# R2_PUBLIC_URL = "https://pub-da3163e6bec745449d684b720f3a6b4c.r2.dev"
# MAX_GALLERY = 4
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
# def _norm_preferred_locations(raw) -> list:
#     """Normalize [{name, address, lat, lng}, ...] or string names."""
#     if raw is None:
#         return []
#     if isinstance(raw, str):
#         try:
#             raw = json.loads(raw)
#         except Exception:
#             raw = [raw] if raw.strip() else []
#     if not isinstance(raw, list):
#         return []
#
#     out = []
#     for item in raw:
#         if hasattr(item, "model_dump"):
#             d = item.model_dump()
#         elif isinstance(item, dict):
#             d = item
#         elif isinstance(item, str) and item.strip():
#             d = {"name": item.strip()}
#         else:
#             continue
#         name = (d.get("name") or d.get("title") or "").strip()
#         if not name:
#             continue
#         loc = {"name": name[:200]}
#         addr = d.get("address")
#         if addr is not None and str(addr).strip():
#             loc["address"] = str(addr).strip()[:300]
#         try:
#             if d.get("lat") is not None:
#                 loc["lat"] = float(d["lat"])
#             if d.get("lng") is not None:
#                 loc["lng"] = float(d["lng"])
#         except (TypeError, ValueError):
#             pass
#         out.append(loc)
#     return out
#
#
# def _norm_location_names(raw, preferred: list) -> list:
#     names: list[str] = []
#     if isinstance(raw, list):
#         for x in raw:
#             if isinstance(x, str) and x.strip():
#                 names.append(x.strip()[:200])
#             elif isinstance(x, dict) and (x.get("name") or "").strip():
#                 names.append(str(x["name"]).strip()[:200])
#     for p in preferred:
#         n = (p.get("name") or "").strip()
#         if n and n not in names:
#             names.append(n)
#     return names
#
#
# def _normalize_service(item, index: int = 0) -> dict:
#     if hasattr(item, "model_dump"):
#         d = item.model_dump()
#     elif isinstance(item, dict):
#         d = item
#     else:
#         d = {}
#
#     name = (d.get("name") or d.get("title") or f"Service {index + 1}").strip()
#     sid = (d.get("id") or "").strip() or f"svc_{uuid.uuid4().hex[:8]}"
#     try:
#         price = int(d.get("price") or 0)
#     except (TypeError, ValueError):
#         price = 0
#     duration = (d.get("duration") or "1 hr").strip() or "1 hr"
#
#     preferred = _norm_preferred_locations(
#         d.get("preferred_locations") or d.get("preferredLocations")
#     )
#     locations = _norm_location_names(
#         d.get("locations") or d.get("location_names"),
#         preferred,
#     )
#
#     return {
#         "id": sid,
#         "name": name,
#         "title": name,
#         "price": price,
#         "duration": duration,
#         "locations": locations,
#         "preferred_locations": preferred,
#     }
#
#
# def _normalize_services(raw) -> list:
#     items = _parse_json_field(raw, [])
#     if not isinstance(items, list):
#         return []
#     return [_normalize_service(s, i) for i, s in enumerate(items)]
#
#
# def _ext_from_content_type(content_type: str) -> str:
#     ct = (content_type or "").lower()
#     if "png" in ct:
#         return "png"
#     if "webp" in ct:
#         return "webp"
#     if "gif" in ct:
#         return "gif"
#     return "jpg"
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
# async def _read_image_bytes(request: Request) -> tuple[bytes, str]:
#     content_type = (request.headers.get("content-type") or "").lower()
#
#     if "multipart/form-data" in content_type:
#         try:
#             form = await request.form()
#         except Exception as e:
#             raise HTTPException(
#                 status_code=400,
#                 detail=(
#                     f"Could not parse multipart form: {e}. "
#                     "Send raw image body with Content-Type: image/jpeg instead."
#                 ),
#             )
#
#         file = (
#             form.get("file")
#             or form.get("photo")
#             or form.get("image")
#             or form.get("avatar")
#         )
#         if file is None:
#             raise HTTPException(
#                 status_code=400,
#                 detail="No file field. Use form field name: file | photo | image",
#             )
#
#         if hasattr(file, "read"):
#             body = await file.read()
#             ct = getattr(file, "content_type", None) or "image/jpeg"
#         elif isinstance(file, (bytes, bytearray)):
#             body = bytes(file)
#             ct = "image/jpeg"
#         else:
#             raise HTTPException(status_code=400, detail="Invalid file field")
#
#         if not body:
#             raise HTTPException(status_code=400, detail="Empty file")
#         if not str(ct).startswith("image/"):
#             ct = "image/jpeg"
#         return body, str(ct)
#
#     if not content_type.startswith("image/") and "octet-stream" not in content_type:
#         if content_type:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Send image/* or multipart/form-data with field 'file'",
#             )
#
#     body = await request.body()
#     if not body:
#         raise HTTPException(status_code=400, detail="No file received")
#
#     ct = content_type if content_type.startswith("image/") else "image/jpeg"
#     return body, ct
#
#
# @router.get("/profile")
# async def get_profile(current_user: dict = Depends(get_current_user)):
#     services = _normalize_services(current_user.get("services"))
#     gallery = _parse_json_field(current_user.get("gallery"), [])
#     preferred_locations = _norm_preferred_locations(
#         current_user.get("preferred_locations")
#     )
#
#     languages = _parse_json_field(current_user.get("languages"), [])
#     if not languages and isinstance(current_user.get("languages"), str):
#         raw = (current_user.get("languages") or "").strip()
#         if raw and not raw.startswith("["):
#             languages = [x.strip() for x in raw.split(",") if x.strip()]
#
#     interests = _parse_json_field(current_user.get("interests"), [])
#     if not interests and isinstance(current_user.get("interests"), str):
#         raw = (current_user.get("interests") or "").strip()
#         if raw and not raw.startswith("["):
#             interests = [x.strip() for x in raw.split(",") if x.strip()]
#
#     available_time = current_user.get("available_time") or ""
#     parsed_time = _parse_json_field(available_time, None)
#     if parsed_time is not None and not isinstance(parsed_time, str):
#         available_time = parsed_time
#
#     available = float(current_user.get("wallet_balance") or 0)
#     held = float(current_user.get("wallet_held") or 0)
#
#     return {
#         "id": current_user["id"],
#         "account_id": current_user["id"],
#         "fullName": current_user.get("full_name") or "",
#         "name": current_user.get("full_name") or "",
#         "email": current_user["email"],
#         "phone": current_user.get("mobile") or "",
#         "mobile": current_user.get("mobile") or "",
#         "city": current_user.get("city") or "",
#         "country": current_user.get("country") or "",
#         "gender": current_user.get("gender") or "",
#         "want_to": current_user.get("want_to") or "",
#         "role": current_user.get("want_to") or "",
#         "price": current_user.get("price") or 1500,
#         "bio": current_user.get("bio") or "",
#         "image": current_user.get("image") or "",
#         "isAvailable": bool(current_user.get("is_available", 1)),
#         "availableTime": available_time,
#         "languages": languages,
#         "interests": interests,
#         "services": services,
#         "gallery": gallery,
#         "preferred_locations": preferred_locations,
#         "preferredLocations": preferred_locations,
#         "lat": current_user.get("lat"),
#         "lng": current_user.get("lng"),
#         "rating_avg": float(current_user.get("rating_avg") or 0),
#         "rating_count": int(current_user.get("rating_count") or 0),
#         "wallet_balance": available,
#         "available_balance": available,
#         "wallet_held": held,
#         "held_balance": held,
#         "total_balance": available + held,
#     }
#
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
#     # Also accept raw body keys not on ProfileUpdate (preferred_locations, etc.)
#     try:
#         body = await request.json()
#     except Exception:
#         body = {}
#     if not isinstance(body, dict):
#         body = {}
#
#     updates = []
#     values = []
#
#     full_name = data.fullName if data.fullName is not None else data.name
#     if full_name is not None:
#         updates.append("full_name = ?")
#         values.append(full_name)
#
#     if data.phone is not None:
#         updates.append("mobile = ?")
#         values.append(data.phone)
#
#     if data.city is not None:
#         updates.append("city = ?")
#         values.append(data.city)
#
#     if data.gender is not None:
#         updates.append("gender = ?")
#         values.append(data.gender)
#
#     if data.price is not None:
#         updates.append("price = ?")
#         values.append(data.price)
#
#     if data.bio is not None:
#         updates.append("bio = ?")
#         values.append(data.bio)
#
#     if data.image is not None:
#         updates.append("image = ?")
#         values.append(data.image)
#
#     if data.isAvailable is not None:
#         updates.append("is_available = ?")
#         values.append(1 if data.isAvailable else 0)
#
#     if data.availableTime is not None:
#         updates.append("available_time = ?")
#         if isinstance(data.availableTime, (dict, list)):
#             values.append(json.dumps(data.availableTime))
#         else:
#             values.append(data.availableTime)
#
#     if data.languages is not None:
#         updates.append("languages = ?")
#         if isinstance(data.languages, list):
#             values.append(json.dumps(data.languages))
#         else:
#             values.append(data.languages)
#
#     if data.interests is not None:
#         updates.append("interests = ?")
#         if isinstance(data.interests, list):
#             values.append(json.dumps(data.interests))
#         else:
#             values.append(data.interests)
#
#     if data.lat is not None:
#         updates.append("lat = ?")
#         values.append(data.lat)
#
#     if data.lng is not None:
#         updates.append("lng = ?")
#         values.append(data.lng)
#
#     # Services — keep locations + preferred_locations
#     if data.services is not None:
#         services = [
#             _normalize_service(
#                 s.model_dump() if hasattr(s, "model_dump") else s, i
#             )
#             for i, s in enumerate(data.services)
#         ]
#         updates.append("services = ?")
#         values.append(json.dumps(services))
#     elif "services" in body and isinstance(body.get("services"), list):
#         services = [_normalize_service(s, i) for i, s in enumerate(body["services"])]
#         updates.append("services = ?")
#         values.append(json.dumps(services))
#
#     if data.gallery is not None:
#         updates.append("gallery = ?")
#         values.append(json.dumps(data.gallery[:MAX_GALLERY]))
#
#     # Profile-level preferred places
#     pref_raw = None
#     if hasattr(data, "preferred_locations") and data.preferred_locations is not None:
#         pref_raw = data.preferred_locations
#     elif hasattr(data, "preferredLocations") and getattr(data, "preferredLocations", None) is not None:
#         pref_raw = data.preferredLocations
#     elif "preferred_locations" in body:
#         pref_raw = body.get("preferred_locations")
#     elif "preferredLocations" in body:
#         pref_raw = body.get("preferredLocations")
#
#     if pref_raw is not None:
#         preferred = _norm_preferred_locations(pref_raw)
#         updates.append("preferred_locations = ?")
#         values.append(json.dumps(preferred))
#
#     if not updates:
#         raise HTTPException(status_code=400, detail="No fields to update")
#
#     values.append(user_id)
#     query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
#     await db.prepare(query).bind(*values).run()
#
#     return {"message": "Profile updated successfully"}
#
#
# @router.post("/profile/photo")
# async def upload_profile_photo(
#     request: Request,
#     current_user: dict = Depends(get_current_user),
#     type: str = Query("avatar", description="avatar | gallery"),
#     index: int = Query(0, ge=0, le=3, description="Gallery slot 0-3 when type=gallery"),
# ):
#     photo_type = (type or "avatar").lower().strip()
#     if photo_type not in ("avatar", "gallery"):
#         raise HTTPException(status_code=400, detail="type must be avatar or gallery")
#
#     body, content_type = await _read_image_bytes(request)
#     user_id = current_user["id"]
#     ext = _ext_from_content_type(content_type)
#     images = request.scope["env"].IMAGES
#     db = request.scope["env"].DB
#
#     if photo_type == "avatar":
#         key = f"profiles/{user_id}/avatar.{ext}"
#         await images.put(key, body, httpMetadata={"contentType": content_type})
#         image_url = f"{R2_PUBLIC_URL}/{key}"
#
#         await db.prepare(
#             "UPDATE users SET image = ? WHERE id = ?"
#         ).bind(image_url, user_id).run()
#
#         return {
#             "image": image_url,
#             "url": image_url,
#             "type": "avatar",
#             "message": "Avatar uploaded successfully",
#         }
#
#     file_id = str(uuid.uuid4())[:8]
#     key = f"profiles/{user_id}/gallery/{file_id}.{ext}"
#     await images.put(key, body, httpMetadata={"contentType": content_type})
#     image_url = f"{R2_PUBLIC_URL}/{key}"
#
#     row = await db.prepare(
#         "SELECT gallery FROM users WHERE id = ?"
#     ).bind(user_id).first()
#
#     gallery = []
#     if row:
#         raw = dict(row).get("gallery")
#         if raw:
#             try:
#                 gallery = json.loads(raw) if isinstance(raw, str) else list(raw)
#             except Exception:
#                 gallery = []
#
#     if not isinstance(gallery, list):
#         gallery = []
#
#     while len(gallery) < MAX_GALLERY:
#         gallery.append("")
#
#     used_index = min(int(index), MAX_GALLERY - 1)
#     gallery[used_index] = image_url
#     gallery = [g for g in gallery if g][:MAX_GALLERY]
#
#     await db.prepare(
#         "UPDATE users SET gallery = ? WHERE id = ?"
#     ).bind(json.dumps(gallery), user_id).run()
#
#     return {
#         "url": image_url,
#         "image": image_url,
#         "gallery": gallery,
#         "index": used_index,
#         "type": "gallery",
#         "message": "Gallery image uploaded successfully",
#     }



from fastapi import APIRouter, Request, Depends, HTTPException, status, Query
from models.user import ProfileUpdate
from utils.security import decode_access_token
import json
import uuid

router = APIRouter()

R2_PUBLIC_URL = "https://pub-da3163e6bec745449d684b720f3a6b4c.r2.dev"
MAX_GALLERY = 4


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


def _norm_preferred_locations(raw) -> list:
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = [raw] if raw.strip() else []
    if not isinstance(raw, list):
        return []

    out = []
    for item in raw:
        if hasattr(item, "model_dump"):
            d = item.model_dump()
        elif isinstance(item, dict):
            d = item
        elif isinstance(item, str) and item.strip():
            d = {"name": item.strip()}
        else:
            continue
        name = (d.get("name") or d.get("title") or "").strip()
        if not name:
            continue
        loc = {"name": name[:200]}
        addr = d.get("address")
        if addr is not None and str(addr).strip():
            loc["address"] = str(addr).strip()[:300]
        try:
            if d.get("lat") is not None:
                loc["lat"] = float(d["lat"])
            if d.get("lng") is not None:
                loc["lng"] = float(d["lng"])
        except (TypeError, ValueError):
            pass
        out.append(loc)
    return out


def _norm_location_names(raw, preferred: list) -> list:
    names: list[str] = []
    if isinstance(raw, list):
        for x in raw:
            if isinstance(x, str) and x.strip():
                names.append(x.strip()[:200])
            elif isinstance(x, dict) and (x.get("name") or "").strip():
                names.append(str(x["name"]).strip()[:200])
    for p in preferred:
        n = (p.get("name") or "").strip()
        if n and n not in names:
            names.append(n)
    return names


def _normalize_service(item, index: int = 0) -> dict:
    if hasattr(item, "model_dump"):
        d = item.model_dump()
    elif isinstance(item, dict):
        d = item
    else:
        d = {}

    name = (d.get("name") or d.get("title") or f"Service {index + 1}").strip()
    sid = (d.get("id") or "").strip() or f"svc_{uuid.uuid4().hex[:8]}"
    try:
        price = int(d.get("price") or 0)
    except (TypeError, ValueError):
        price = 0
    duration = (d.get("duration") or "1 hr").strip() or "1 hr"

    preferred = _norm_preferred_locations(
        d.get("preferred_locations") or d.get("preferredLocations")
    )
    locations = _norm_location_names(
        d.get("locations") or d.get("location_names"),
        preferred,
    )

    return {
        "id": sid,
        "name": name,
        "title": name,
        "price": price,
        "duration": duration,
        "locations": locations,
        "preferred_locations": preferred,
    }


def _normalize_services(raw) -> list:
    items = _parse_json_field(raw, [])
    if not isinstance(items, list):
        return []
    return [_normalize_service(s, i) for i, s in enumerate(items)]


def _ext_from_content_type(content_type: str) -> str:
    ct = (content_type or "").lower()
    if "png" in ct:
        return "png"
    if "webp" in ct:
        return "webp"
    if "gif" in ct:
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


async def _read_image_bytes(request: Request) -> tuple[bytes, str]:
    content_type = (request.headers.get("content-type") or "").lower()

    if "multipart/form-data" in content_type:
        try:
            form = await request.form()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Could not parse multipart form: {e}. "
                    "Send raw image body with Content-Type: image/jpeg instead."
                ),
            )

        file = (
            form.get("file")
            or form.get("photo")
            or form.get("image")
            or form.get("avatar")
        )
        if file is None:
            raise HTTPException(
                status_code=400,
                detail="No file field. Use form field name: file | photo | image",
            )

        if hasattr(file, "read"):
            body = await file.read()
            ct = getattr(file, "content_type", None) or "image/jpeg"
        elif isinstance(file, (bytes, bytearray)):
            body = bytes(file)
            ct = "image/jpeg"
        else:
            raise HTTPException(status_code=400, detail="Invalid file field")

        if not body:
            raise HTTPException(status_code=400, detail="Empty file")
        if not str(ct).startswith("image/"):
            ct = "image/jpeg"
        return body, str(ct)

    if not content_type.startswith("image/") and "octet-stream" not in content_type:
        if content_type:
            raise HTTPException(
                status_code=400,
                detail="Send image/* or multipart/form-data with field 'file'",
            )

    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="No file received")

    ct = content_type if content_type.startswith("image/") else "image/jpeg"
    return body, ct


@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    services = _normalize_services(current_user.get("services"))
    gallery = _parse_json_field(current_user.get("gallery"), [])
    preferred_locations = _norm_preferred_locations(
        current_user.get("preferred_locations")
    )

    languages = _parse_json_field(current_user.get("languages"), [])
    if not languages and isinstance(current_user.get("languages"), str):
        raw = (current_user.get("languages") or "").strip()
        if raw and not raw.startswith("["):
            languages = [x.strip() for x in raw.split(",") if x.strip()]

    interests = _parse_json_field(current_user.get("interests"), [])
    if not interests and isinstance(current_user.get("interests"), str):
        raw = (current_user.get("interests") or "").strip()
        if raw and not raw.startswith("["):
            interests = [x.strip() for x in raw.split(",") if x.strip()]

    available_time = current_user.get("available_time") or ""
    parsed_time = _parse_json_field(available_time, None)
    if parsed_time is not None and not isinstance(parsed_time, str):
        available_time = parsed_time

    available = float(current_user.get("wallet_balance") or 0)
    held = float(current_user.get("wallet_held") or 0)

    return {
        "id": current_user["id"],
        "account_id": current_user["id"],
        "fullName": current_user.get("full_name") or "",
        "name": current_user.get("full_name") or "",
        "email": current_user["email"],
        "phone": current_user.get("mobile") or "",
        "mobile": current_user.get("mobile") or "",
        "city": current_user.get("city") or "",
        "country": current_user.get("country") or "",
        "gender": current_user.get("gender") or "",
        "want_to": current_user.get("want_to") or "",
        "role": current_user.get("want_to") or "",
        "price": current_user.get("price") or 1500,
        "bio": current_user.get("bio") or "",
        "image": current_user.get("image") or "",
        "isAvailable": bool(current_user.get("is_available", 1)),
        "availableTime": available_time,
        "languages": languages,
        "interests": interests,
        "services": services,
        "gallery": gallery,
        "preferred_locations": preferred_locations,
        "preferredLocations": preferred_locations,
        "lat": current_user.get("lat"),
        "lng": current_user.get("lng"),
        "rating_avg": float(current_user.get("rating_avg") or 0),
        "rating_count": int(current_user.get("rating_count") or 0),
        "wallet_balance": available,
        "available_balance": available,
        "wallet_held": held,
        "held_balance": held,
        "total_balance": available + held,
    }


@router.patch("/profile")
@router.put("/profile")
async def update_profile(
    data: ProfileUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}

    updates = []
    values = []

    full_name = data.fullName if data.fullName is not None else data.name
    if full_name is not None:
        updates.append("full_name = ?")
        values.append(full_name)

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
        if isinstance(data.availableTime, (dict, list)):
            values.append(json.dumps(data.availableTime))
        else:
            values.append(data.availableTime)

    if data.languages is not None:
        updates.append("languages = ?")
        if isinstance(data.languages, list):
            values.append(json.dumps(data.languages))
        else:
            values.append(data.languages)

    if data.interests is not None:
        updates.append("interests = ?")
        if isinstance(data.interests, list):
            values.append(json.dumps(data.interests))
        else:
            values.append(data.interests)

    if data.lat is not None:
        updates.append("lat = ?")
        values.append(data.lat)

    if data.lng is not None:
        updates.append("lng = ?")
        values.append(data.lng)

    if data.services is not None:
        services = [
            _normalize_service(
                s.model_dump() if hasattr(s, "model_dump") else s, i
            )
            for i, s in enumerate(data.services)
        ]
        updates.append("services = ?")
        values.append(json.dumps(services))
    elif "services" in body and isinstance(body.get("services"), list):
        services = [_normalize_service(s, i) for i, s in enumerate(body["services"])]
        updates.append("services = ?")
        values.append(json.dumps(services))

    if data.gallery is not None:
        updates.append("gallery = ?")
        values.append(json.dumps(data.gallery[:MAX_GALLERY]))

    pref_raw = None
    if hasattr(data, "preferred_locations") and data.preferred_locations is not None:
        pref_raw = data.preferred_locations
    elif getattr(data, "preferredLocations", None) is not None:
        pref_raw = data.preferredLocations
    elif "preferred_locations" in body:
        pref_raw = body.get("preferred_locations")
    elif "preferredLocations" in body:
        pref_raw = body.get("preferredLocations")

    if pref_raw is not None:
        preferred = _norm_preferred_locations(pref_raw)
        updates.append("preferred_locations = ?")
        values.append(json.dumps(preferred))

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
    type: str = Query("avatar", description="avatar | gallery"),
    index: int = Query(0, ge=0, le=3, description="Gallery slot 0-3 when type=gallery"),
):
    photo_type = (type or "avatar").lower().strip()
    if photo_type not in ("avatar", "gallery"):
        raise HTTPException(status_code=400, detail="type must be avatar or gallery")

    body, content_type = await _read_image_bytes(request)
    user_id = current_user["id"]
    ext = _ext_from_content_type(content_type)
    images = request.scope["env"].IMAGES
    db = request.scope["env"].DB

    if photo_type == "avatar":
        key = f"profiles/{user_id}/avatar.{ext}"
        await images.put(key, body, httpMetadata={"contentType": content_type})
        image_url = f"{R2_PUBLIC_URL}/{key}"

        await db.prepare(
            "UPDATE users SET image = ? WHERE id = ?"
        ).bind(image_url, user_id).run()

        return {
            "image": image_url,
            "url": image_url,
            "type": "avatar",
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

    if not isinstance(gallery, list):
        gallery = []

    while len(gallery) < MAX_GALLERY:
        gallery.append("")

    used_index = min(int(index), MAX_GALLERY - 1)
    gallery[used_index] = image_url
    gallery = [g for g in gallery if g][:MAX_GALLERY]

    await db.prepare(
        "UPDATE users SET gallery = ? WHERE id = ?"
    ).bind(json.dumps(gallery), user_id).run()

    return {
        "url": image_url,
        "image": image_url,
        "gallery": gallery,
        "index": used_index,
        "type": "gallery",
        "message": "Gallery image uploaded successfully",
    }