"""
Trust & safety: reports, blocks, suspension, ID-verified checks, chat filter.

Tables are created on first use (CREATE TABLE IF NOT EXISTS), so no manual
migration is needed. Helpers here are imported by bookings, wallet and messages.
"""
import re
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from routes.profile import get_current_user

router = APIRouter()

AUTO_SUSPEND_REPORTERS = 2  # distinct users reporting the same account

_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        reporter_id TEXT NOT NULL,
        reported_id TEXT NOT NULL,
        booking_id TEXT,
        reason TEXT NOT NULL,
        details TEXT,
        status TEXT NOT NULL DEFAULT 'open',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_reports_reported ON reports (reported_id, status)",
    """
    CREATE TABLE IF NOT EXISTS user_blocks (
        blocker_id TEXT NOT NULL,
        blocked_id TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (blocker_id, blocked_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_flags (
        user_id TEXT PRIMARY KEY,
        suspended INTEGER NOT NULL DEFAULT 0,
        reason TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS booking_idempotency (
        idem_key TEXT NOT NULL,
        user_id TEXT NOT NULL,
        booking_id TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (idem_key, user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS otp_attempts (
        booking_id TEXT PRIMARY KEY,
        attempts INTEGER NOT NULL DEFAULT 0
    )
    """,
]

_ready = False


async def ensure_tables(db) -> None:
    global _ready
    if _ready:
        return
    for stmt in _SCHEMA:
        await db.prepare(stmt).run()
    _ready = True


def _rows(res) -> list:
    items = res.results if hasattr(res, "results") else res
    return [dict(r) for r in items]


# ── checks used by other routes ─────────────────────────────────────────────

async def is_kyc_verified(db, user_id: str) -> bool:
    row = await db.prepare(
        "SELECT status FROM kyc WHERE user_id = ? "
        "AND LOWER(COALESCE(status, '')) = 'verified' LIMIT 1"
    ).bind(user_id).first()
    return bool(row)


async def is_suspended(db, user_id: str) -> bool:
    row = await db.prepare(
        "SELECT suspended FROM user_flags WHERE user_id = ? AND suspended = 1"
    ).bind(user_id).first()
    return bool(row)


async def is_blocked_between(db, a: str, b: str) -> bool:
    row = await db.prepare(
        "SELECT 1 AS x FROM user_blocks "
        "WHERE (blocker_id = ? AND blocked_id = ?) "
        "   OR (blocker_id = ? AND blocked_id = ?) LIMIT 1"
    ).bind(a, b, b, a).first()
    return bool(row)


# ── chat / text filter ──────────────────────────────────────────────────────

_PHONE = re.compile(r"(?:\+?\d[\s\-\.\(\)]*){10,}")
_UPI = re.compile(r"[\w.\-]{2,}@[a-zA-Z]{2,}")
_LINK = re.compile(r"(https?://|www\.|t\.me/|wa\.me/)", re.I)
_OFF_APP = re.compile(
    r"\b(whats\s*app|watsapp|telegram|insta(gram)?\s*id|snap\s*chat|gpay|"
    r"google\s*pay|phone\s*pe|phonepe|paytm)\b",
    re.I,
)
# Starter list (English + Hinglish). Extend from real reports.
_SEXUAL = re.compile(
    r"\b(sex|s[e3]x|sexy|escort|call\s*girl|callboy|call\s*boy|gigolo|hookup|hook\s*up|"
    r"one\s*night|night\s*stand|nude|nudes|massage\s*happy|happy\s*ending|"
    r"hotel\s*room|room\s*booking|boyfriend\s*experience|girlfriend\s*experience|"
    r"gfe|bfe|paid\s*sex|chudai|randi|rand|lund|chut)\b",
    re.I,
)


def _squash(text: str) -> str:
    """Catch spelling tricks like 's e x', 's3x', 'w h a t s a p p'."""
    t = text.lower()
    t = t.translate(str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "@": "a", "$": "s"}))
    return re.sub(r"[^a-z]", "", t)


_SQUASHED_BAD = ("escort", "callgirl", "callboy", "gigolo", "hookup",
                 "nightstand", "happyending", "whatsapp", "telegram")


def check_message(text: str) -> Optional[str]:
    """Return a user-facing reason if the text must be blocked, else None."""
    t = text or ""
    if _PHONE.search(t) or len(re.sub(r"\D", "", t)) >= 10:
        return "Phone numbers can't be shared in chat. Please keep talking in the app."
    if _UPI.search(t) or _LINK.search(t):
        return "Links, payment IDs and emails can't be shared in chat."
    if _OFF_APP.search(t):
        return "Please keep the conversation and payments inside the app."
    if _SEXUAL.search(t):
        return "This message breaks our rules. Sexual services are not allowed."
    sq = _squash(t)
    if any(w in sq for w in _SQUASHED_BAD):
        return "This message breaks our rules."
    return None


# Places that are never allowed as a meeting point.
BLOCKED_PLACE_WORDS = (
    "hotel", "lodge", "resort", "oyo", "guest house", "guesthouse", "motel",
    "hostel", "homestay", "villa", "my home", "my house", "my room",
    "your home", "your house", "your room", "my flat", "your flat", "apartment",
    "private room", "farmhouse", "airbnb",
)
BLOCKED_PLACE_CATEGORIES = (
    "lodging", "hotel", "motel", "hostel", "guest_house", "resort", "residential",
)


def place_is_blocked(name: str, category: Optional[str]) -> bool:
    n = f" {(name or '').lower()} "
    if any(w in n for w in BLOCKED_PLACE_WORDS):
        return True
    c = (category or "").lower()
    return any(w in c for w in BLOCKED_PLACE_CATEGORIES)


# ── endpoints ───────────────────────────────────────────────────────────────

class ReportCreate(BaseModel):
    reported_user_id: str
    reason: str = Field(..., min_length=3, max_length=200)
    details: Optional[str] = Field(None, max_length=1000)
    booking_id: Optional[str] = None


class BlockCreate(BaseModel):
    blocked_user_id: str


@router.post("/reports", status_code=status.HTTP_201_CREATED)
async def create_report(
    data: ReportCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    me = current_user["id"]

    if data.reported_user_id == me:
        raise HTTPException(status_code=400, detail="You cannot report yourself")

    target = await db.prepare(
        "SELECT id FROM users WHERE id = ?"
    ).bind(data.reported_user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # Same reporter + same account + still open: don't count twice.
    dup = await db.prepare(
        "SELECT id FROM reports WHERE reporter_id = ? AND reported_id = ? "
        "AND status = 'open' LIMIT 1"
    ).bind(me, data.reported_user_id).first()

    report_id = dict(dup)["id"] if dup else secrets.token_hex(8)
    if not dup:
        await db.prepare(
            "INSERT INTO reports (id, reporter_id, reported_id, booking_id, reason, details) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        ).bind(
            report_id, me, data.reported_user_id, data.booking_id,
            data.reason.strip(), (data.details or "").strip(),
        ).run()

    # Two different people reported the same account: pause it until reviewed.
    cnt = await db.prepare(
        "SELECT COUNT(DISTINCT reporter_id) AS n FROM reports "
        "WHERE reported_id = ? AND status = 'open'"
    ).bind(data.reported_user_id).first()
    n = int(dict(cnt).get("n") or 0) if cnt else 0
    suspended = False
    if n >= AUTO_SUSPEND_REPORTERS:
        await db.prepare(
            "INSERT INTO user_flags (user_id, suspended, reason) VALUES (?, 1, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET suspended = 1, reason = excluded.reason, "
            "updated_at = CURRENT_TIMESTAMP"
        ).bind(data.reported_user_id, f"auto: {n} open reports").run()
        suspended = True

    return {
        "id": report_id,
        "status": "open",
        "message": "Report received. Our team reviews reports within 24 hours.",
        "account_paused": suspended,
    }


@router.post("/blocks", status_code=status.HTTP_201_CREATED)
async def block_user(
    data: BlockCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    me = current_user["id"]
    if data.blocked_user_id == me:
        raise HTTPException(status_code=400, detail="You cannot block yourself")
    await db.prepare(
        "INSERT OR IGNORE INTO user_blocks (blocker_id, blocked_id) VALUES (?, ?)"
    ).bind(me, data.blocked_user_id).run()
    return {"blocked": True, "user_id": data.blocked_user_id}


@router.delete("/blocks/{user_id}")
async def unblock_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    await db.prepare(
        "DELETE FROM user_blocks WHERE blocker_id = ? AND blocked_id = ?"
    ).bind(current_user["id"], user_id).run()
    return {"blocked": False, "user_id": user_id}


@router.get("/blocks")
async def my_blocks(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    db = request.scope["env"].DB
    rows = await db.prepare(
        "SELECT blocked_id FROM user_blocks WHERE blocker_id = ?"
    ).bind(current_user["id"]).all()
    return {"blocked": [r["blocked_id"] for r in _rows(rows)]}
