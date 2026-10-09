from fastapi import APIRouter, Request, Depends, HTTPException, status, Query
from routes.profile import get_current_user
from pydantic import BaseModel, Field
from typing import Optional
import secrets
import json

router = APIRouter()


def _format_notification(row: dict) -> dict:
    raw_data = row.get("data")
    parsed = None
    if raw_data:
        try:
            parsed = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
        except Exception:
            parsed = {"raw": raw_data}

    return {
        "id": row["id"],
        "title": row.get("title") or "",
        "body": row.get("body") or "",
        "message": row.get("body") or "",  # Flutter alias
        "type": row.get("type") or "general",
        "data": parsed,
        "is_read": bool(row.get("is_read", 0)),
        "read": bool(row.get("is_read", 0)),
        "created_at": row.get("created_at"),
    }


async def create_notification(
    db,
    user_id: str,
    title: str,
    body: str = "",
    type: str = "general",
    data: dict | None = None,
):
    """Call from bookings / wallet / messages to push a notification."""
    nid = secrets.token_hex(8)
    await db.prepare(
        """
        INSERT INTO notifications (id, user_id, title, body, type, data, is_read)
        VALUES (?, ?, ?, ?, ?, ?, 0)
        """
    ).bind(
        nid,
        user_id,
        title,
        body or "",
        type,
        json.dumps(data) if data else None,
    ).run()
    return nid


@router.get("/notifications")
async def list_notifications(
    request: Request,
    current_user: dict = Depends(get_current_user),
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Flutter: GET /api/notifications
    Optional: ?unread_only=true
    """
    db = request.scope["env"].DB
    user_id = current_user["id"]

    if unread_only:
        rows = await db.prepare(
            """
            SELECT * FROM notifications
            WHERE user_id = ? AND is_read = 0
            ORDER BY created_at DESC
            LIMIT ?
            """
        ).bind(user_id, limit).all()
    else:
        rows = await db.prepare(
            """
            SELECT * FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """
        ).bind(user_id, limit).all()

    items = rows.results if hasattr(rows, "results") else rows
    notifications = [_format_notification(dict(r)) for r in items]

    unread_row = await db.prepare(
        """
        SELECT COUNT(*) AS cnt FROM notifications
        WHERE user_id = ? AND is_read = 0
        """
    ).bind(user_id).first()
    unread_count = int(dict(unread_row).get("cnt") or 0) if unread_row else 0

    return {
        "count": len(notifications),
        "unread_count": unread_count,
        "notifications": notifications,
        "data": notifications,
        "items": notifications,
    }


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT id FROM notifications WHERE id = ? AND user_id = ?"
    ).bind(notification_id, user_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")

    await db.prepare(
        "UPDATE notifications SET is_read = 1 WHERE id = ?"
    ).bind(notification_id).run()

    return {"id": notification_id, "is_read": True, "message": "Marked as read"}


@router.post("/notifications/read-all")
async def mark_all_read(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    await db.prepare(
        "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0"
    ).bind(user_id).run()

    return {"message": "All notifications marked as read"}


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    user_id = current_user["id"]

    row = await db.prepare(
        "SELECT id FROM notifications WHERE id = ? AND user_id = ?"
    ).bind(notification_id, user_id).first()

    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")

    await db.prepare(
        "DELETE FROM notifications WHERE id = ?"
    ).bind(notification_id).run()

    return {"message": "Notification deleted", "id": notification_id}