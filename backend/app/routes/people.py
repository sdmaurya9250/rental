from fastapi import APIRouter, Request, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import math

router = APIRouter()

RADIUS_STEPS = [5.0, 10.0, 20.0]
MIN_RESULTS = 5


class FeedRequest(BaseModel):
    lat: float
    lng: float
    city: Optional[str] = None
    area: Optional[str] = None
    user_id: Optional[str] = None
    radius_km: Optional[float] = None
    expand: Optional[bool] = True


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


def _norm_preferred_locations(raw) -> list:
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raw = [raw] if str(raw).strip() else []
    if not isinstance(raw, list):
        return []

    out = []
    for item in raw:
        if isinstance(item, dict):
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

def _normalize_services(raw_services, fallback_price=1500):
    services = _parse_json_list(raw_services, [])
    result = []

    for index, item in enumerate(services):
        if isinstance(item, dict):
            name = item.get("name") or item.get("title") or f"Service {index + 1}"
            price = int(item.get("price") or fallback_price)
            duration = item.get("duration") or "1 hr"
            sid = item.get("id") or f"service-{index + 1}"
            preferred = _norm_preferred_locations(
                item.get("preferred_locations") or item.get("preferredLocations")
            )
            locations = _norm_location_names(
                item.get("locations") or item.get("location_names"),
                preferred,
            )

            interests_raw = item.get("interests") or item.get("interest") or []
            if isinstance(interests_raw, str):
                interests = [x.strip() for x in interests_raw.split(",") if x.strip()]
            elif isinstance(interests_raw, list):
                interests = [str(x).strip() for x in interests_raw if str(x).strip()]
            else:
                interests = []

            available_time = item.get("available_time") or item.get("availableTime") or {}
            if isinstance(available_time, str):
                try:
                    available_time = json.loads(available_time)
                except Exception:
                    available_time = {}
            if not isinstance(available_time, dict):
                available_time = {}

            time_slots = item.get("time_slots") or item.get("timeSlots") or []
            if isinstance(time_slots, str):
                try:
                    time_slots = json.loads(time_slots)
                except Exception:
                    time_slots = []
            if not isinstance(time_slots, list):
                time_slots = []
        else:
            name = str(item)
            price = int(fallback_price)
            duration = "1 hr"
            sid = f"service-{index + 1}"
            preferred = []
            locations = []
            interests = []
            available_time = {}
            time_slots = []

        result.append({
            "id": sid,
            "name": name,
            "title": name,
            "price": price,
            "duration": duration,
            "locations": locations,
            "preferred_locations": preferred,
            "interests": interests,
            "available_time": available_time,
            "availableTime": available_time,
            "time_slots": time_slots,
            "timeSlots": time_slots,
        })

    if not result:
        empty = {
            "locations": [],
            "preferred_locations": [],
            "interests": [],
            "available_time": {},
            "availableTime": {},
            "time_slots": [],
            "timeSlots": [],
        }
        result = [
            {
                "id": "coffee",
                "name": "Coffee Partner",
                "title": "Coffee Partner",
                "price": fallback_price,
                "duration": "1 hr",
                **empty,
            },
            {
                "id": "cafe",
                "name": "Cafe & Food Partner",
                "title": "Cafe & Food Partner",
                "price": int(fallback_price * 1.5),
                "duration": "2 hrs",
                **empty,
            },
            {
                "id": "event",
                "name": "Event Partner",
                "title": "Event Partner",
                "price": int(fallback_price * 2.5),
                "duration": "3 hrs",
                **empty,
            },
            {
                "id": "travel",
                "name": "Travel Buddy",
                "title": "Travel Buddy",
                "price": int(fallback_price * 4),
                "duration": "Full Day",
                **empty,
            },
        ]

    return result


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    R = 6371.0
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlmb = math.radians(float(lng2) - float(lng1))
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


async def _kyc_verified_map(db, user_ids: list) -> dict:
    """user_id -> True if KYC is verified."""
    out = {uid: False for uid in user_ids}
    if not user_ids:
        return out
    placeholders = ",".join("?" * len(user_ids))
    try:
        rows = await db.prepare(
            f"""
            SELECT user_id, status FROM kyc
            WHERE user_id IN ({placeholders})
              AND LOWER(COALESCE(status, '')) = 'verified'
            """
        ).bind(*user_ids).all()
        items = rows.results if hasattr(rows, "results") else rows
        for row in items:
            r = dict(row)
            uid = r.get("user_id")
            if uid:
                out[uid] = True
    except Exception:
        # kyc table missing or query error — leave all False
        pass
    return out


def _row_to_person(
    r: dict,
    detailed: bool = False,
    distance_km: float | None = None,
    kyc_verified: bool = False,
):
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

    preferred_locations = _norm_preferred_locations(r.get("preferred_locations"))
    if not preferred_locations:
        seen = set()
        for s in services:
            for loc in s.get("preferred_locations") or []:
                key = (loc.get("name") or "").lower()
                if key and key not in seen:
                    seen.add(key)
                    preferred_locations.append(loc)

    verified = bool(kyc_verified)

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
        "preferred_locations": preferred_locations,
        "preferredLocations": preferred_locations,
        "rating_avg": float(r.get("rating_avg") or 0),
        "rating_count": int(r.get("rating_count") or 0),
        # KYC badge for PeopleGrid
        "verified": verified,
        "kyc_verified": verified,
        "isVerified": verified,
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
    people = sorted(people, key=lambda p: p.get("distance_km", 9999))

    if radius_km is not None and not expand:
        filtered = _filter_by_radius(people, radius_km)
        return filtered, float(radius_km)

    steps = list(RADIUS_STEPS)
    if radius_km is not None:
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

    return people, used


@router.post("/people")
async def people_feed(data: FeedRequest, request: Request):
    db = request.scope["env"].DB

    exclude_id = (data.user_id or "").strip() or None
    expand = True if data.expand is None else bool(data.expand)

    sql = """
        SELECT id, full_name, city, gender, price, bio, image, is_available,
               services, interests, want_to, languages, available_time, gallery,
               lat, lng, rating_avg, rating_count, preferred_locations
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

    if data.city and data.city.strip():
        sql += " AND LOWER(COALESCE(city, '')) LIKE ?"
        params.append(f"%{data.city.strip().lower()}%")

    sql += " LIMIT 400"

    rows = await db.prepare(sql).bind(*params).all()
    results = rows.results if hasattr(rows, "results") else rows

    raw = []
    for row in results:
        r = dict(row)
        try:
            ulat = float(r["lat"])
            ulng = float(r["lng"])
        except (TypeError, ValueError, KeyError):
            continue
        dist = _haversine_km(data.lat, data.lng, ulat, ulng)
        raw.append((r, dist))

    verified_map = await _kyc_verified_map(db, [r["id"] for r, _ in raw])

    people = [
        _row_to_person(
            r,
            detailed=False,
            distance_km=dist,
            kyc_verified=verified_map.get(r["id"], False),
        )
        for r, dist in raw
    ]

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

    db = request.scope["env"].DB

    sql = """
        SELECT id, full_name, city, gender, price, bio, image, is_available,
               services, interests, want_to, languages, available_time, gallery,
               lat, lng, rating_avg, rating_count, preferred_locations
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
    raw_rows = [dict(row) for row in results]
    verified_map = await _kyc_verified_map(db, [r["id"] for r in raw_rows])

    people = [
        _row_to_person(
            r,
            detailed=False,
            kyc_verified=verified_map.get(r["id"], False),
        )
        for r in raw_rows
    ]

    return {"count": len(people), "people": people}


@router.get("/people/{user_id}")
async def get_person(user_id: str, request: Request):
    db = request.scope["env"].DB

    row = await db.prepare(
        """
        SELECT id, full_name, email, mobile, city, gender, price, bio, image,
               is_available, available_time, languages, interests, services,
               want_to, gallery, lat, lng, rating_avg, rating_count,
               preferred_locations
        FROM users WHERE id = ?
        """
    ).bind(user_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Person not found")

    verified_map = await _kyc_verified_map(db, [user_id])
    return _row_to_person(
        dict(row),
        detailed=True,
        kyc_verified=verified_map.get(user_id, False),
    )