"""
InferX endpoint smoke test.
Run this the MOMENT they give you the endpoint URL and key:
  python test_endpoint.py

Tests:
  1. Basic completion
  2. Tool/function calling
  3. JSON output mode
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

BASE_URL = os.getenv("INFERX_BASE_URL", "")
API_KEY  = os.getenv("INFERX_API_KEY", "")
MODEL    = os.getenv("INFERX_MODEL", "gemma-4-31b")

print(f"\n── InferX Endpoint Test ────────────────────────────────────────")
print(f"  URL:   {BASE_URL or '(not set)'}")
print(f"  Model: {MODEL}")
print()

if not BASE_URL or not API_KEY:
    print("  ✗ INFERX_BASE_URL or INFERX_API_KEY not set in .env")
    print("    Edit .env and run again.")
    sys.exit(1)

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


# ── Test 1: Basic completion ──────────────────────────────────────────────────
print("Test 1: Basic completion")
try:
    r = client.chat.completions.create(
        model=MODEL,
        max_tokens=64,
        messages=[{"role": "user", "content": "Reply with exactly: AURA_OK"}],
    )
    reply = r.choices[0].message.content or ""
    if "AURA_OK" in reply:
        print(f"  ✓ Got expected response")
    else:
        print(f"  ⚠ Got response but content unexpected: {reply[:100]}")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)


# ── Test 2: Tool/function calling ─────────────────────────────────────────────
print("\nTest 2: Tool/function calling")
DUMMY_TOOL = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
            },
            "required": ["city"],
        },
    },
}]

try:
    r = client.chat.completions.create(
        model=MODEL,
        max_tokens=256,
        messages=[{"role": "user", "content": "What's the weather in Mumbai?"}],
        tools=DUMMY_TOOL,
        tool_choice="auto",
    )
    msg = r.choices[0].message
    if msg.tool_calls:
        tc = msg.tool_calls[0]
        args = json.loads(tc.function.arguments)
        print(f"  ✓ Tool called: {tc.function.name}({args})")
    else:
        print(f"  ⚠ No tool call made — model replied with text instead.")
        print(f"    This may cause issues. Response: {msg.content[:100]}")
        print(f"    Try adding to system prompt: 'You MUST use tools.'")
except Exception as e:
    print(f"  ✗ Failed: {e}")


# ── Test 3: JSON output ───────────────────────────────────────────────────────
print("\nTest 3: JSON output (for planner)")
try:
    r = client.chat.completions.create(
        model=MODEL,
        max_tokens=256,
        messages=[
            {
                "role": "system",
                "content": "Return ONLY valid JSON, no markdown, no explanation.",
            },
            {
                "role": "user",
                "content": 'Return: {"tasks": ["step 1", "step 2", "step 3"]}',
            },
        ],
        temperature=0.1,
    )
    raw = r.choices[0].message.content or ""
    # Strip markdown fences if present
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:].strip()
    data = json.loads(clean)
    tasks = data.get("tasks", [])
    if tasks:
        print(f"  ✓ JSON output works. Got {len(tasks)} tasks.")
    else:
        print(f"  ⚠ Parsed JSON but no 'tasks' key. Raw: {raw[:100]}")
except json.JSONDecodeError as e:
    print(f"  ⚠ JSON parse failed: {e}")
    print(f"    Raw output: {raw[:200]}")
    print(f"    Planner will fall back to treating goal as single task — OK for demo.")
except Exception as e:
    print(f"  ✗ Failed: {e}")


print("\n── Done. If tests 1 and 2 pass, AURA is ready to run. ──────────\n")
