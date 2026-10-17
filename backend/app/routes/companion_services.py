# from fastapi import APIRouter, Request, Depends, HTTPException, status
# from routes.profile import get_current_user
# from pydantic import BaseModel, Field
# from typing import Optional, List
# import secrets
# import json
#
# router = APIRouter()
#
#
# class CompanionServiceItem(BaseModel):
#     id: Optional[str] = None
#     name: str = Field(..., min_length=1, max_length=100)
#     price: int = Field(..., ge=0)
#     duration: Optional[str] = "1 hr"
#     title: Optional[str] = None
#
#
# class CompanionServicesReplace(BaseModel):
#     services: List[CompanionServiceItem]
#
#
# def _parse_services(raw) -> list:
#     if raw is None:
#         return []
#     if isinstance(raw, list):
#         return raw
#     try:
#         parsed = json.loads(raw)
#         return parsed if isinstance(parsed, list) else []
#     except Exception:
#         return []
#
#
# def _normalize_item(item: dict | CompanionServiceItem, index: int = 0) -> dict:
#     if hasattr(item, "model_dump"):
#         d = item.model_dump()
#     else:
#         d = dict(item)
#
#     name = (d.get("name") or d.get("title") or f"Service {index + 1}").strip()
#     sid = (d.get("id") or "").strip() or f"svc_{secrets.token_hex(4)}"
#     price = int(d.get("price") or 0)
#     duration = (d.get("duration") or "1 hr").strip() or "1 hr"
#
#     return {
#         "id": sid,
#         "name": name,
#         "title": name,
#         "price": price,
#         "duration": duration,
#     }
#
#
# def _require_companion(user: dict):
#     role = str(user.get("want_to") or "").strip().lower()
#     # support new + old role strings
#     ok = role in (
#         "companion",
#         "both",
#         "become a rentpeople",
#         "become",
#     ) or "become" in role or "both" in role or role == "companion"
#     if not ok and role == "finder":
#         raise HTTPException(
#             status_code=403,
#             detail="Only companions can manage services",
#         )
#
#
# async def _load_services(db, user_id: str) -> list:
#     row = await db.prepare(
#         "SELECT services, want_to FROM users WHERE id = ?"
#     ).bind(user_id).first()
#     if not row:
#         raise HTTPException(status_code=404, detail="User not found")
#     return _parse_services(dict(row).get("services")), dict(row)
#
#
# async def _save_services(db, user_id: str, services: list):
#     await db.prepare(
#         "UPDATE users SET services = ? WHERE id = ?"
#     ).bind(json.dumps(services), user_id).run()
#
#
# @router.get("/companion/services")
# async def list_my_services(
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     """List services for the logged-in companion."""
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#     services, _ = await _load_services(db, user_id)
#     normalized = [_normalize_item(s, i) for i, s in enumerate(services)]
#
#     return {
#         "count": len(normalized),
#         "services": normalized,
#         "data": normalized,
#     }
#
#
# @router.put("/companion/services")
# async def replace_services(
#     data: CompanionServicesReplace,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     """Replace entire services list."""
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#     _require_companion(current_user)
#
#     services = [_normalize_item(s, i) for i, s in enumerate(data.services)]
#     await _save_services(db, user_id, services)
#
#     return {
#         "message": "Services updated",
#         "count": len(services),
#         "services": services,
#     }
#
#
# @router.post("/companion/services", status_code=status.HTTP_201_CREATED)
# async def add_service(
#     data: CompanionServiceItem,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     """Add one service."""
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#     _require_companion(current_user)
#
#     services, _ = await _load_services(db, user_id)
#     services = [_normalize_item(s, i) for i, s in enumerate(services)]
#
#     new_item = _normalize_item(data, len(services))
#     # unique id
#     existing_ids = {s["id"] for s in services}
#     while new_item["id"] in existing_ids:
#         new_item["id"] = f"svc_{secrets.token_hex(4)}"
#
#     services.append(new_item)
#     await _save_services(db, user_id, services)
#
#     return {
#         "message": "Service added",
#         "service": new_item,
#         "services": services,
#     }
#
#
# @router.patch("/companion/services/{service_id}")
# async def update_service(
#     service_id: str,
#     data: CompanionServiceItem,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     """Update one service by id."""
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#     _require_companion(current_user)
#
#     services, _ = await _load_services(db, user_id)
#     services = [_normalize_item(s, i) for i, s in enumerate(services)]
#
#     found = False
#     for i, s in enumerate(services):
#         if s["id"] == service_id:
#             updated = _normalize_item(data, i)
#             updated["id"] = service_id  # keep same id
#             services[i] = updated
#             found = True
#             break
#
#     if not found:
#         raise HTTPException(status_code=404, detail="Service not found")
#
#     await _save_services(db, user_id, services)
#
#     return {
#         "message": "Service updated",
#         "service": next(s for s in services if s["id"] == service_id),
#         "services": services,
#     }
#
#
# @router.delete("/companion/services/{service_id}")
# async def delete_service(
#     service_id: str,
#     request: Request,
#     current_user: dict = Depends(get_current_user),
# ):
#     """Remove one service by id."""
#     db = request.scope["env"].DB
#     user_id = current_user["id"]
#     _require_companion(current_user)
#
#     services, _ = await _load_services(db, user_id)
#     services = [_normalize_item(s, i) for i, s in enumerate(services)]
#     new_list = [s for s in services if s["id"] != service_id]
#
#     if len(new_list) == len(services):
#         raise HTTPException(status_code=404, detail="Service not found")
#
#     await _save_services(db, user_id, new_list)
#
#     return {
#         "message": "Service removed",
#         "id": service_id,
#         "services": new_list,
#     }




from fastapi import APIRouter, Request, Depends, HTTPException, status
from routes.profile import get_current_user
from pydantic import BaseModel, Field
from typing import Optional, List, Any
import secrets
import json

router = APIRouter()


class PreferredLocation(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class CompanionServiceItem(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100)
    price: int = Field(..., ge=0)
    duration: Optional[str] = "1 hr"
    title: Optional[str] = None
    # Place fields (app sends these)
    locations: Optional[List[str]] = None
    preferred_locations: Optional[List[PreferredLocation]] = None


class CompanionServicesReplace(BaseModel):
    services: List[CompanionServiceItem]


def _parse_services(raw) -> list:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _norm_preferred_locations(raw: Any) -> list:
    """Normalize list of {name, address, lat, lng}."""
    if not raw:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return []
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


def _norm_location_names(raw: Any, preferred: list) -> list:
    """String list of place names; fall back from preferred_locations."""
    names: list[str] = []
    if isinstance(raw, list):
        for x in raw:
            if isinstance(x, str) and x.strip():
                names.append(x.strip()[:200])
            elif isinstance(x, dict) and (x.get("name") or "").strip():
                names.append(str(x["name"]).strip()[:200])
    # Ensure names from preferred_locations are included
    for p in preferred:
        n = (p.get("name") or "").strip()
        if n and n not in names:
            names.append(n)
    return names


def _normalize_item(item: dict | CompanionServiceItem, index: int = 0) -> dict:
    if hasattr(item, "model_dump"):
        d = item.model_dump()
    else:
        d = dict(item)

    name = (d.get("name") or d.get("title") or f"Service {index + 1}").strip()
    sid = (d.get("id") or "").strip() or f"svc_{secrets.token_hex(4)}"
    price = int(d.get("price") or 0)
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


def _require_companion(user: dict):
    role = str(user.get("want_to") or "").strip().lower()
    ok = role in (
        "companion",
        "both",
        "become a rentpeople",
        "become",
    ) or "become" in role or "both" in role or role == "companion"
    if not ok and role == "finder":
        raise HTTPException(
            status_code=403,
            detail="Only companions can manage services",
        )


async def _load_services(db, user_id: str) -> tuple[list, dict]:
    row = await db.prepare(
        "SELECT services, want_to FROM users WHERE id = ?"
    ).bind(user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return _parse_services(dict(row).get("services")), dict(row)


async def _save_services(db, user_id: str, services: list):
    await db.prepare(
        "UPDATE users SET services = ? WHERE id = ?"
    ).bind(json.dumps(services), user_id).run()


@router.get("/companion/services")
async def list_my_services(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]
    services, _ = await _load_services(db, user_id)
    normalized = [_normalize_item(s, i) for i, s in enumerate(services)]

    return {
        "count": len(normalized),
        "services": normalized,
        "data": normalized,
    }


@router.put("/companion/services")
async def replace_services(
    data: CompanionServicesReplace,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Replace entire services list (keeps locations + preferred_locations)."""
    db = request.scope["env"].DB
    user_id = current_user["id"]
    _require_companion(current_user)

    services = [_normalize_item(s, i) for i, s in enumerate(data.services)]
    await _save_services(db, user_id, services)

    return {
        "message": "Services updated",
        "count": len(services),
        "services": services,
    }


@router.post("/companion/services", status_code=status.HTTP_201_CREATED)
async def add_service(
    data: CompanionServiceItem,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]
    _require_companion(current_user)

    services, _ = await _load_services(db, user_id)
    services = [_normalize_item(s, i) for i, s in enumerate(services)]

    new_item = _normalize_item(data, len(services))
    existing_ids = {s["id"] for s in services}
    while new_item["id"] in existing_ids:
        new_item["id"] = f"svc_{secrets.token_hex(4)}"

    services.append(new_item)
    await _save_services(db, user_id, services)

    return {
        "message": "Service added",
        "service": new_item,
        "services": services,
    }


@router.patch("/companion/services/{service_id}")
async def update_service(
    service_id: str,
    data: CompanionServiceItem,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]
    _require_companion(current_user)

    services, _ = await _load_services(db, user_id)
    services = [_normalize_item(s, i) for i, s in enumerate(services)]

    found = False
    for i, s in enumerate(services):
        if s["id"] == service_id:
            updated = _normalize_item(data, i)
            updated["id"] = service_id
            services[i] = updated
            found = True
            break

    if not found:
        raise HTTPException(status_code=404, detail="Service not found")

    await _save_services(db, user_id, services)

    return {
        "message": "Service updated",
        "service": next(s for s in services if s["id"] == service_id),
        "services": services,
    }


@router.delete("/companion/services/{service_id}")
async def delete_service(
    service_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]
    _require_companion(current_user)

    services, _ = await _load_services(db, user_id)
    services = [_normalize_item(s, i) for i, s in enumerate(services)]
    new_list = [s for s in services if s["id"] != service_id]

    if len(new_list) == len(services):
        raise HTTPException(status_code=404, detail="Service not found")

    await _save_services(db, user_id, new_list)

    return {
        "message": "Service removed",
        "id": service_id,
        "services": new_list,
    }