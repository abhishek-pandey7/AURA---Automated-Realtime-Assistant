import json
import os
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich import box

from aura.config import INFERX_BASE_URL, INFERX_API_KEY, INFERX_MODEL
from aura.memory import Memory
from aura.tools import ALL_TOOL_DEFS, dispatch

console = Console()

_client = OpenAI(base_url=INFERX_BASE_URL, api_key=INFERX_API_KEY)

SYSTEM_PROMPT = """You are AURA (Automated Realtime Assistant), an autonomous CLI agent running on the user's machine.
Your job is to complete tasks by using tools — not just describe what to do.

Current working directory: {cwd}

Core rules:
1. Always prefer DOING over EXPLAINING. Use tools immediately.
2. After each tool result, read the output carefully and decide the next action.
3. If a command fails, read stderr, identify the cause, fix it, and retry automatically.
4. For code: write it, run it, check the output, fix any errors — all without asking the user.
5. When a task is fully complete, give a short plain-English summary of what was done.
6. Never ask the user for information you can discover yourself with tools.
7. Only ask the user if you genuinely need a decision only they can make.

You have access to: bash, file operations, web tools, and raw Desktop UI control.

CRITICAL DESKTOP RULES:
- Web Navigation: To use the internet on desktop, press Windows key, open 'Chrome' (or use an open window), press `Ctrl + T` to open a New Tab, and type the URL.
- For all other clicks: Use `desktop_find_text` first to scan the screen. Use `desktop_click` on the returned coordinates.
- If OCR fails, fall back to pure keyboard navigation.
"""


def run_agent(goal: str, memory: Memory, max_iterations: int = 30) -> str:
    """
    Core observe → think → act loop.
    Runs until the LLM stops calling tools (task done) or max_iterations hit.
    Returns the final summary string.
    """
    cwd = os.getcwd()
    system = SYSTEM_PROMPT.format(cwd=cwd)

    memory.add_user(goal)

    for iteration in range(max_iterations):

        # ── LLM call ─────────────────────────────────────────────────────
        with console.status("[bold cyan]AURA is thinking...[/bold cyan]", spinner="dots"):
            response = None
            last_error = None
            for p_retry in range(3):
                try:
                    response = _client.chat.completions.create(
                        model=INFERX_MODEL,
                        max_tokens=4096,
                        messages=[
                            {"role": "system", "content": system},
                            *memory.get_messages(),
                        ],
                        tools=ALL_TOOL_DEFS,
                        tool_choice="auto",
                        temperature=0.3,
                    )
                    break  # Success
                except Exception as e:
                    import time
                    err_str = str(e)
                    last_error = e
                    if "502" in err_str or "500" in err_str or "503" in err_str:
                        console.print(f"  [dim]Proxy glitch ({e}) — retrying ({p_retry+1}/3)...[/dim]")
                        time.sleep(2)
                        continue
                    else:
                        break  # Break for 4xx errors
                        
            if response is None:
                console.print(f"[bold red]LLM error:[/bold red] {last_error}")
                return f"Agent stopped: {last_error}"

        choice = response.choices[0]
        message = choice.message

        # ── No tool calls → task complete ────────────────────────────────
        if not message.tool_calls:
            final = message.content or "[ AURA ] Task complete."

            # Save to memory
            memory.add_assistant(final)

            console.print(Panel(
                final,
                title="[bold green]✓ AURA[/bold green]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2),
            ))
            return final

        # ── Save assistant message with tool calls to memory ─────────────
        # Must be stored as the raw dict format the API expects back
        assistant_msg = {
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,  # stays as JSON string
                    },
                }
                for tc in message.tool_calls
            ],
        }
        memory.messages.append(assistant_msg)
        memory._save()

        # ── Execute each tool call ────────────────────────────────────────
        tool_result_contents = []

        for tc in message.tool_calls:
            tool_name = tc.function.name

            # Parse arguments — handle malformed JSON gracefully
            try:
                tool_inputs = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                # Some models wrap JSON in markdown fences
                raw = tc.function.arguments.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:].strip()
                try:
                    tool_inputs = json.loads(raw)
                except Exception:
                    tool_inputs = {}

            _print_tool_call(tool_name, tool_inputs)
            result = dispatch(tool_name, tool_inputs)
            _print_tool_result(tool_name, result)

            tool_result_contents.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": result,
            })

        for item in tool_result_contents:
            raw_content = item["content"]
            image_url = None
            
            # Intercept images passed from the desktop_analyze_screen tool
            if "[ IMAGE_BASE64: " in raw_content:
                start_i = raw_content.find("[ IMAGE_BASE64: ") + len("[ IMAGE_BASE64: ")
                end_i = raw_content.find(" ]", start_i)
                if end_i != -1:
                    image_url = raw_content[start_i:end_i].strip()
                    # Strip the raw base64 from the tool message string to prevent bloat
                    raw_content = raw_content[:start_i - len("[ IMAGE_BASE64: ")] + "[ screenshot attached in next message ]" + raw_content[end_i+2:]
            
            memory.messages.append({
                "role": "tool",
                "tool_call_id": item["tool_use_id"],
                "content": raw_content,
            })
            
            if image_url:
                # Add the actual image as a subsequent user message (OpenAI standard)
                memory.messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Screenshot captured:"},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                })
                
        memory._save()

    console.print("[bold yellow]⚠ Max iterations reached.[/bold yellow]")
    return "Max iterations reached. Task may be incomplete."


def _print_tool_call(name: str, inputs: dict):
    color_map = {
        "bash": "yellow",
        "write_file": "cyan",
        "patch_file": "cyan",
        "read_file": "blue",
        "list_dir": "blue",
        "delete_file": "red",
        "web_search": "magenta",
        "web_fetch": "magenta",
        "browser_navigate": "green",
        "browser_click": "green",
        "browser_fill": "green",
        "browser_get_text": "green",
        "browser_screenshot": "green",
        "desktop_click": "magenta",
        "desktop_type": "magenta",
        "desktop_press": "magenta",
        "desktop_get_position": "magenta",
    }
    color = color_map.get(name, "white")

    if name == "bash":
        detail = f"$ {inputs.get('command', '')}"
    elif name in ("write_file", "read_file", "patch_file", "delete_file"):
        detail = inputs.get("path", "")
    elif name == "web_search":
        detail = f"🔍 {inputs.get('query', '')}"
    elif name == "web_fetch":
        detail = f"🌐 {inputs.get('url', '')}"
    elif name.startswith("browser_"):
        detail = (
            inputs.get("url")
            or inputs.get("selector")
            or inputs.get("path")
            or ""
        )
    elif name.startswith("desktop_"):
        detail = (
            inputs.get("text")
            or "+".join(inputs.get("keys", []))
            or f"({inputs.get('x', '')}, {inputs.get('y', '')})"
            or inputs.get("reason")
            or ""
        )
    else:
        detail = json.dumps(inputs)[:80]

    console.print(f"  [bold {color}]▶ {name}[/bold {color}]  [dim]{detail}[/dim]")


def _print_tool_result(name: str, result: str):
    if not result or result.strip() == "[ no output ]":
        console.print("  [dim]← (no output)[/dim]\n")
        return

    lines = result.strip().splitlines()
    preview = "\n".join(lines[:25])
    truncated = len(lines) > 25

    # Syntax highlight bash output that looks like Python
    if name == "bash" and any(
        kw in result for kw in ["def ", "class ", "import ", "Traceback", "Error:"]
    ):
        console.print(Syntax(preview, "python", theme="monokai", line_numbers=False))
    else:
        # Indent each line for visual separation
        indented = "\n".join(f"  {l}" for l in preview.splitlines())
        console.print(f"[dim]  ←[/dim]\n{indented}")

    if truncated:
        console.print(f"  [dim]  ... ({len(lines) - 25} more lines hidden)[/dim]")

    console.print()
