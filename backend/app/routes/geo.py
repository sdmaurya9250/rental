from fastapi import APIRouter, Request, HTTPException, Query
import json

router = APIRouter()


def _get_mapbox_token(request: Request) -> str:
    env = request.scope.get("env")
    token = getattr(env, "MAPBOX_TOKEN", None) if env else None
    if not token:
        raise HTTPException(status_code=500, detail="MAPBOX_TOKEN not configured")
    return token


@router.get("/geo/geocode")
async def geocode(
    request: Request,
    q: str = Query(..., min_length=2, description="Place or city name"),
    limit: int = Query(5, ge=1, le=10),
):
    """Forward geocode: text → list of places with lat/lng (Mapbox)."""
    token = _get_mapbox_token(request)
    url = (
        f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
        f"{q}.json?access_token={token}&limit={limit}&types=place,locality,neighborhood"
    )

    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Mapbox error: {str(e)}")

    features = []
    for f in data.get("features") or []:
        center = f.get("center") or []
        if len(center) < 2:
            continue
        ctx = f.get("context") or []
        city = f.get("text") or ""
        region = ""
        country = ""
        for c in ctx:
            cid = c.get("id") or ""
            if cid.startswith("region"):
                region = c.get("text") or ""
            if cid.startswith("country"):
                country = c.get("text") or ""
        features.append({
            "name": f.get("place_name") or city,
            "city": city,
            "region": region,
            "country": country,
            "lng": center[0],
            "lat": center[1],
        })

    return {"query": q, "results": features}


@router.get("/geo/reverse")
async def reverse_geocode(
    request: Request,
    lat: float = Query(...),
    lng: float = Query(...),
):
    """Reverse geocode: lat/lng → city name (Mapbox)."""
    token = _get_mapbox_token(request)
    url = (
        f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
        f"{lng},{lat}.json?access_token={token}&types=place,locality"
    )

    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Mapbox error: {str(e)}")

    features = data.get("features") or []
    if not features:
        return {"city": None, "place_name": None, "lat": lat, "lng": lng}

    f = features[0]
    city = f.get("text") or ""
    place_name = f.get("place_name") or city

    return {
        "city": city,
        "place_name": place_name,
        "lat": lat,
        "lng": lng,
    }