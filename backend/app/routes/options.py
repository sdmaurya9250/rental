from fastapi import APIRouter, Request, HTTPException
import json

router = APIRouter()

DEFAULT_OPTIONS = {
    "durations": ["1 hr", "2 hrs", "3 hrs", "Full Day"],
    "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "timeSlots": [
        "Morning (8–12)",
        "Afternoon (12–17)",
        "Evening (17–21)",
        "Night (21–24)",
    ],
    "languages": ["English", "Hindi", "Marathi", "Tamil"],
    "interests": ["Coffee", "Travel", "Movies", "Shopping", "Food"],
    "locations": ["Pune", "Mumbai", "Bangalore", "Hadapsar", "Hinjewadi"],
}


def _parse_list(raw, fallback: list) -> list:
    if raw is None:
        return list(fallback)
    if isinstance(raw, list):
        return raw
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list) and parsed:
            return parsed
    except Exception:
        pass
    return list(fallback)


@router.get("/options")
@router.get("/service-options")
async def get_service_options(request: Request):
    """
    App: GET /api/options  or  GET /api/service-options
    Returns durations, days, timeSlots, languages, interests, locations from DB.
    """
    db = request.scope["env"].DB

    try:
        row = await db.prepare(
            "SELECT * FROM app_options WHERE id = ?"
        ).bind("service_options").first()
    except Exception:
        # Table missing → defaults only
        return {**DEFAULT_OPTIONS, "source": "default"}

    if not row:
        # Auto-seed
        try:
            await db.prepare(
                """
                INSERT INTO app_options (
                    id, durations, days, time_slots, languages, interests, locations
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """
            ).bind(
                "service_options",
                json.dumps(DEFAULT_OPTIONS["durations"]),
                json.dumps(DEFAULT_OPTIONS["days"]),
                json.dumps(DEFAULT_OPTIONS["timeSlots"]),
                json.dumps(DEFAULT_OPTIONS["languages"]),
                json.dumps(DEFAULT_OPTIONS["interests"]),
                json.dumps(DEFAULT_OPTIONS["locations"]),
            ).run()
        except Exception:
            pass
        return {**DEFAULT_OPTIONS, "source": "default"}

    r = dict(row)
    return {
        "durations": _parse_list(r.get("durations"), DEFAULT_OPTIONS["durations"]),
        "days": _parse_list(r.get("days"), DEFAULT_OPTIONS["days"]),
        "timeSlots": _parse_list(r.get("time_slots"), DEFAULT_OPTIONS["timeSlots"]),
        "languages": _parse_list(r.get("languages"), DEFAULT_OPTIONS["languages"]),
        "interests": _parse_list(r.get("interests"), DEFAULT_OPTIONS["interests"]),
        "locations": _parse_list(r.get("locations"), DEFAULT_OPTIONS["locations"]),
        "source": "db",
    }