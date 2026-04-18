import sys
import os
from aura.config import VERSION


USAGE = """
AURA — Automated Realtime Assistant

Usage:
  aura run              Start an interactive AURA session in the current directory
  aura run "<goal>"     Run a single goal non-interactively and exit
  aura version          Show version
  aura help             Show this help

Examples:
  aura run
  aura run "create a Flask app with a /ping endpoint and run it"
"""


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("help", "--help", "-h"):
        print(USAGE)
        return

    if args[0] in ("version", "--version", "-v"):
        print(f"AURA v{VERSION}")
        return

    if args[0] == "run":
        # Inline goal passed directly: aura run "do something"
        if len(args) > 1:
            goal = " ".join(args[1:])
            _run_single(goal)
        else:
            # Interactive REPL mode
            _run_interactive()
        return

    # Anything else — treat as a goal directly
    # e.g. someone accidentally types: aura "build me a thing"
    goal = " ".join(args)
    _run_single(goal)


def _run_interactive():
    """Full interactive REPL with welcome screen."""
    from aura.ui import run_repl
    run_repl()


def _run_single(goal: str):
    """
    Non-interactive: run one goal and exit.
    Used for scripting: aura run "do X"
    """
    from rich.console import Console
    from aura.memory import Memory
    from aura.planner import plan
    from aura import agent

    console = Console()
    memory = Memory()
    cwd = os.getcwd()

    console.print(f"\n[bold cyan]AURA[/bold cyan] [dim]v{VERSION}[/dim]\n")
    console.print(f"[dim]Goal:[/dim] {goal}\n")

    tasks = plan(goal, cwd)
    for i, task in enumerate(tasks):
        console.print(f"[cyan]Task {i+1}/{len(tasks)}:[/cyan] {task}")

    console.print()
    for task in tasks:
        agent.run_agent(task, memory)

    # Speak when done
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say("Task completed successfully, Abhishek.")
        engine.runAndWait()
    except Exception:
        pass


if __name__ == "__main__":
    main()
