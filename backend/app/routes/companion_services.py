from fastapi import APIRouter, Request, Depends, HTTPException, status
from routes.profile import get_current_user
from pydantic import BaseModel, Field
from typing import Optional, List
import secrets
import json

router = APIRouter()


class CompanionServiceItem(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=100)
    price: int = Field(..., ge=0)
    duration: Optional[str] = "1 hr"
    title: Optional[str] = None


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


def _normalize_item(item: dict | CompanionServiceItem, index: int = 0) -> dict:
    if hasattr(item, "model_dump"):
        d = item.model_dump()
    else:
        d = dict(item)

    name = (d.get("name") or d.get("title") or f"Service {index + 1}").strip()
    sid = (d.get("id") or "").strip() or f"svc_{secrets.token_hex(4)}"
    price = int(d.get("price") or 0)
    duration = (d.get("duration") or "1 hr").strip() or "1 hr"

    return {
        "id": sid,
        "name": name,
        "title": name,
        "price": price,
        "duration": duration,
    }


def _require_companion(user: dict):
    role = str(user.get("want_to") or "").strip().lower()
    # support new + old role strings
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


async def _load_services(db, user_id: str) -> list:
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
    """List services for the logged-in companion."""
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
    """Replace entire services list."""
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
    """Add one service."""
    db = request.scope["env"].DB
    user_id = current_user["id"]
    _require_companion(current_user)

    services, _ = await _load_services(db, user_id)
    services = [_normalize_item(s, i) for i, s in enumerate(services)]

    new_item = _normalize_item(data, len(services))
    # unique id
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
    """Update one service by id."""
    db = request.scope["env"].DB
    user_id = current_user["id"]
    _require_companion(current_user)

    services, _ = await _load_services(db, user_id)
    services = [_normalize_item(s, i) for i, s in enumerate(services)]

    found = False
    for i, s in enumerate(services):
        if s["id"] == service_id:
            updated = _normalize_item(data, i)
            updated["id"] = service_id  # keep same id
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
    """Remove one service by id."""
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