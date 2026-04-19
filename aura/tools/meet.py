"""
aura/tools/meet.py — Google Meet integration for AURA.

Creates Google Meet video conferences via Calendar API and optionally
emails the Meet link to specified recipients via Gmail.

Uses the same credentials.json / token.json as Gmail & Calendar tools.
Scopes cover both Calendar (Meet creation) and Gmail (sending the link).
"""

import os
import base64
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "credentials.json")
TOKEN_FILE       = os.path.join(os.path.dirname(__file__), "..", "..", "token.json")

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "meet_create",
            "description": (
                "Create a Google Meet video conference linked to a Google Calendar event. "
                "Optionally sends calendar invites to attendees and/or emails the Meet link "
                "to additional recipients. Returns the Meet link and calendar event URL."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Meeting title / subject."
                    },
                    "start_datetime": {
                        "type": "string",
                        "description": "Start date and time in ISO 8601 format, e.g. '2025-04-20T10:00:00'."
                    },
                    "end_datetime": {
                        "type": "string",
                        "description": "End date and time in ISO 8601. Defaults to 1 hour after start."
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Email addresses of people to invite via Google Calendar. "
                            "They will get a calendar invite with the Meet link automatically."
                        )
                    },
                    "email_link_to": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Extra email addresses to send just a plain email containing the Meet link "
                            "(without a calendar invite). Use for people who only need the link."
                        )
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional meeting agenda or notes shown in the calendar invite."
                    }
                },
                "required": ["title", "start_datetime"]
            }
        }
    }
]


def _get_creds():
    """Authenticate and return Google OAuth credentials covering Calendar + Gmail."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

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
                    "  1. Go to https://console.cloud.google.com/\n"
                    "  2. Enable 'Google Calendar API' and 'Gmail API'\n"
                    "  3. Credentials → OAuth 2.0 Client ID → Desktop app → Download JSON\n"
                    "  4. Save as 'credentials.json' in the project root.\n"
                    "  5. Delete token.json if it exists, then run again."
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return creds


def _send_meet_link_email(gmail_service, recipient: str, title: str, meet_link: str,
                           start_str: str, description: str = "") -> None:
    """Send a plain email containing the Meet link to a recipient."""
    msg = MIMEMultipart("alternative")
    msg["To"] = recipient
    msg["Subject"] = f"You're invited: {title}"

    body_lines = [
        f"Hi,",
        f"",
        f"You've been invited to join a Google Meet:",
        f"",
        f"  📅 {title}",
        f"  🕐 {start_str}",
        f"  🔗 {meet_link}",
    ]
    if description:
        body_lines += ["", "Agenda:", description]
    body_lines += ["", "Click the link above at the scheduled time to join.", "", "— AURA"]

    msg.attach(MIMEText("\n".join(body_lines), "plain"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    gmail_service.users().messages().send(userId="me", body={"raw": raw}).execute()


def meet_create(
    title: str,
    start_datetime: str,
    end_datetime: str = None,
    attendees: list = None,
    email_link_to: list = None,
    description: str = ""
) -> str:
    try:
        from googleapiclient.discovery import build

        creds = _get_creds()
        cal_service = build("calendar", "v3", credentials=creds)

        # Build start/end datetimes
        dt_start = datetime.datetime.fromisoformat(start_datetime)
        if end_datetime:
            dt_end = datetime.datetime.fromisoformat(end_datetime)
        else:
            dt_end = dt_start + datetime.timedelta(hours=1)

        # Build the calendar event body
        event_body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": dt_start.isoformat(), "timeZone": "Asia/Kolkata"},
            "end":   {"dateTime": dt_end.isoformat(),   "timeZone": "Asia/Kolkata"},
            "conferenceData": {
                "createRequest": {
                    "requestId": f"aura-meet-{int(datetime.datetime.now().timestamp())}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}
                }
            },
        }

        if attendees:
            event_body["attendees"] = [{"email": a.strip()} for a in attendees]

        # conferenceDataVersion=1 triggers Meet link generation
        created = cal_service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates="all" if attendees else "none",
        ).execute()

        meet_link = created.get("hangoutLink", "(Meet link not generated)")
        cal_link  = created.get("htmlLink", "")
        event_start = created["start"].get("dateTime", start_datetime)

        result_lines = [
            "[ AURA ] ✓ Google Meet created!",
            f"  Title    : {title}",
            f"  Starts   : {event_start}",
            f"  Meet link: {meet_link}",
            f"  Calendar : {cal_link}",
        ]

        if attendees:
            result_lines.append(f"  Invites sent to: {', '.join(attendees)}")

        # Send plain-email link to extra recipients
        if email_link_to and meet_link:
            gmail_service = build("gmail", "v1", credentials=creds)
            sent_to = []
            for recipient in email_link_to:
                try:
                    _send_meet_link_email(
                        gmail_service, recipient.strip(), title, meet_link, event_start, description
                    )
                    sent_to.append(recipient.strip())
                except Exception as mail_err:
                    result_lines.append(f"  ⚠ Failed to email {recipient}: {mail_err}")
            if sent_to:
                result_lines.append(f"  Meet link emailed to: {', '.join(sent_to)}")

        return "\n".join(result_lines)

    except Exception as ex:
        return f"[ AURA ] meet_create failed: {ex}"
