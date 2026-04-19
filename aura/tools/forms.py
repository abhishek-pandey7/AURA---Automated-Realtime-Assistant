"""
aura/tools/forms.py — Google Forms auto-fill support for AURA.

Strategy:
  - User profile data is stored locally in user_profile.json (project root).
  - The LLM loads the profile, opens the form URL via browser/desktop tools,
    reads the field labels via OCR, and fills them using profile data.
  - forms_generate_prefill_url can generate a pre-filled Google Forms URL
    when the caller already knows the form entry IDs.

No additional Google API scopes are required — form filling uses existing
desktop tools (desktop_read_screen, desktop_click, desktop_type) or the
browser tools, orchestrated by the LLM.
"""

import os
import json

PROFILE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "user_profile.json")

# Canonical default profile — extend freely
DEFAULT_PROFILE = {
    "full_name": "",
    "first_name": "",
    "last_name": "",
    "email": "",
    "phone": "",
    "organization": "",
    "role": "",
    "college": "",
    "department": "",
    "year_of_study": "",
    "roll_number": "",
    "address": "",
    "city": "",
    "state": "",
    "country": "India",
    "pincode": "",
    "date_of_birth": "",
    "gender": "",
    "linkedin": "",
    "github": "",
    "portfolio": "",
    "skills": [],
    "bio": "",
}

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "forms_load_profile",
            "description": (
                "Load the user's personal profile (name, email, phone, college, skills, etc.) "
                "stored locally in user_profile.json. Call this FIRST before filling any web form "
                "so you know what data to enter into each field."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "forms_update_profile",
            "description": (
                "Save or update a single field in the user's local profile. "
                "Use this when the user provides new personal information that should be remembered."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {
                        "type": "string",
                        "description": (
                            "Profile field name. Common fields: full_name, first_name, last_name, "
                            "email, phone, organization, role, college, department, year_of_study, "
                            "roll_number, city, state, country, pincode, linkedin, github, skills, bio."
                        )
                    },
                    "value": {
                        "type": "string",
                        "description": "Value to store for this field."
                    }
                },
                "required": ["field", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "forms_generate_prefill_url",
            "description": (
                "Generate a Google Forms pre-filled URL given the base form URL and a mapping "
                "of entry IDs to values. The resulting URL can be opened directly and will have "
                "all specified fields pre-populated. Use this when you know the form's entry IDs "
                "(e.g. entry.123456789). Entry IDs can be found by inspecting the form HTML or "
                "Google's 'Get pre-filled link' feature."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "form_url": {
                        "type": "string",
                        "description": "The base Google Forms URL (e.g. https://forms.gle/... or https://docs.google.com/forms/d/.../viewform)."
                    },
                    "field_values": {
                        "type": "object",
                        "description": (
                            "A dict mapping entry IDs to values, e.g. "
                            "{\"entry.123456\": \"Abhishek Pandey\", \"entry.789012\": \"abhishek@example.com\"}."
                        )
                    }
                },
                "required": ["form_url", "field_values"]
            }
        }
    }
]


def _load_raw_profile() -> dict:
    """Load profile from disk, creating with defaults if missing."""
    if not os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_PROFILE, f, indent=2)
        return dict(DEFAULT_PROFILE)
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def forms_load_profile() -> str:
    """Return the user profile as a formatted string for the LLM."""
    try:
        profile = _load_raw_profile()

        # Check if profile is still empty (first-time setup)
        filled = [k for k, v in profile.items() if v and v != DEFAULT_PROFILE.get(k, "")]
        if not filled:
            return (
                "[ AURA ] User profile is empty.\n"
                f"  Profile file: {os.path.abspath(PROFILE_FILE)}\n\n"
                "  Ask the user for their details and use forms_update_profile to save them.\n\n"
                f"Profile template:\n{json.dumps(profile, indent=2)}"
            )

        return (
            "[ AURA ] User profile loaded:\n"
            f"{json.dumps(profile, indent=2)}\n\n"
            "  Use these values to fill form fields. Match field labels to the closest profile key."
        )
    except Exception as ex:
        return f"[ AURA ] forms_load_profile failed: {ex}"


def forms_update_profile(field: str, value: str) -> str:
    """Update a single field in user_profile.json."""
    try:
        profile = _load_raw_profile()
        profile[field] = value
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)
        return f"[ AURA ] ✓ Profile updated: {field!r} = {value!r}"
    except Exception as ex:
        return f"[ AURA ] forms_update_profile failed: {ex}"


def forms_generate_prefill_url(form_url: str, field_values: dict) -> str:
    """Generate a Google Forms pre-filled URL."""
    try:
        from urllib.parse import urlparse, urlencode, urlunparse, parse_qs, urljoin

        # Normalise the base URL to the /viewform endpoint
        parsed = urlparse(form_url)
        # Strip any existing query params that clash
        base = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
        if not base.endswith("/viewform"):
            base = base.rstrip("/") + "/viewform"

        # Build query string: each entry.XXXXXXX=value pair
        params = []
        for entry_id, val in field_values.items():
            # Accept bare numbers, "entry.XXXX", or "entry_XXXX"
            key = entry_id if entry_id.startswith("entry.") else f"entry.{entry_id.lstrip('entry_')}"
            params.append((key, str(val)))

        query = urlencode(params)
        prefill_url = f"{base}?{query}"

        lines = [
            "[ AURA ] ✓ Pre-filled Google Forms URL generated:",
            f"  {prefill_url}",
            "",
            "  Open this URL in a browser — all specified fields will be pre-populated.",
            "  The user still needs to review and submit the form manually (or use desktop tools to click Submit).",
        ]
        return "\n".join(lines)
    except Exception as ex:
        return f"[ AURA ] forms_generate_prefill_url failed: {ex}"
