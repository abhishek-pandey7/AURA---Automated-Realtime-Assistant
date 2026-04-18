import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich import box
from rich.rule import Rule

from aura.config import VERSION
from aura.memory import Memory
from aura.planner import plan
from aura import agent

console = Console()

# ── ASCII art logo ────────────────────────────────────────────────────────────
LOGO = r"""
     ██████╗ ██╗   ██╗██████╗  █████╗ 
    ██╔══██╗██║   ██║██╔══██╗██╔══██╗
    ███████║██║   ██║██████╔╝███████║
    ██╔══██║██║   ██║██╔══██╗██╔══██║
    ██║  ██║╚██████╔╝██║  ██║██║  ██║
    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
"""

TAGLINE = "Automated  Realtime  Assistant"

HELP_TEXT = """
[bold cyan]Commands:[/bold cyan]
  [bold]/voice[/bold]      Speak a command using your microphone
  [bold]/help[/bold]       Show this help
  [bold]/clear[/bold]      Clear conversation history
  [bold]/sessions[/bold]   List past sessions
  [bold]/resume[/bold]     Resume a previous session
  [bold]/tools[/bold]      List available tools
  [bold]/cwd[/bold]        Show current working directory
  [bold]/exit[/bold]       Exit AURA

[bold cyan]Usage:[/bold cyan]
  Just type your goal in plain English and press Enter.
  AURA will plan, execute, and report back autonomously.

[bold cyan]Examples:[/bold cyan]
  › Build a Flask REST API with /ping and /echo endpoints
  › Find all TODO comments in this codebase and list them
  › Search for the latest Python asyncio docs and summarize them
  › Create a test suite for app.py and fix any failures
"""

TOOLS_TEXT = """
[bold]Shell[/bold]
  bash              Run any shell command

[bold]Filesystem[/bold]  
  read_file         Read a file's contents
  write_file        Create or overwrite a file
  patch_file        Surgically edit a specific part of a file
  list_dir          List directory contents
  delete_file       Delete a file (always asks confirmation)

[bold]Web[/bold]
  web_search        Search the web (no API key needed)
  web_fetch         Read any webpage as clean text

[bold]Browser[/bold]
  browser_navigate  Open a URL in headless browser
  browser_click     Click an element by selector or text
  browser_fill      Fill a form field
  browser_get_text  Extract all text from current page
  browser_screenshot  Save a screenshot
"""


def print_welcome():
    console.clear()
    console.print()
    console.print(Align.center(Text(LOGO, style="bold cyan")))
    console.print(Align.center(Text(TAGLINE, style="bold white")))
    console.print(Align.center(Text(f"v{VERSION}  ·  type /help for commands", style="dim")))
    console.print()
    console.print(Rule(style="cyan dim"))
    console.print()
    cwd = os.getcwd()
    console.print(f"  [dim]Working directory:[/dim] [bold]{cwd}[/bold]")
    console.print(f"  [dim]AURA has full access to files in this directory.[/dim]")
    console.print()


def print_help():
    console.print(Panel(HELP_TEXT, title="[bold cyan]AURA Help[/bold cyan]",
                        border_style="cyan", box=box.ROUNDED))


def print_tools():
    console.print(Panel(TOOLS_TEXT, title="[bold cyan]Available Tools[/bold cyan]",
                        border_style="cyan", box=box.ROUNDED))


def print_sessions():
    sessions = Memory.list_sessions()
    if not sessions:
        console.print("  [dim]No past sessions found.[/dim]")
        return

    table = Table(box=box.SIMPLE, header_style="bold cyan", show_header=True)
    table.add_column("ID", style="dim", width=18)
    table.add_column("Started")
    table.add_column("Directory")
    table.add_column("Messages", justify="right")

    for s in sessions:
        table.add_row(s["id"], s["started"][:19], s["cwd"], str(s["messages"]))

    console.print(table)


def handle_command(cmd: str, memory: Memory) -> tuple[bool, Memory]:
    """
    Handle slash commands. Returns (should_continue, memory).
    """
    cmd = cmd.strip().lower()

    if cmd == "/help":
        print_help()

    elif cmd == "/clear":
        memory.clear()
        console.print("  [bold green]✓[/bold green] Conversation cleared.")

    elif cmd == "/sessions":
        print_sessions()

    elif cmd == "/resume":
        print_sessions()
        session_id = console.input("\n  Enter session ID to resume › ").strip()
        try:
            memory = Memory(session_id=session_id)
            console.print(f"  [bold green]✓[/bold green] Resumed session {session_id}")
        except FileNotFoundError:
            console.print(f"  [bold red]✗[/bold red] Session not found.")

    elif cmd == "/tools":
        print_tools()

    elif cmd == "/cwd":
        console.print(f"  [bold]{os.getcwd()}[/bold]")

    elif cmd in ("/exit", "/quit", "/q"):
        console.print("\n  [bold cyan]Goodbye. AURA signing off.[/bold cyan]\n")
        sys.exit(0)

    else:
        console.print(f"  [dim]Unknown command: {cmd}. Type /help for help.[/dim]")

    return True, memory


def capture_voice() -> str:
    import speech_recognition as sr
    r = sr.Recognizer()
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True
    r.pause_threshold = 1.0

    try:
        with sr.Microphone() as source:
            console.print("\n[bold green]🎤 VOICE MODE[/bold green]")
            console.print("[cyan]Adjusting for background noise...[/cyan]")
            r.adjust_for_ambient_noise(source, duration=1)
            console.print("[cyan]Listening... Speak now.[/cyan]")
            audio = r.listen(source, timeout=10, phrase_time_limit=15)
        
        console.print("[yellow]Transcribing...[/yellow]")
        text = r.recognize_google(audio).strip()
        if not text:
            console.print("[red]No speech detected.[/red]")
            return ""
            
        console.print(f"[bold green]You said:[/bold green] {text}\n")
        return text
    except Exception as e:
        console.print(f"[red]Voice capture failed:[/red] {e}")
        return ""

def run_repl():
    """
    Main REPL loop. Prints welcome, accepts user input, runs agent.
    """
    print_welcome()
    memory = Memory()

    while True:
        try:
            console.print()
            user_input = console.input("[bold cyan]›[/bold cyan] ").strip()

            if not user_input:
                continue

            # Slash commands
            if user_input.startswith("/"):
                if user_input.lower() == "/voice":
                    user_input = capture_voice()
                    if not user_input:
                        continue
                else:
                    _, memory = handle_command(user_input, memory)
                    continue

            # ── Goal received — plan then execute ─────────────────────────
            console.print()
            cwd = os.getcwd()

            # Step 1: Plan
            with console.status("[bold cyan]AURA is planning...[/bold cyan]", spinner="star"):
                tasks = plan(user_input, cwd)

            # Print the plan
            console.print(Panel(
                "\n".join(f"  [bold cyan]{i+1}.[/bold cyan] {t}" for i, t in enumerate(tasks)),
                title="[bold cyan]◆ Plan[/bold cyan]",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(0, 1),
            ))
            console.print()

            # Step 2: Execute each subtask
            for i, task in enumerate(tasks):
                if len(tasks) > 1:
                    console.print(Rule(
                        f"[bold]Task {i+1}/{len(tasks)}:[/bold] {task[:60]}",
                        style="cyan dim",
                    ))
                    console.print()

                agent.run_agent(task, memory)

            # Done
            console.print()
            console.print(Rule("[bold green]✓ All tasks complete[/bold green]", style="green dim"))

        except KeyboardInterrupt:
            console.print("\n\n  [dim]Interrupted. Type /exit to quit.[/dim]")
            continue
        except EOFError:
            console.print("\n  [bold cyan]Goodbye.[/bold cyan]\n")
            sys.exit(0)
