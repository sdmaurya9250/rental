# from fastapi import APIRouter, Request, Query
# from typing import Optional
# import json
#
# router = APIRouter()
#
#
# @router.get("/people")
# async def browse_people(
#     request: Request,
#     city: Optional[str] = Query(None, description="Filter by city"),
#     sort: Optional[str] = Query("popular", description="popular | price_low | price_high"),
#     limit: int = Query(20, ge=1, le=50),
# ):
#     db = request.scope["env"].DB
#
#     # Base query: only show people who want to be found / both, and have profile
#     sql = """
#         SELECT
#             id,
#             full_name,
#             city,
#             gender,
#             price,
#             bio,
#             image,
#             is_available,
#             services,
#             interests,
#             want_to
#         FROM users
#         WHERE want_to IN ('Become a RentPeople', 'Both')
#     """
#     params = []
#
#     if city:
#         sql += " AND LOWER(city) = LOWER(?)"
#         params.append(city)
#
#     # Sorting
#     if sort == "price_low":
#         sql += " ORDER BY COALESCE(price, 999999) ASC"
#     elif sort == "price_high":
#         sql += " ORDER BY COALESCE(price, 0) DESC"
#     else:
#         # popular = available first, then by price
#         sql += " ORDER BY is_available DESC, COALESCE(price, 999999) ASC"
#
#     sql += " LIMIT ?"
#     params.append(limit)
#
#     rows = await db.prepare(sql).bind(*params).all()
#
#     people = []
#     for row in rows.results if hasattr(rows, "results") else rows:
#         r = dict(row)
#
#         # Parse services / interests into tags
#         tags = []
#         try:
#             services = json.loads(r.get("services") or "[]")
#             if services and isinstance(services[0], dict):
#                 tags = [s.get("name") for s in services if s.get("name")]
#             else:
#                 tags = [str(s) for s in services]
#         except Exception:
#             tags = []
#
#         if not tags:
#             try:
#                 interests = json.loads(r.get("interests") or "[]")
#                 tags = interests if isinstance(interests, list) else []
#             except Exception:
#                 tags = []
#
#         price = r.get("price") or 1500
#
#         people.append({
#             "id": r["id"],
#             "name": r.get("full_name") or "User",
#             "location": r.get("city") or "",
#             "price": f"₹{price:,}/hr",
#             "priceValue": price,
#             "isOnline": bool(r.get("is_available", 0)),
#             "tags": tags[:4],
#             "image": r.get("image") or "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=600&auto=format&fit=crop",
#             "gender": r.get("gender") or "",
#             "bio": r.get("bio") or "",
#         })
#
#     return {
#         "count": len(people),
#         "people": people
#     }
#
#
# @router.get("/people/{user_id}")
# async def get_person(user_id: str, request: Request):
#     db = request.scope["env"].DB
#
#     row = await db.prepare(
#         """
#         SELECT id, full_name, email, mobile, city, gender, price, bio, image,
#                is_available, available_time, languages, interests, services, want_to
#         FROM users WHERE id = ?
#         """
#     ).bind(user_id).first()
#
#     if not row:
#         from fastapi import HTTPException
#         raise HTTPException(status_code=404, detail="Person not found")
#
#     r = dict(row)
#
#     services = []
#     try:
#         services = json.loads(r.get("services") or "[]")
#     except Exception:
#         services = []
#
#     languages = []
#     try:
#         languages = json.loads(r.get("languages") or "[]")
#         if isinstance(languages, str):
#             languages = [x.strip() for x in languages.split(",") if x.strip()]
#     except Exception:
#         languages = []
#
#     price = r.get("price") or 1500
#
#     return {
#         "id": r["id"],
#         "name": r.get("full_name") or "User",
#         "email": r.get("email"),
#         "phone": r.get("mobile"),
#         "location": r.get("city") or "",
#         "gender": r.get("gender") or "",
#         "price": f"₹{price:,}/hr",
#         "priceValue": price,
#         "isOnline": bool(r.get("is_available", 0)),
#         "bio": r.get("bio") or "",
#         "image": r.get("image") or "",
#         "availableTime": r.get("available_time") or "",
#         "languages": languages,
#         "services": services,
#         "want_to": r.get("want_to") or "",
#     }


from fastapi import APIRouter, Request, Query, HTTPException
from typing import Optional
import json

router = APIRouter()


def _parse_json_list(value, default=None):
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
        if isinstance(parsed, str):
            return [x.strip() for x in parsed.split(",") if x.strip()]
    except Exception:
        if isinstance(value, str) and value.strip():
            return [x.strip() for x in value.split(",") if x.strip()]
    return default


def _normalize_services(raw_services, fallback_price=1500):
    services = _parse_json_list(raw_services, [])
    result = []

    for index, item in enumerate(services):
        if isinstance(item, dict):
            name = item.get("name") or item.get("title") or f"Service {index + 1}"
            price = int(item.get("price") or fallback_price)
            duration = item.get("duration") or "1 hr"
            sid = item.get("id") or f"service-{index + 1}"
        else:
            name = str(item)
            price = int(fallback_price)
            duration = "1 hr"
            sid = f"service-{index + 1}"

        result.append({
            "id": sid,
            "name": name,
            "title": name,
            "price": price,
            "duration": duration,
        })

    # Default services if user has none
    if not result:
        result = [
            {"id": "coffee", "name": "Coffee Partner", "title": "Coffee Partner", "price": fallback_price, "duration": "1 hr"},
            {"id": "cafe", "name": "Cafe & Food Partner", "title": "Cafe & Food Partner", "price": int(fallback_price * 1.5), "duration": "2 hrs"},
            {"id": "event", "name": "Event Partner", "title": "Event Partner", "price": int(fallback_price * 2.5), "duration": "3 hrs"},
            {"id": "travel", "name": "Travel Buddy", "title": "Travel Buddy", "price": int(fallback_price * 4), "duration": "Full Day"},
        ]

    return result


def _row_to_person(r: dict, detailed: bool = False):
    price = int(r.get("price") or 1500)
    services = _normalize_services(r.get("services"), price)

    tags = [s["name"] for s in services]
    interests = _parse_json_list(r.get("interests"), tags)
    languages = _parse_json_list(r.get("languages"), [])

    gallery = _parse_json_list(r.get("gallery"), [])
    main_image = r.get("image") or ""
    images = []
    if main_image:
        images.append(main_image)
    for g in gallery:
        if g and g not in images:
            images.append(g)
    if not images:
        images = ["https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=600&auto=format&fit=crop"]

    person = {
        "id": r["id"],
        "name": r.get("full_name") or "User",
        "age": None,
        "location": r.get("city") or "",
        "isOnline": bool(r.get("is_available", 0)),
        "image": images[0],
        "images": images,
        "bio": r.get("bio") or "",
        "gender": r.get("gender") or "",
        "want_to": r.get("want_to") or "",
        "rate": price,
        "price": f"₹{price:,}/hr",
        "priceValue": price,
        "tags": tags[:6],
        "interests": interests[:8] if interests else tags[:6],
        "languages": languages,
        "availableTime": r.get("available_time") or "",
        "availability": r.get("available_time") or "",
        "services": services,
    }

    if detailed:
        person["email"] = r.get("email")
        person["phone"] = r.get("mobile")

    return person


@router.get("/people")
async def browse_people(
    request: Request,
    city: Optional[str] = Query(None),
    sort: Optional[str] = Query("popular"),
    limit: int = Query(20, ge=1, le=50),
):
    db = request.scope["env"].DB

    sql = """
        SELECT id, full_name, city, gender, price, bio, image, is_available,
               services, interests, want_to, languages, available_time, gallery
        FROM users
        WHERE want_to IN ('Become a RentPeople', 'Both')
    """
    params = []

    if city:
        sql += " AND LOWER(city) = LOWER(?)"
        params.append(city)

    if sort == "price_low":
        sql += " ORDER BY COALESCE(price, 999999) ASC"
    elif sort == "price_high":
        sql += " ORDER BY COALESCE(price, 0) DESC"
    else:
        sql += " ORDER BY is_available DESC, COALESCE(price, 999999) ASC"

    sql += " LIMIT ?"
    params.append(limit)

    rows = await db.prepare(sql).bind(*params).all()
    results = rows.results if hasattr(rows, "results") else rows

    people = [_row_to_person(dict(row), detailed=False) for row in results]

    return {"count": len(people), "people": people}


@router.get("/people/{user_id}")
async def get_person(user_id: str, request: Request):
    db = request.scope["env"].DB

    row = await db.prepare(
        """
        SELECT id, full_name, email, mobile, city, gender, price, bio, image,
               is_available, available_time, languages, interests, services,
               want_to, gallery
        FROM users WHERE id = ?
        """
    ).bind(user_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Person not found")

    return _row_to_person(dict(row), detailed=True)