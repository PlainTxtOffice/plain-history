"""Format saved snapshot times in the writer's local time zone."""

from datetime import datetime


def format_saved_at(created_at: str) -> str:
    """Return a local date and time such as "Oct 14, 2026 at 3:02 PM".

    Return the stored text unchanged when it is not an ISO 8601 timestamp.
    """
    try:
        moment = datetime.fromisoformat(created_at).astimezone()
    except ValueError:
        return created_at
    hour = moment.strftime("%I").lstrip("0")
    return f"{moment:%b} {moment.day}, {moment.year} at {hour}:{moment:%M %p}"
