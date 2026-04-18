import os
from dotenv import load_dotenv

load_dotenv()

INFERX_BASE_URL = os.getenv("INFERX_BASE_URL", "https://api.openai.com/v1")
INFERX_API_KEY  = os.getenv("INFERX_API_KEY", "")
INFERX_MODEL    = os.getenv("INFERX_MODEL", "gemma-4-31b")
SAFE_MODE       = os.getenv("AURA_SAFE_MODE", "true").lower() == "true"

# Commands that always require explicit user confirmation regardless of SAFE_MODE
ALWAYS_CONFIRM_PATTERNS = [
    "rm ", "rmdir", "sudo", "chmod", "chown",
    "dd ", "mkfs", ":(){:|:&};:", "shutdown", "reboot",
    "git push", "pip install", "npm install",
]

VERSION = "0.1.0"
