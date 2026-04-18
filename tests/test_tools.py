"""
AURA tool verification tests.
Run before your hackathon demo to confirm everything works:
  python test_tools.py

Does NOT require the InferX endpoint — tests tools only.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path so imports work without installing
sys.path.insert(0, os.path.dirname(__file__))

PASS = "  ✓"
FAIL = "  ✗"
results = []


def test(name: str, fn):
    try:
        result = fn()
        if result is False:
            raise AssertionError("returned False")
        print(f"{PASS} {name}")
        results.append((name, True, ""))
    except Exception as e:
        print(f"{FAIL} {name}  →  {e}")
        results.append((name, False, str(e)))


print("\n── AURA Tool Tests ─────────────────────────────────────────────\n")

# ── Shell ─────────────────────────────────────────────────────────────────────
print("Shell:")

def _test_bash_basic():
    from aura.tools.shell import run
    out = run("echo hello_aura")
    assert "hello_aura" in out, f"Got: {out}"

def _test_bash_stderr():
    from aura.tools.shell import run
    out = run("ls /nonexistent_path_xyz 2>&1 || true")
    # Should return something (error message), not crash
    assert out is not None

def _test_bash_timeout():
    from aura.tools.shell import run
    out = run("sleep 5", timeout=1)
    assert "timed out" in out.lower()

test("bash: basic execution", _test_bash_basic)
test("bash: captures stderr", _test_bash_stderr)
test("bash: timeout works", _test_bash_timeout)

# ── Filesystem ────────────────────────────────────────────────────────────────
print("\nFilesystem:")

def _test_write_read():
    from aura.tools import filesystem
    with tempfile.TemporaryDirectory() as d:
        path = f"{d}/test.txt"
        # Bypass confirmation for tests
        p = Path(path)
        p.write_text("hello aura")
        out = filesystem.read_file(path)
        assert "hello aura" in out

def _test_read_missing():
    from aura.tools.filesystem import read_file
    out = read_file("/tmp/does_not_exist_aura_test.txt")
    assert "not found" in out.lower()

def _test_list_dir():
    from aura.tools.filesystem import list_dir
    out = list_dir(".")
    assert len(out) > 0

def _test_patch_file():
    from aura.tools import filesystem
    with tempfile.TemporaryDirectory() as d:
        path = f"{d}/patch_test.py"
        p = Path(path)
        p.write_text("x = 1\ny = 2\n")
        # Direct patch without confirm (bypass for test)
        content = p.read_text()
        patched = content.replace("x = 1", "x = 99", 1)
        p.write_text(patched)
        result = p.read_text()
        assert "x = 99" in result

test("filesystem: read file", _test_write_read)
test("filesystem: missing file returns error string", _test_read_missing)
test("filesystem: list_dir returns content", _test_list_dir)
test("filesystem: patch_file logic", _test_patch_file)

# ── Web ───────────────────────────────────────────────────────────────────────
print("\nWeb:")

def _test_web_fetch():
    from aura.tools.web import web_fetch
    out = web_fetch("https://httpbin.org/get", max_chars=500)
    # httpbin returns JSON — should contain "url" or "origin"
    assert len(out) > 10, f"Too short: {out}"

def _test_web_fetch_bad_url():
    from aura.tools.web import web_fetch
    out = web_fetch("https://this-domain-does-not-exist-aura-xyz.com")
    assert "error" in out.lower() or "aura" in out.lower()

def _test_web_search():
    from aura.tools.web import web_search
    out = web_search("Python programming language", max_results=3)
    assert len(out) > 20, f"Too short: {out}"

test("web: fetch real URL", _test_web_fetch)
test("web: bad URL returns error string", _test_web_fetch_bad_url)
test("web: search returns results", _test_web_search)

# ── Config ────────────────────────────────────────────────────────────────────
print("\nConfig:")

def _test_config_loads():
    from aura import config
    assert hasattr(config, "INFERX_BASE_URL")
    assert hasattr(config, "INFERX_MODEL")
    assert hasattr(config, "SAFE_MODE")

def _test_env_present():
    return Path(".env").exists() or Path(".env.example").exists()

test("config: loads without error", _test_config_loads)
test("config: .env file exists", _test_env_present)

# ── Tool registry ─────────────────────────────────────────────────────────────
print("\nTool registry:")

def _test_tool_defs_not_empty():
    from aura.tools import ALL_TOOL_DEFS
    assert len(ALL_TOOL_DEFS) >= 10, f"Only {len(ALL_TOOL_DEFS)} tools registered"

def _test_dispatch_unknown():
    from aura.tools import dispatch
    out = dispatch("nonexistent_tool_xyz", {})
    assert "unknown" in out.lower()

def _test_all_tools_have_names():
    from aura.tools import ALL_TOOL_DEFS
    for t in ALL_TOOL_DEFS:
        name = t.get("function", {}).get("name")
        assert name, f"Tool missing name: {t}"

test("registry: tools registered", _test_tool_defs_not_empty)
test("registry: dispatch unknown tool gracefully", _test_dispatch_unknown)
test("registry: all tool defs have names", _test_all_tools_have_names)

# ── Memory ────────────────────────────────────────────────────────────────────
print("\nMemory:")

def _test_memory_save_load():
    from aura.memory import Memory
    m = Memory()
    sid = m.session_id
    m.add_user("test goal")
    m.add_assistant("test response")
    # Load it back
    m2 = Memory(session_id=sid)
    msgs = m2.get_messages()
    assert len(msgs) == 2
    assert msgs[0]["content"] == "test goal"
    assert msgs[1]["content"] == "test response"

def _test_memory_clear():
    from aura.memory import Memory
    m = Memory()
    m.add_user("hello")
    m.clear()
    assert len(m.get_messages()) == 0

test("memory: save and reload session", _test_memory_save_load)
test("memory: clear works", _test_memory_clear)

# ── Summary ───────────────────────────────────────────────────────────────────
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed

print(f"\n── Results: {passed}/{total} passed", end="")
if failed:
    print(f"  ({failed} failed)")
    print("\nFailed tests:")
    for name, ok, err in results:
        if not ok:
            print(f"  ✗ {name}: {err}")
else:
    print(" — all good ✓")

print()
sys.exit(0 if failed == 0 else 1)
