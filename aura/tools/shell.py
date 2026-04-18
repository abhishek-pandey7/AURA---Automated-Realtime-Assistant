import subprocess
import os
from aura.confirm import confirm_shell
from aura.config import ALWAYS_CONFIRM_PATTERNS

TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": (
            "Run a bash shell command in the current working directory. "
            "Returns stdout and stderr. Use for running scripts, installing packages, "
            "executing code, checking git status, listing processes, etc."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute.",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Max seconds to wait. Default 60.",
                    "default": 60,
                },
            },
            "required": ["command"],
        },
    },
}


def run(command: str, timeout: int = 60) -> str:
    """Execute a shell command. Asks confirmation for dangerous commands."""
    needs_confirm = any(p in command.lower() for p in ALWAYS_CONFIRM_PATTERNS)
    if needs_confirm:
        approved = confirm_shell(command)
        if not approved:
            return "[ AURA ] Command cancelled by user."

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),   # always runs in the directory where aura was launched
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        return output.strip() or "[ no output ]"

    except subprocess.TimeoutExpired:
        return f"[ AURA ] Command timed out after {timeout}s."
    except Exception as e:
        return f"[ AURA ] Error running command: {e}"
