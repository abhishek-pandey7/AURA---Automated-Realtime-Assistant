import json
import os
from datetime import datetime
from pathlib import Path

SESSIONS_DIR = Path.home() / ".aura" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


class Memory:
    """
    Conversation history for one AURA session.
    Stores messages in OpenAI format and persists to disk.
    """

    def __init__(self, session_id: str | None = None):
        if session_id:
            self.session_id = session_id
            self._load()
        else:
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.messages: list[dict] = []
            self.metadata = {
                "started": datetime.now().isoformat(),
                "cwd": os.getcwd(),
            }

    # ── Message helpers ───────────────────────────────────────────────────────

    def add_user(self, content: str):
        """Add a plain user message."""
        self.messages.append({"role": "user", "content": content})
        self._save()

    def add_assistant(self, content: str):
        """Add a plain assistant text response (no tool calls)."""
        self.messages.append({"role": "assistant", "content": content})
        self._save()

    def get_messages(self) -> list[dict]:
        return list(self.messages)

    def clear(self):
        self.messages = []
        self._save()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self):
        path = SESSIONS_DIR / f"{self.session_id}.json"
        with open(path, "w") as f:
            json.dump({
                "session_id": self.session_id,
                "metadata": self.metadata,
                "messages": self.messages,
            }, f, indent=2)

    def _load(self):
        path = SESSIONS_DIR / f"{self.session_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Session {self.session_id} not found.")
        with open(path) as f:
            data = json.load(f)
        self.messages = data["messages"]
        self.metadata = data["metadata"]

    @staticmethod
    def list_sessions() -> list[dict]:
        sessions = []
        for path in sorted(SESSIONS_DIR.glob("*.json"), reverse=True)[:10]:
            try:
                with open(path) as f:
                    data = json.load(f)
                sessions.append({
                    "id": data["session_id"],
                    "started": data["metadata"].get("started", "unknown"),
                    "cwd": data["metadata"].get("cwd", "unknown"),
                    "messages": len(data["messages"]),
                })
            except Exception:
                continue
        return sessions
