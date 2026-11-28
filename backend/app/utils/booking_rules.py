"""Pure booking rules: venue approval, service lookup, distance."""
import math
import re
from fastapi import HTTPException
from routes.geo import is_lodging

VENUE_MATCH_METERS = 300

_APPROVED_VENUE_RE = re.compile(
    r"(companion|cafe|coffee|tea|restaurant|food|bakery|dining|mall|shopping|market|store|"
    r"cinema|movie|theat|park|garden|museum|gallery|art|library|bookstore|"
    r"stadium|sport|fitness|gym|temple|beach|lake|viewpoint|attraction|landmark)",
    re.IGNORECASE,
)


def haversine_m(lat1, lng1, lat2, lng2) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lng2 - lng1) / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


def find_service(services: list, service_id, service_name):
    sid = (service_id or "").strip()
    sname = (service_name or "").strip().lower()
    for s in services:
        if isinstance(s, dict) and sid and str(s.get("id") or "") == sid:
            return s
    for s in services:
        if isinstance(s, dict):
            n = str(s.get("name") or s.get("title") or "").strip().lower()
            if sname and n == sname:
                return s
    return None


def validate_venue(data, service) -> None:
    """Raise 400 unless the meeting place is a real approved public place."""
    if data.location_type != "in_person":
        return
    lat, lng = data.location_lat, data.location_lng
    category = (data.location_category or "").strip()

    if lat is None or lng is None:
        raise HTTPException(400, "Pick a meeting place from the list (location is missing).")
    if not (6.0 <= lat <= 37.5 and 68.0 <= lng <= 97.5):
        raise HTTPException(400, "Meeting place is outside the service area.")
    if is_lodging(data.location, category):
        raise HTTPException(400, "Hotels, lodges and homestays cannot be used as a meeting place.")

    for loc in (service or {}).get("preferred_locations") or []:
        try:
            plat, plng = float(loc.get("lat")), float(loc.get("lng"))
        except (TypeError, ValueError):
            continue
        if haversine_m(lat, lng, plat, plng) <= VENUE_MATCH_METERS:
            return

    if _APPROVED_VENUE_RE.search(category):
        return
    raise HTTPException(
        400,
        "This place is not on the approved list. Choose a café, mall, cinema, park or similar public place.",
    )
