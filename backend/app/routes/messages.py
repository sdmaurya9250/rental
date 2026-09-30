from fastapi import APIRouter, Request, Depends, HTTPException, status
from models.user import MessageCreate
from routes.profile import get_current_user
import secrets

router = APIRouter()


def _user_brief(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "name": row.get("full_name") or "User",
        "image": row.get("image") or "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=200&auto=format&fit=crop",
        "isOnline": bool(row.get("is_available", 0)),
        "city": row.get("city") or "",
    }


@router.get("/messages/conversations")
async def list_conversations(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """List people I have chatted with (inbox)."""
    db = request.scope["env"].DB
    user_id = current_user["id"]

    # Get distinct other users from messages involving me
    rows = await db.prepare(
        """
        SELECT
            CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END AS other_id,
            MAX(created_at) AS last_at
        FROM messages
        WHERE sender_id = ? OR receiver_id = ?
        GROUP BY other_id
        ORDER BY last_at DESC
        """
    ).bind(user_id, user_id, user_id).all()

    items = rows.results if hasattr(rows, "results") else rows
    conversations = []

    for item in items:
        other_id = dict(item).get("other_id")
        if not other_id:
            continue

        user_row = await db.prepare(
            "SELECT id, full_name, image, is_available, city FROM users WHERE id = ?"
        ).bind(other_id).first()

        if not user_row:
            continue

        u = dict(user_row)

        # Last message
        last = await db.prepare(
            """
            SELECT content, sender_id, created_at
            FROM messages
            WHERE (sender_id = ? AND receiver_id = ?)
               OR (sender_id = ? AND receiver_id = ?)
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).bind(user_id, other_id, other_id, user_id).first()

        last_msg = dict(last) if last else {}

        # Unread count (messages sent to me that are unread)
        unread = await db.prepare(
            """
            SELECT COUNT(*) AS cnt FROM messages
            WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
            """
        ).bind(other_id, user_id).first()
        unread_count = int(dict(unread).get("cnt") or 0) if unread else 0

        conversations.append({
            **_user_brief(u),
            "last_message": last_msg.get("content") or "",
            "last_message_at": last_msg.get("created_at") or "",
            "last_message_from_me": last_msg.get("sender_id") == user_id,
            "unread_count": unread_count,
        })

    return {
        "count": len(conversations),
        "conversations": conversations,
    }


@router.get("/messages/{other_user_id}")
async def get_messages(
    other_user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get chat messages with one person + mark their messages as read."""
    db = request.scope["env"].DB
    user_id = current_user["id"]

    if other_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    other = await db.prepare(
        "SELECT id, full_name, image, is_available, city FROM users WHERE id = ?"
    ).bind(other_user_id).first()

    if not other:
        raise HTTPException(status_code=404, detail="User not found")

    rows = await db.prepare(
        """
        SELECT id, sender_id, receiver_id, content, is_read, created_at
        FROM messages
        WHERE (sender_id = ? AND receiver_id = ?)
           OR (sender_id = ? AND receiver_id = ?)
        ORDER BY created_at ASC
        """
    ).bind(user_id, other_user_id, other_user_id, user_id).all()

    items = rows.results if hasattr(rows, "results") else rows
    messages = []

    for row in items:
        r = dict(row)
        messages.append({
            "id": r["id"],
            "content": r["content"],
            "from_me": r["sender_id"] == user_id,
            "sender_id": r["sender_id"],
            "receiver_id": r["receiver_id"],
            "is_read": bool(r.get("is_read", 0)),
            "created_at": r.get("created_at"),
        })

    # Mark messages from the other user as read
    await db.prepare(
        """
        UPDATE messages SET is_read = 1
        WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
        """
    ).bind(other_user_id, user_id).run()

    return {
        "person": _user_brief(dict(other)),
        "messages": messages,
        "count": len(messages),
    }


@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def send_message(
    data: MessageCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Send a message to another user."""
    db = request.scope["env"].DB
    sender_id = current_user["id"]
    content = data.content.strip()

    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if data.receiver_id == sender_id:
        raise HTTPException(status_code=400, detail="Cannot message yourself")

    receiver = await db.prepare(
        "SELECT id FROM users WHERE id = ?"
    ).bind(data.receiver_id).first()

    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    msg_id = secrets.token_hex(8)

    await db.prepare(
        """
        INSERT INTO messages (id, sender_id, receiver_id, content, is_read)
        VALUES (?, ?, ?, ?, 0)
        """
    ).bind(msg_id, sender_id, data.receiver_id, content).run()

    return {
        "id": msg_id,
        "content": content,
        "from_me": True,
        "sender_id": sender_id,
        "receiver_id": data.receiver_id,
        "is_read": False,
        "message": "Message sent",
    }