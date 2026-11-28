

from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
import json

router = APIRouter()


@router.get("/whatsapp/webhook")
async def whatsapp_verify(
    request: Request,
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
):
    env = request.scope["env"]
    expected = (getattr(env, "WHATSAPP_VERIFY_TOKEN", None) or "").strip()

    if hub_mode == "subscribe" and hub_verify_token and expected and hub_verify_token == expected:
        return PlainTextResponse(content=hub_challenge or "", status_code=200)

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp/webhook")
async def whatsapp_events(request: Request):
    """Accept events; always 200 so Meta does not disable the webhook."""
    try:
        body = await request.json()
        _ = body
    except Exception:
        pass
    return {"status": "ok"}