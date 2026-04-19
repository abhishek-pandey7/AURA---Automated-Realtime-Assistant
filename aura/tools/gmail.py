"""
aura/tools/gmail.py — Gmail send/read integration for AURA.

Uses the same credentials.json / token.json as the Calendar tool.
The OAuth token will be automatically extended to include Gmail scopes
on the next login if needed.
"""

import os
import base64
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
]

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "token.json")

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "gmail_send",
            "description": "Send an email via Gmail API. Reliable programmatic send — does NOT need a browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address (or comma-separated list of addresses)."
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line."
                    },
                    "body": {
                        "type": "string",
                        "description": "Plain-text body of the email."
                    },
                    "cc": {
                        "type": "string",
                        "description": "Optional CC email addresses (comma-separated)."
                    }
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "gmail_read_inbox",
            "description": "Read the latest unread emails from the Gmail inbox. Returns sender, subject, and a short snippet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Number of recent emails to return (default 5)."
                    }
                },
                "required": []
            }
        }
    }
]


def _get_service():
    """Authenticate and return Gmail API service, reusing existing token if available."""
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
                    "  Steps:\n"
                    "  1. Go to https://console.cloud.google.com/\n"
                    "  2. Create project → Enable 'Gmail API' AND 'Google Calendar API'\n"
                    "  3. Credentials → OAuth 2.0 Client ID → Desktop app → Download JSON\n"
                    "  4. Save as 'credentials.json' in the project root.\n"
                    "  5. Delete token.json if it exists, then run this again."
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def gmail_send(to: str, subject: str, body: str, cc: str = "") -> str:
    try:
        service = _get_service()

        msg = MIMEMultipart("alternative")
        msg["To"] = to
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc
        msg.attach(MIMEText(body, "plain"))

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        return f"[ AURA ] ✓ Email sent to {to} with subject '{subject}'."
    except Exception as ex:
        return f"[ AURA ] Gmail send failed: {ex}"


def gmail_read_inbox(max_results: int = 5) -> str:
    try:
        service = _get_service()

        result = service.users().messages().list(
            userId="me",
            labelIds=["INBOX", "UNREAD"],
            maxResults=max_results
        ).execute()

        messages = result.get("messages", [])
        if not messages:
            return "[ AURA ] No unread messages in your inbox."

        lines = [f"[ AURA ] {len(messages)} unread email(s):\n"]
        for msg_ref in messages:
            msg = service.users().messages().get(
                userId="me",
                id=msg_ref["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()

            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            sender = headers.get("From", "Unknown")
            subject = headers.get("Subject", "(No subject)")
            date = headers.get("Date", "")
            snippet = msg.get("snippet", "")[:100]
            lines.append(f"  • From: {sender}\n    Subject: {subject}\n    Date: {date}\n    Preview: {snippet}\n")

        return "\n".join(lines)
    except Exception as ex:
        return f"[ AURA ] Gmail read failed: {ex}"
