import os
from pathlib import Path
from aura.confirm import confirm_write, confirm_delete

# ── Tool definitions (sent to LLM) ───────────────────────────────────────────

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full contents of a file. Returns the text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file to read."},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write content to a file, creating it if it doesn't exist. "
                "Overwrites the entire file. Use patch_file for small edits."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write to."},
                    "content": {"type": "string", "description": "Full content to write."},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "patch_file",
            "description": (
                "Surgically replace a specific string in a file with a new string. "
                "Use this for small targeted edits instead of rewriting the whole file. "
                "old_str must match exactly as it appears in the file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "old_str": {"type": "string", "description": "Exact string to find and replace."},
                    "new_str": {"type": "string", "description": "String to replace it with."},
                },
                "required": ["path", "old_str", "new_str"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and directories at a given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path. Defaults to current dir."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file. Always asks for confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to delete."},
                },
                "required": ["path"],
            },
        },
    },
]

# ── Implementations ───────────────────────────────────────────────────────────

def read_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"[ AURA ] File not found: {path}"
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"[ AURA ] Could not read file: {e}"


def write_file(path: str, content: str) -> str:
    approved = confirm_write(path, preview=content)
    if not approved:
        return "[ AURA ] File write cancelled by user."
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"[ AURA ] Written: {path} ({len(content)} chars)"
    except Exception as e:
        return f"[ AURA ] Write failed: {e}"


def patch_file(path: str, old_str: str, new_str: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"[ AURA ] File not found: {path}"
    content = p.read_text(encoding="utf-8")
    if old_str not in content:
        return f"[ AURA ] patch_file: could not find the target string in {path}."
    patched = content.replace(old_str, new_str, 1)
    approved = confirm_write(path, preview=f"Replacing:\n{old_str[:100]}\n\nWith:\n{new_str[:100]}")
    if not approved:
        return "[ AURA ] Patch cancelled by user."
    p.write_text(patched, encoding="utf-8")
    return f"[ AURA ] Patched: {path}"


def list_dir(path: str = ".") -> str:
    p = Path(path)
    if not p.exists():
        return f"[ AURA ] Path not found: {path}"
    try:
        items = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
        lines = []
        for item in items:
            if item.is_dir():
                lines.append(f"  📁  {item.name}/")
            else:
                size = item.stat().st_size
                size_str = f"{size:,} B" if size < 1024 else f"{size//1024:,} KB"
                lines.append(f"  📄  {item.name}  [{size_str}]")
        return "\n".join(lines) if lines else "[ empty directory ]"
    except Exception as e:
        return f"[ AURA ] list_dir error: {e}"


def delete_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"[ AURA ] File not found: {path}"
    approved = confirm_delete(path)
    if not approved:
        return "[ AURA ] Delete cancelled by user."
    try:
        p.unlink()
        return f"[ AURA ] Deleted: {path}"
    except Exception as e:
        return f"[ AURA ] Delete failed: {e}"
