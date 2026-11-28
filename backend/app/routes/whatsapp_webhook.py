# from fastapi import APIRouter, Request, HTTPException, Query
# from fastapi.responses import PlainTextResponse, JSONResponse
#
# router = APIRouter()
#
#
# @router.api_route("/whatsapp/webhook", methods=["GET", "POST"])
# async def whatsapp_webhook(
#     request: Request,
#     hub_mode: str | None = Query(None, alias="hub.mode"),
#     hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
#     hub_challenge: str | None = Query(None, alias="hub.challenge"),
# ):
#     # ── GET = verification ─────────────────────
#     if request.method == "GET":
#         env = request.scope.get("env")
#         expected = (getattr(env, "WHATSAPP_VERIFY_TOKEN", None) or "").strip()
#
#         if (
#             hub_mode == "subscribe"
#             and expected
#             and hub_verify_token == expected
#             and hub_challenge is not None
#         ):
#             # Must be plain text, not JSON
#             return PlainTextResponse(content=str(hub_challenge), status_code=200)
#
#         raise HTTPException(status_code=403, detail="Verification failed")
#
#     # ── POST = events (always 200 so Meta is happy) ──
#     try:
#         await request.json()
#     except Exception:
#         pass
#     return JSONResponse({"ok": True})


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
        # Must be plain text challenge only
        return PlainTextResponse(content=hub_challenge or "", status_code=200)

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/whatsapp/webhook")
async def whatsapp_events(request: Request):
    """Accept events; always 200 so Meta does not disable the webhook."""
    try:
        body = await request.json()
        # Optional: log or handle messages later
        _ = body
    except Exception:
        pass
    return {"status": "ok"}