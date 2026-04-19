"""
aura/tools/calendar.py — Google Calendar integration for AURA.

First-time setup:
  1. Go to https://console.cloud.google.com/
  2. Create a new project → Enable "Google Calendar API"
  3. Credentials → Create OAuth 2.0 Client ID → Desktop app
  4. Download the JSON → save as credentials.json in the project root
  5. Run `aura run` and ask AURA to list events — it will open a browser for one-time auth.
     A token.json file will be saved so you never need to log in again.
"""

import os
import json
import datetime

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "token.json")

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "calendar_list_events",
            "description": "List upcoming events from Google Calendar. Returns the next N events with their title, date, and time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of upcoming events to return (default 10)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_add_event",
            "description": "Add a new event or reminder to Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title/summary of the event."
                    },
                    "start_datetime": {
                        "type": "string",
                        "description": "Start date and time in ISO 8601 format, e.g. '2025-04-20T09:00:00'. For all-day events use 'YYYY-MM-DD'."
                    },
                    "end_datetime": {
                        "type": "string",
                        "description": "End date and time in ISO 8601 format. If omitted, defaults to 1 hour after start."
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional longer description or notes for the event."
                    },
                    "reminder_minutes": {
                        "type": "integer",
                        "description": "Minutes before the event to send a popup reminder (default 10)."
                    }
                },
                "required": ["title", "start_datetime"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calendar_delete_event",
            "description": "Delete an event from Google Calendar by its title (deletes the next matching upcoming event).",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the event to delete."
                    }
                },
                "required": ["title"]
            }
        }
    }
]


def _get_service():
    """Authenticate and return the Google Calendar API service object."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    token_path = os.path.abspath(TOKEN_FILE)
    creds_path = os.path.abspath(CREDENTIALS_FILE)

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(
                    "[ AURA ] credentials.json not found!\n"
                    "  Please follow these steps:\n"
                    "  1. Go to https://console.cloud.google.com/\n"
                    "  2. Create a project → Enable 'Google Calendar API'\n"
                    "  3. Credentials → Create OAuth 2.0 Client ID → Desktop app\n"
                    "  4. Download JSON → save as 'credentials.json' in the project root.\n"
                    "  5. Run this command again — a browser window will open for one-time login."
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def calendar_list_events(max_results: int = 10) -> str:
    try:
        service = _get_service()
        now = datetime.datetime.utcnow().isoformat() + "Z"
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        if not events:
            return "[ AURA ] No upcoming events found in your Google Calendar."

        lines = [f"[ AURA ] Upcoming {len(events)} events:\n"]
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date", "Unknown"))
            title = e.get("summary", "(No title)")
            desc = e.get("description", "")
            desc_snippet = f" — {desc[:60]}" if desc else ""
            lines.append(f"  • {start}  |  {title}{desc_snippet}")

        return "\n".join(lines)
    except Exception as ex:
        return f"[ AURA ] Calendar list failed: {ex}"


def calendar_add_event(
    title: str,
    start_datetime: str,
    end_datetime: str = None,
    description: str = "",
    reminder_minutes: int = 10
) -> str:
    try:
        service = _get_service()

        # Detect all-day vs timed event
        if "T" in start_datetime:
            start_body = {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"}
            if end_datetime:
                end_body = {"dateTime": end_datetime, "timeZone": "Asia/Kolkata"}
            else:
                # Default: 1 hour duration
                dt = datetime.datetime.fromisoformat(start_datetime)
                end_body = {
                    "dateTime": (dt + datetime.timedelta(hours=1)).isoformat(),
                    "timeZone": "Asia/Kolkata"
                }
        else:
            # All-day event
            start_body = {"date": start_datetime}
            if end_datetime:
                end_body = {"date": end_datetime}
            else:
                dt = datetime.date.fromisoformat(start_datetime)
                end_body = {"date": (dt + datetime.timedelta(days=1)).isoformat()}

        event = {
            "summary": title,
            "description": description,
            "start": start_body,
            "end": end_body,
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": reminder_minutes},
                ]
            }
        }

        created = service.events().insert(calendarId="primary", body=event).execute()
        link = created.get("htmlLink", "")
        return f"[ AURA ] ✓ Event '{title}' created!\n  Starts: {start_datetime}\n  Link: {link}"
    except Exception as ex:
        return f"[ AURA ] Calendar add failed: {ex}"


def calendar_delete_event(title: str) -> str:
    try:
        service = _get_service()
        now = datetime.datetime.utcnow().isoformat() + "Z"

        events_result = service.events().list(
            calendarId="primary",
            timeMin=now,
            maxResults=20,
            singleEvents=True,
            orderBy="startTime",
            q=title
        ).execute()

        events = events_result.get("items", [])
        matched = [e for e in events if title.lower() in e.get("summary", "").lower()]

        if not matched:
            return f"[ AURA ] No upcoming event found with title matching '{title}'."

        event = matched[0]
        service.events().delete(calendarId="primary", eventId=event["id"]).execute()
        return f"[ AURA ] ✓ Deleted event: '{event.get('summary')}'"
    except Exception as ex:
        return f"[ AURA ] Calendar delete failed: {ex}"
