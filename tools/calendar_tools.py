
"""Google Calendar tools for the productivity agent."""

import hashlib
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain.tools import tool


BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "calendar_token.json"

# Allows the app to create and modify calendar events.
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def get_calendar_service():
    """Authenticate and return the Google Calendar API service."""
    if not CREDENTIALS_FILE.is_file():
        raise FileNotFoundError(
            "credentials.json is missing from the project folder."
        )

    credentials = None

    if TOKEN_FILE.is_file():
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE)
        )

    has_required_scope = (
        credentials is not None
        and credentials.has_scopes(SCOPES)
    )

    if (
        credentials is not None
        and credentials.expired
        and credentials.refresh_token
        and has_required_scope
    ):
        credentials.refresh(Request())

    if (
        credentials is None
        or not credentials.valid
        or not credentials.has_scopes(SCOPES)
    ):
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            SCOPES,
        )
        credentials = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(
        credentials.to_json(),
        encoding="utf-8",
    )

    return build(
        "calendar",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )


def _parse_datetime(value: str, field_name: str) -> datetime:
    """Parse an ISO 8601 datetime and require a timezone offset."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{field_name} must be an ISO 8601 datetime with a timezone."
        )

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} is not a valid ISO 8601 datetime."
        ) from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(
            f"{field_name} must include a timezone offset, "
            "for example 2026-10-15T17:30:00+03:00."
        )

    return parsed


@tool
def create_calendar_event(
    title: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    timezone: str = "Africa/Nairobi",
    location: str = "",
    source_url: str = "",
) -> str:
    """Create a Google Calendar event with a pop-up reminder 30 minutes
    before it starts.

    Use ISO 8601 start and end values with timezone offsets, such as
    2026-10-15T17:30:00+03:00. Use an IANA timezone name, such as
    Africa/Nairobi. Include the original event URL in source_url when
    the event came from a webpage. Do not invent missing event details.
    """
    if not title or not title.strip():
        return "Error: The event title cannot be empty."

    if not timezone or not timezone.strip():
        return "Error: A timezone name is required."

    try:
        start = _parse_datetime(start_datetime, "start_datetime")
        end = _parse_datetime(end_datetime, "end_datetime")

        if end <= start:
            return "Error: The event end time must be after its start time."

        if source_url:
            if not source_url.startswith(("https://", "http://")):
                return "Error: source_url must be an HTTP or HTTPS URL."

        # Store a stable marker so repeat requests for the same source
        # can reuse the existing event rather than creating duplicates.
        source_hash = (
            hashlib.sha256(source_url.encode("utf-8")).hexdigest()
            if source_url
            else None
        )

        service = get_calendar_service()

        if source_hash:
            existing_result = (
                service.events()
                .list(
                    calendarId="primary",
                    privateExtendedProperty=f"sourceHash={source_hash}",
                    maxResults=10,
                )
                .execute()
            )

            existing_events = existing_result.get("items", [])
            if existing_events:
                existing = existing_events[0]
                existing_start = existing.get("start", {}).get(
                    "dateTime",
                    existing.get("start", {}).get("date", ""),
                )
                return (
                    "This source link already has a calendar event; "
                    "I did not create a duplicate.\n"
                    f"Title: {existing.get('summary', title)}\n"
                    f"Start: {existing_start}\n"
                    f"Calendar link: {existing.get('htmlLink', '(not provided)')}"
                )

        description_parts = []
        if description.strip():
            description_parts.append(description.strip())
        if source_url:
            description_parts.append(f"Source event: {source_url}")

        event_body = {
            "summary": title.strip(),
            "description": "\n\n".join(description_parts),
            "start": {
                "dateTime": start.isoformat(),
                "timeZone": timezone.strip(),
            },
            "end": {
                "dateTime": end.isoformat(),
                "timeZone": timezone.strip(),
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {
                        "method": "popup",
                        "minutes": 30,
                    }
                ],
            },
        }

        if location.strip():
            event_body["location"] = location.strip()

        if source_hash:
            event_body["extendedProperties"] = {
                "private": {"sourceHash": source_hash}
            }

        created = (
            service.events()
            .insert(
                calendarId="primary",
                body=event_body,
            )
            .execute()
        )

        created_start = created.get("start", {}).get(
            "dateTime",
            created.get("start", {}).get("date", ""),
        )
        created_end = created.get("end", {}).get(
            "dateTime",
            created.get("end", {}).get("date", ""),
        )

        return (
            "Calendar event created successfully.\n"
            f"Title: {created.get('summary', title)}\n"
            f"Start: {created_start}\n"
            f"End: {created_end}\n"
            "Reminder: pop-up 30 minutes before the event.\n"
            f"Calendar link: {created.get('htmlLink', '(not provided)')}"
        )

    except (ValueError, HttpError) as exc:
        return f"Could not create the calendar event: {exc}"
    except Exception as exc:
        return (
            "Could not create the calendar event. "
            f"{type(exc).__name__}: {exc}"
        )
