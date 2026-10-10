from fastapi import APIRouter, Request, HTTPException, Query
import json
from urllib.parse import quote

router = APIRouter()


def _get_mapbox_token(request: Request) -> str:
    env = request.scope.get("env")
    token = getattr(env, "MAPBOX_TOKEN", None) if env else None
    if not token:
        raise HTTPException(status_code=500, detail="MAPBOX_TOKEN not configured")
    return str(token)


async def _fetch_json(url: str) -> dict:
    """Outbound HTTP via Workers JS fetch (urllib does not work on CF Python Workers)."""
    try:
        from js import fetch  # Pyodide / Cloudflare Python Workers
        resp = await fetch(url)
        status = int(resp.status)
        text = await resp.text()
        if status < 200 or status >= 300:
            raise HTTPException(status_code=502, detail=f"Mapbox HTTP {status}: {text[:200]}")
        return json.loads(text)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Mapbox fetch failed: {type(e).__name__}: {str(e)}"
        )

#
# @router.get("/geo/geocode")
# async def geocode(
#     request: Request,
#     q: str = Query(..., min_length=2),
#     limit: int = Query(5, ge=1, le=10),
# ):
#     token = _get_mapbox_token(request)
#     encoded = quote(q)
#     url = (
#         f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
#         f"{encoded}.json?access_token={token}&limit={limit}"
#         f"&types=place,locality,neighborhood"
#     )
#     data = await _fetch_json(url)
#
#     features = []
#     for f in data.get("features") or []:
#         center = f.get("center") or []
#         if len(center) < 2:
#             continue
#         city = f.get("text") or ""
#         region, country = "", ""
#         for c in f.get("context") or []:
#             cid = c.get("id") or ""
#             if cid.startswith("region"):
#                 region = c.get("text") or ""
#             if cid.startswith("country"):
#                 country = c.get("text") or ""
#         features.append({
#             "name": f.get("place_name") or city,
#             "city": city,
#             "region": region,
#             "country": country,
#             "lng": center[0],
#             "lat": center[1],
#         })
#
#     return {"query": q, "results": features}

@router.get("/geo/geocode")
async def geocode(
    request: Request,
    q: str = Query(..., min_length=2),
    limit: int = Query(5, ge=1, le=10),
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
):
    token = _get_mapbox_token(request)
    encoded = quote(q)
    proximity = f"&proximity={lng},{lat}" if lat is not None and lng is not None else ""
    url = (
        f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
        f"{encoded}.json?access_token={token}&limit={limit}"
        f"&types=address,place,locality,neighborhood{proximity}"
    )
    data = await _fetch_json(url)

    features = []
    for f in data.get("features") or []:
        center = f.get("center") or []
        if len(center) < 2:
            continue
        city = f.get("text") or ""
        region, country = "", ""
        for c in f.get("context") or []:
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
    token = _get_mapbox_token(request)
    url = (
        f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
        f"{lng},{lat}.json?access_token={token}&types=place,locality"
    )
    data = await _fetch_json(url)

    features = data.get("features") or []
    if not features:
        return {"city": None, "place_name": None, "lat": lat, "lng": lng}

    f = features[0]
    city = f.get("text") or ""
    return {
        "city": city,
        "place_name": f.get("place_name") or city,
        "lat": lat,
        "lng": lng,
    }