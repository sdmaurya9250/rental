"""Service types a companion can offer. Ids match kServiceTypes in the app."""

SERVICE_CATEGORIES = {
    "travel",
    "dinner",
    "events",
    "shopping",
    "coffee_chat",
    "movie_buddy",
    "walk_fitness",
    "sports_partner",
    "language_practice",
    "city_guide",
    "museum_art",
    "study_work",
    "other",
}


def clean_category(raw) -> str:
    """Return a known category id, or 'other' for empty / unknown values."""
    c = str(raw or "").strip().lower().replace(" ", "_").replace("&", "").replace("__", "_")
    return c if c in SERVICE_CATEGORIES else "other"
