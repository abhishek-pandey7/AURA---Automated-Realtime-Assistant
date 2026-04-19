import os
from pathlib import Path
from dotenv import load_dotenv

# Always load .env from the project root (two levels up from this file:
# aura/config.py → aura/ → project_root/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=_ENV_FILE)

INFERX_BASE_URL = os.getenv("INFERX_BASE_URL", "https://api.openai.com/v1")
INFERX_API_KEY  = os.getenv("INFERX_API_KEY", "")
INFERX_MODEL    = os.getenv("INFERX_MODEL", "gemma-4-31b")
SAFE_MODE       = os.getenv("AURA_SAFE_MODE", "true").lower() == "true"

if not INFERX_API_KEY:
    raise EnvironmentError(
        f"\n[ AURA ] Missing INFERX_API_KEY!\n"
        f"  Expected .env at: {_ENV_FILE}\n"
        f"  {'(file found but key is empty)' if _ENV_FILE.exists() else '(file NOT found)'}\n\n"
        f"  Fix: make sure your .env contains:\n"
        f"    INFERX_API_KEY=sk-...\n"
        f"  See .env.example for a full template."
    )

# Commands that always require explicit user confirmation regardless of SAFE_MODE
ALWAYS_CONFIRM_PATTERNS = [
    "rm ", "rmdir", "sudo", "chmod", "chown",
    "dd ", "mkfs", ":(){:|:&};:", "shutdown", "reboot",
    "git push", "pip install", "npm install",
]

VERSION = "0.1.0"
