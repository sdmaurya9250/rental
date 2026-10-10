# # from fastapi import APIRouter, Request, Query, HTTPException
# # from typing import Optional
# # import json
# # from fastapi import Query
# # import math
# #
# # router = APIRouter()
# #
# #
# # def _parse_json_list(value, default=None):
# #     if default is None:
# #         default = []
# #     if value is None:
# #         return default
# #     if isinstance(value, list):
# #         return value
# #     try:
# #         parsed = json.loads(value)
# #         if isinstance(parsed, list):
# #             return parsed
# #         if isinstance(parsed, str):
# #             return [x.strip() for x in parsed.split(",") if x.strip()]
# #     except Exception:
# #         if isinstance(value, str) and value.strip():
# #             return [x.strip() for x in value.split(",") if x.strip()]
# #     return default
# #
# #
# # def _normalize_services(raw_services, fallback_price=1500):
# #     services = _parse_json_list(raw_services, [])
# #     result = []
# #
# #     for index, item in enumerate(services):
# #         if isinstance(item, dict):
# #             name = item.get("name") or item.get("title") or f"Service {index + 1}"
# #             price = int(item.get("price") or fallback_price)
# #             duration = item.get("duration") or "1 hr"
# #             sid = item.get("id") or f"service-{index + 1}"
# #         else:
# #             name = str(item)
# #             price = int(fallback_price)
# #             duration = "1 hr"
# #             sid = f"service-{index + 1}"
# #
# #         result.append({
# #             "id": sid,
# #             "name": name,
# #             "title": name,
# #             "price": price,
# #             "duration": duration,
# #         })
# #
# #     # Default services if user has none
# #     if not result:
# #         result = [
# #             {"id": "coffee", "name": "Coffee Partner", "title": "Coffee Partner", "price": fallback_price, "duration": "1 hr"},
# #             {"id": "cafe", "name": "Cafe & Food Partner", "title": "Cafe & Food Partner", "price": int(fallback_price * 1.5), "duration": "2 hrs"},
# #             {"id": "event", "name": "Event Partner", "title": "Event Partner", "price": int(fallback_price * 2.5), "duration": "3 hrs"},
# #             {"id": "travel", "name": "Travel Buddy", "title": "Travel Buddy", "price": int(fallback_price * 4), "duration": "Full Day"},
# #         ]
# #
# #     return result
# #
# #
# # def _row_to_person(r: dict, detailed: bool = False):
# #     price = int(r.get("price") or 1500)
# #     services = _normalize_services(r.get("services"), price)
# #
# #     tags = [s["name"] for s in services]
# #     interests = _parse_json_list(r.get("interests"), tags)
# #     languages = _parse_json_list(r.get("languages"), [])
# #
# #     gallery = _parse_json_list(r.get("gallery"), [])
# #     main_image = r.get("image") or ""
# #     images = []
# #     if main_image:
# #         images.append(main_image)
# #     for g in gallery:
# #         if g and g not in images:
# #             images.append(g)
# #     if not images:
# #         images = ["https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=600&auto=format&fit=crop"]
# #
# #     person = {
# #         "id": r["id"],
# #         "name": r.get("full_name") or "User",
# #         "age": None,
# #         "location": r.get("city") or "",
# #         "isOnline": bool(r.get("is_available", 0)),
# #         "image": images[0],
# #         "images": images,
# #         "bio": r.get("bio") or "",
# #         "gender": r.get("gender") or "",
# #         "want_to": r.get("want_to") or "",
# #         "rate": price,
# #         "price": f"₹{price:,}/hr",
# #         "priceValue": price,
# #         "tags": tags[:6],
# #         "interests": interests[:8] if interests else tags[:6],
# #         "languages": languages,
# #         "availableTime": r.get("available_time") or "",
# #         "availability": r.get("available_time") or "",
# #         "services": services,
# #     }
# #
# #     if detailed:
# #         person["email"] = r.get("email")
# #         person["phone"] = r.get("mobile")
# #
# #     return person
# #
# #
# # @router.get("/people")
# # async def browse_people(
# #     request: Request,
# #     city: Optional[str] = Query(None),
# #     sort: Optional[str] = Query("popular"),
# #     limit: int = Query(20, ge=1, le=50),
# # ):
# #     db = request.scope["env"].DB
# #
# #     sql = """
# #         SELECT id, full_name, city, gender, price, bio, image, is_available,
# #                services, interests, want_to, languages, available_time, gallery
# #         FROM users
# #         WHERE want_to IN ('Become a RentPeople', 'Both')
# #     """
# #     params = []
# #
# #     if city:
# #         sql += " AND LOWER(city) = LOWER(?)"
# #         params.append(city)
# #
# #     if sort == "price_low":
# #         sql += " ORDER BY COALESCE(price, 999999) ASC"
# #     elif sort == "price_high":
# #         sql += " ORDER BY COALESCE(price, 0) DESC"
# #     else:
# #         sql += " ORDER BY is_available DESC, COALESCE(price, 999999) ASC"
# #
# #     sql += " LIMIT ?"
# #     params.append(limit)
# #
# #     rows = await db.prepare(sql).bind(*params).all()
# #     results = rows.results if hasattr(rows, "results") else rows
# #
# #     people = [_row_to_person(dict(row), detailed=False) for row in results]
# #
# #     return {"count": len(people), "people": people}
# #
# #
# # @router.get("/people/{user_id}")
# # async def get_person(user_id: str, request: Request):
# #     db = request.scope["env"].DB
# #
# #     row = await db.prepare(
# #         """
# #         SELECT id, full_name, email, mobile, city, gender, price, bio, image,
# #                is_available, available_time, languages, interests, services,
# #                want_to, gallery
# #         FROM users WHERE id = ?
# #         """
# #     ).bind(user_id).first()
# #
# #     if not row:
# #         raise HTTPException(status_code=404, detail="Person not found")
# #
# #     return _row_to_person(dict(row), detailed=True)
# #
# #
# # def _haversine_km(lat1, lng1, lat2, lng2) -> float:
# #     R = 6371.0
# #     p1, p2 = math.radians(lat1), math.radians(lat2)
# #     dphi = math.radians(lat2 - lat1)
# #     dlmb = math.radians(lng2 - lng1)
# #     a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
# #     return 2 * R * math.asin(math.sqrt(a))
# #
# #
# # @router.get("/people")
# # async def list_people(
# #     request: Request,
# #     city: str | None = None,
# #     sort: str | None = None,
# #     limit: int = Query(50, ge=1, le=100),
# #     lat: float | None = Query(None),
# #     lng: float | None = Query(None),
# #     radius_km: float = Query(50, ge=1, le=500),
# # ):
# #     db = request.scope["env"].DB
# #
# #     # Base query — only users with location when near-me is used
# #     sql = """
# #         SELECT id, full_name, city, gender, price, bio, image, is_available,
# #                services, interests, want_to, mobile, email, lat, lng
# #         FROM users
# #         WHERE 1=1
# #     """
# #     params = []
# #
# #     if city:
# #         sql += " AND LOWER(city) LIKE ?"
# #         params.append(f"%{city.lower()}%")
# #
# #     if lat is not None and lng is not None:
# #         sql += " AND lat IS NOT NULL AND lng IS NOT NULL"
# #
# #     sql += " LIMIT ?"
# #     params.append(limit * 3 if (lat is not None and lng is not None) else limit)
# #
# #     rows = await db.prepare(sql).bind(*params).all()
# #     items = rows.results if hasattr(rows, "results") else rows
# #
# #     people = []
# #     for row in items:
# #         r = dict(row)
# #         person = _row_to_person(r, detailed=False)  # your existing helper
# #
# #         if lat is not None and lng is not None:
# #             ulat, ulng = r.get("lat"), r.get("lng")
# #             if ulat is None or ulng is None:
# #                 continue
# #             dist = _haversine_km(lat, lng, float(ulat), float(ulng))
# #             if dist > radius_km:
# #                 continue
# #             person["distance_km"] = round(dist, 1)
# #
# #         people.append(person)
# #
# #     if lat is not None and lng is not None:
# #         people.sort(key=lambda p: p.get("distance_km", 9999))
# #     elif sort == "price_low":
# #         people.sort(key=lambda p: p.get("priceValue") or p.get("rate") or 999999)
# #     elif sort == "price_high":
# #         people.sort(key=lambda p: -(p.get("priceValue") or p.get("rate") or 0))
# #
# #     return people[:limit]
#
#
# from fastapi import APIRouter, Request, Query, HTTPException
# from pydantic import BaseModel
# from typing import Optional
# import json
# import math
#
# router = APIRouter()
#
#
# class FeedRequest(BaseModel):
#     lat: float
#     lng: float
#     city: Optional[str] = None
#     user_id: Optional[str] = None
#     radius_km: Optional[float] = None  # optional — omit = no hard cutoff
#
#
# def _parse_json_list(value, default=None):
#     if default is None:
#         default = []
#     if value is None:
#         return default
#     if isinstance(value, list):
#         return value
#     try:
#         parsed = json.loads(value)
#         if isinstance(parsed, list):
#             return parsed
#         if isinstance(parsed, str):
#             return [x.strip() for x in parsed.split(",") if x.strip()]
#     except Exception:
#         if isinstance(value, str) and value.strip():
#             return [x.strip() for x in value.split(",") if x.strip()]
#     return default
#
#
# def _normalize_services(raw_services, fallback_price=1500):
#     services = _parse_json_list(raw_services, [])
#     result = []
#
#     for index, item in enumerate(services):
#         if isinstance(item, dict):
#             name = item.get("name") or item.get("title") or f"Service {index + 1}"
#             price = int(item.get("price") or fallback_price)
#             duration = item.get("duration") or "1 hr"
#             sid = item.get("id") or f"service-{index + 1}"
#         else:
#             name = str(item)
#             price = int(fallback_price)
#             duration = "1 hr"
#             sid = f"service-{index + 1}"
#
#         result.append({
#             "id": sid,
#             "name": name,
#             "title": name,
#             "price": price,
#             "duration": duration,
#         })
#
#     if not result:
#         result = [
#             {"id": "coffee", "name": "Coffee Partner", "title": "Coffee Partner", "price": fallback_price, "duration": "1 hr"},
#             {"id": "cafe", "name": "Cafe & Food Partner", "title": "Cafe & Food Partner", "price": int(fallback_price * 1.5), "duration": "2 hrs"},
#             {"id": "event", "name": "Event Partner", "title": "Event Partner", "price": int(fallback_price * 2.5), "duration": "3 hrs"},
#             {"id": "travel", "name": "Travel Buddy", "title": "Travel Buddy", "price": int(fallback_price * 4), "duration": "Full Day"},
#         ]
#
#     return result
#
#
# def _haversine_km(lat1, lng1, lat2, lng2) -> float:
#     R = 6371.0
#     p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
#     dphi = math.radians(float(lat2) - float(lat1))
#     dlmb = math.radians(float(lng2) - float(lng1))
#     a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
#     return 2 * R * math.asin(math.sqrt(a))
#
#
# def _row_to_person(r: dict, detailed: bool = False, distance_km: float | None = None):
#     price = int(r.get("price") or 1500)
#     services = _normalize_services(r.get("services"), price)
#
#     tags = [s["name"] for s in services]
#     interests = _parse_json_list(r.get("interests"), tags)
#     languages = _parse_json_list(r.get("languages"), [])
#
#     gallery = _parse_json_list(r.get("gallery"), [])
#     main_image = r.get("image") or ""
#     images = []
#     if main_image:
#         images.append(main_image)
#     for g in gallery:
#         if g and g not in images:
#             images.append(g)
#     if not images:
#         images = ["https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=600&auto=format&fit=crop"]
#
#     person = {
#         "id": r["id"],
#         "name": r.get("full_name") or "User",
#         "age": None,
#         "location": r.get("city") or "",
#         "city": r.get("city") or "",
#         "lat": r.get("lat"),
#         "lng": r.get("lng"),
#         "isOnline": bool(r.get("is_available", 0)),
#         "image": images[0],
#         "images": images,
#         "bio": r.get("bio") or "",
#         "gender": r.get("gender") or "",
#         "want_to": r.get("want_to") or "",
#         "rate": price,
#         "price": f"₹{price:,}/hr",
#         "priceValue": price,
#         "tags": tags[:6],
#         "interests": interests[:8] if interests else tags[:6],
#         "languages": languages,
#         "availableTime": r.get("available_time") or "",
#         "availability": r.get("available_time") or "",
#         "services": services,
#     }
#
#     if distance_km is not None:
#         person["distance_km"] = round(float(distance_km), 1)
#
#     if detailed:
#         person["email"] = r.get("email")
#         person["phone"] = r.get("mobile")
#
#     return person
#
#
# # ─────────────────────────────────────────────
# # POST /api/people
# # Frontend: { user_id, lat, lng, city }
# # Backend: sort by distance → feed for home screen
# # ─────────────────────────────────────────────
# @router.post("/people")
# async def people_feed(data: FeedRequest, request: Request):
#     db = request.scope["env"].DB
#
#     exclude_id = (data.user_id or "").strip() or None
#
#     sql = """
#         SELECT id, full_name, city, gender, price, bio, image, is_available,
#                services, interests, want_to, languages, available_time, gallery,
#                lat, lng
#         FROM users
#         WHERE want_to IN ('companion', 'Both')
#           AND lat IS NOT NULL
#           AND lng IS NOT NULL
#     """
#     params = []
#
#     if exclude_id:
#         sql += " AND id != ?"
#         params.append(exclude_id)
#
#     if data.city and data.city.strip():
#         sql += " AND LOWER(city) LIKE ?"
#         params.append(f"%{data.city.strip().lower()}%")
#
#     sql += " LIMIT 300"
#
#     rows = await db.prepare(sql).bind(*params).all()
#     results = rows.results if hasattr(rows, "results") else rows
#
#     people = []
#     for row in results:
#         r = dict(row)
#         try:
#             ulat = float(r["lat"])
#             ulng = float(r["lng"])
#         except (TypeError, ValueError, KeyError):
#             continue
#
#         dist = _haversine_km(data.lat, data.lng, ulat, ulng)
#
#         # radius optional — only filter if client sends it
#         if data.radius_km is not None and dist > float(data.radius_km):
#             continue
#
#         people.append(_row_to_person(r, detailed=False, distance_km=dist))
#
#     people.sort(key=lambda p: p.get("distance_km", 9999))
#
#     return {
#         "count": len(people),
#         "center": {
#             "user_id": exclude_id,
#             "lat": data.lat,
#             "lng": data.lng,
#             "city": data.city,
#         },
#         "people": people,
#     }
#
#
# # ─────────────────────────────────────────────
# # GET /api/people
# # ?city=  or  ?lat=&lng=&city=&user_id=&radius_km=
# # ─────────────────────────────────────────────
# @router.get("/people")
# async def browse_people(
#     request: Request,
#     city: Optional[str] = Query(None),
#     sort: Optional[str] = Query("popular"),
#     limit: int = Query(20, ge=1, le=50),
#     lat: Optional[float] = Query(None),
#     lng: Optional[float] = Query(None),
#     radius_km: Optional[float] = Query(None),
#     user_id: Optional[str] = Query(None),
# ):
#     # Near-me via GET → same logic as POST
#     if lat is not None and lng is not None:
#         data = FeedRequest(
#             lat=lat,
#             lng=lng,
#             city=city,
#             user_id=user_id,
#             radius_km=radius_km,
#         )
#         result = await people_feed(data, request)
#         result["people"] = result["people"][:limit]
#         result["count"] = len(result["people"])
#         return result
#
#     # City / all browse (no distance)
#     db = request.scope["env"].DB
#
#     sql = """
#         SELECT id, full_name, city, gender, price, bio, image, is_available,
#                services, interests, want_to, languages, available_time, gallery,
#                lat, lng
#         FROM users
#         WHERE want_to IN ('companion', 'Both')
#     """
#     params = []
#
#     if city:
#         sql += " AND LOWER(city) LIKE ?"
#         params.append(f"%{city.lower()}%")
#
#     if user_id:
#         sql += " AND id != ?"
#         params.append(user_id)
#
#     if sort == "price_low":
#         sql += " ORDER BY COALESCE(price, 999999) ASC"
#     elif sort == "price_high":
#         sql += " ORDER BY COALESCE(price, 0) DESC"
#     else:
#         sql += " ORDER BY is_available DESC, COALESCE(price, 999999) ASC"
#
#     sql += " LIMIT ?"
#     params.append(limit)
#
#     rows = await db.prepare(sql).bind(*params).all()
#     results = rows.results if hasattr(rows, "results") else rows
#     people = [_row_to_person(dict(row), detailed=False) for row in results]
#
#     return {"count": len(people), "people": people}
#
#
# # ─────────────────────────────────────────────
# # GET /api/people/{user_id}
# # ─────────────────────────────────────────────
# @router.get("/people/{user_id}")
# async def get_person(user_id: str, request: Request):
#     db = request.scope["env"].DB
#
#     row = await db.prepare(
#         """
#         SELECT id, full_name, email, mobile, city, gender, price, bio, image,
#                is_available, available_time, languages, interests, services,
#                want_to, gallery, lat, lng
#         FROM users WHERE id = ?
#         """
#     ).bind(user_id).first()
#
#     if not row:
#         raise HTTPException(status_code=404, detail="Person not found")
#
#     return _row_to_person(dict(row), detailed=True)



from fastapi import APIRouter, Request, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import math

router = APIRouter()

# Progressive radii (km) — OLX-style
RADIUS_STEPS = [5.0, 10.0, 20.0]
MIN_RESULTS = 5  # expand radius if fewer than this


class FeedRequest(BaseModel):
    lat: float
    lng: float
    city: Optional[str] = None
    area: Optional[str] = None  # e.g. "Koregaon Park" (display / soft filter)
    user_id: Optional[str] = None
    radius_km: Optional[float] = None  # 5 | 10 | 20 | omit
    expand: Optional[bool] = True  # if True, grow 5→10→20 when few results


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

    if not result:
        result = [
            {"id": "coffee", "name": "Coffee Partner", "title": "Coffee Partner", "price": fallback_price, "duration": "1 hr"},
            {"id": "cafe", "name": "Cafe & Food Partner", "title": "Cafe & Food Partner", "price": int(fallback_price * 1.5), "duration": "2 hrs"},
            {"id": "event", "name": "Event Partner", "title": "Event Partner", "price": int(fallback_price * 2.5), "duration": "3 hrs"},
            {"id": "travel", "name": "Travel Buddy", "title": "Travel Buddy", "price": int(fallback_price * 4), "duration": "Full Day"},
        ]

    return result


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    R = 6371.0
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlmb = math.radians(float(lng2) - float(lng1))
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _row_to_person(r: dict, detailed: bool = False, distance_km: float | None = None):
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
        images = [
            "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=600&auto=format&fit=crop"
        ]

    person = {
        "id": r["id"],
        "name": r.get("full_name") or "User",
        "age": None,
        "location": r.get("city") or "",
        "city": r.get("city") or "",
        "lat": r.get("lat"),
        "lng": r.get("lng"),
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
        "rating_avg": float(r.get("rating_avg") or 0),
        "rating_count": int(r.get("rating_count") or 0),
    }

    if distance_km is not None:
        person["distance_km"] = round(float(distance_km), 1)

    if detailed:
        person["email"] = r.get("email")
        person["phone"] = r.get("mobile")

    return person


def _filter_by_radius(people: list, radius_km: float) -> list:
    return [p for p in people if (p.get("distance_km") or 9999) <= float(radius_km)]


def _apply_radius(people: list, radius_km: Optional[float], expand: bool):
    """
    OLX-style:
      - expand=True  → try 5 → 10 → 20 until MIN_RESULTS (or all)
      - expand=False → strict radius only
      - radius_km=None + expand → same progressive from 5
    """
    people = sorted(people, key=lambda p: p.get("distance_km", 9999))

    if radius_km is not None and not expand:
        filtered = _filter_by_radius(people, radius_km)
        return filtered, float(radius_km)

    # Progressive steps
    steps = list(RADIUS_STEPS)
    if radius_km is not None:
        # start from requested, then larger only
        steps = [r for r in steps if r >= float(radius_km)]
        if not steps:
            steps = [float(radius_km)]

    used = None
    chosen = []
    for r in steps:
        chosen = _filter_by_radius(people, r)
        used = float(r)
        if len(chosen) >= MIN_RESULTS:
            return chosen, used

    # Still few → return all with distance (no hard cut)
    return people, used


# ─────────────────────────────────────────────
# POST /api/people  — main near-me feed
# Body: { lat, lng, city?, area?, user_id?, radius_km?, expand? }
# ─────────────────────────────────────────────
@router.post("/people")
async def people_feed(data: FeedRequest, request: Request):
    db = request.scope["env"].DB

    exclude_id = (data.user_id or "").strip() or None
    expand = True if data.expand is None else bool(data.expand)

    # Companions only (new + legacy role strings)
    sql = """
        SELECT id, full_name, city, gender, price, bio, image, is_available,
               services, interests, want_to, languages, available_time, gallery,
               lat, lng, rating_avg, rating_count
        FROM users
        WHERE lat IS NOT NULL
          AND lng IS NOT NULL
          AND (
            LOWER(COALESCE(want_to, '')) IN ('companion', 'both')
            OR LOWER(COALESCE(want_to, '')) LIKE '%become%'
            OR LOWER(COALESCE(want_to, '')) = 'both'
          )
    """
    params = []

    if exclude_id:
        sql += " AND id != ?"
        params.append(exclude_id)

    # Soft city filter (e.g. "Pune") — does not block other areas if empty
    if data.city and data.city.strip():
        # Prefer city match but OLX often still shows nearby across city text;
        # keep as soft filter on city column
        sql += " AND LOWER(COALESCE(city, '')) LIKE ?"
        params.append(f"%{data.city.strip().lower()}%")

    sql += " LIMIT 400"

    rows = await db.prepare(sql).bind(*params).all()
    results = rows.results if hasattr(rows, "results") else rows

    people = []
    for row in results:
        r = dict(row)
        try:
            ulat = float(r["lat"])
            ulng = float(r["lng"])
        except (TypeError, ValueError, KeyError):
            continue

        dist = _haversine_km(data.lat, data.lng, ulat, ulng)
        people.append(_row_to_person(r, detailed=False, distance_km=dist))

    # Optional area soft boost: names containing area stay sorted by distance still
    # (distance order is primary; no hard filter on area string)

    filtered, used_radius = _apply_radius(people, data.radius_km, expand)

    return {
        "count": len(filtered),
        "radius_km": data.radius_km,
        "radius_used_km": used_radius,
        "expand": expand,
        "center": {
            "user_id": exclude_id,
            "lat": data.lat,
            "lng": data.lng,
            "city": data.city,
            "area": data.area,
        },
        "people": filtered,
    }


# ─────────────────────────────────────────────
# GET /api/people
# Near-me: ?lat=&lng=&city=&area=&radius_km=&expand=&user_id=
# Browse:  ?city=&sort=&limit=
# ─────────────────────────────────────────────
@router.get("/people")
async def browse_people(
    request: Request,
    city: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
    sort: Optional[str] = Query("popular"),
    limit: int = Query(50, ge=1, le=100),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    radius_km: Optional[float] = Query(None),
    expand: Optional[bool] = Query(True),
    user_id: Optional[str] = Query(None),
):
    if lat is not None and lng is not None:
        data = FeedRequest(
            lat=lat,
            lng=lng,
            city=city,
            area=area,
            user_id=user_id,
            radius_km=radius_km,
            expand=expand,
        )
        result = await people_feed(data, request)
        result["people"] = result["people"][:limit]
        result["count"] = len(result["people"])
        return result

    # No coords → city / all browse
    db = request.scope["env"].DB

    sql = """
        SELECT id, full_name, city, gender, price, bio, image, is_available,
               services, interests, want_to, languages, available_time, gallery,
               lat, lng, rating_avg, rating_count
        FROM users
        WHERE (
            LOWER(COALESCE(want_to, '')) IN ('companion', 'both')
            OR LOWER(COALESCE(want_to, '')) LIKE '%become%'
        )
    """
    params = []

    if city:
        sql += " AND LOWER(COALESCE(city, '')) LIKE ?"
        params.append(f"%{city.lower()}%")

    if user_id:
        sql += " AND id != ?"
        params.append(user_id)

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


# ─────────────────────────────────────────────
# GET /api/people/{user_id}
# ─────────────────────────────────────────────
@router.get("/people/{user_id}")
async def get_person(user_id: str, request: Request):
    db = request.scope["env"].DB

    row = await db.prepare(
        """
        SELECT id, full_name, email, mobile, city, gender, price, bio, image,
               is_available, available_time, languages, interests, services,
               want_to, gallery, lat, lng, rating_avg, rating_count
        FROM users WHERE id = ?
        """
    ).bind(user_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Person not found")

    return _row_to_person(dict(row), detailed=True)