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

You have access to: bash, file read/write/patch/delete, web search, web fetch, and browser automation.
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
            except Exception as e:
                console.print(f"[bold red]LLM error:[/bold red] {e}")
                return f"Agent stopped: {e}"

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

        # Feed all tool results back as a single user message
        # (OpenAI format: role=tool per call)
        tool_messages = [
            {
                "role": "tool",
                "tool_call_id": item["tool_use_id"],
                "content": item["content"],
            }
            for item in tool_result_contents
        ]
        for tm in tool_messages:
            memory.messages.append(tm)
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
