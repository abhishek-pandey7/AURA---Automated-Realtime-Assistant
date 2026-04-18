# AURA — Automated Realtime Assistant

> A CLI-based autonomous AI agent that plans, executes, and adapts — powered by Gemma 4 31B via InferX.

## What it does

You type a goal in plain English. AURA breaks it into steps, executes them using tools (shell, files, web, browser), reads the results, fixes errors, and reports back — without you doing anything else.

```
$ aura run
     ██████╗ ██╗   ██╗██████╗  █████╗ 
    ...

› Build a Flask REST API with /users endpoint, write tests, run them, fix any failures

◆ Plan
  1. Create project directory and app.py with Flask
  2. Implement /users GET and POST endpoints
  3. Write pytest tests in test_app.py
  4. Run tests and fix any failures

▶ bash  $ mkdir flask_app && cd flask_app
▶ write_file  flask_app/app.py
▶ write_file  flask_app/test_app.py
▶ bash  $ cd flask_app && pytest -v
▶ patch_file  flask_app/app.py   ← auto-fixing failure
▶ bash  $ pytest -v
✓ All tasks complete
```

## Quickstart

```bash
git clone <repo>
cd aura
cp .env.example .env
# edit .env with your InferX endpoint and key

pip install -e .
playwright install chromium   # optional, for browser tools

aura run
```

## Commands

| Command | Description |
|---|---|
| `aura run` | Start interactive session |
| `aura run "goal"` | Run one goal and exit |
| `aura version` | Show version |

Inside the REPL:

| Command | Description |
|---|---|
| `/help` | Show help |
| `/clear` | Clear conversation |
| `/sessions` | List past sessions |
| `/resume` | Resume a saved session |
| `/tools` | List all tools |
| `/cwd` | Show working directory |
| `/exit` | Quit |

## How it differs from Claude Code / Codex

| Feature | Claude Code | AURA |
|---|---|---|
| LLM backend | Anthropic (closed) | Gemma 4 31B via InferX (open-weight) |
| Upfront task planning | No — reactive | Yes — breaks goal into subtasks first |
| Browser automation | No | Yes — headless Playwright |
| Session persistence | No | Yes — resume sessions from disk |
| Web search | No | Yes — no API key needed |
| Confirmation prompts | Yes | Yes — Y/N for writes, deletes, shell |
| Self-hostable | No | Yes |

## Architecture

```
aura/
├── cli.py          Entry point — `aura run` command
├── ui.py           Welcome screen + REPL loop
├── agent.py        Core observe→think→act loop
├── planner.py      Goal → ordered subtask list
├── memory.py       Session persistence
├── confirm.py      Y/N prompts for dangerous actions
├── config.py       Environment config
└── tools/
    ├── shell.py        bash execution
    ├── filesystem.py   read / write / patch / delete
    ├── web.py          web search + fetch (no API)
    └── browser.py      headless Playwright
```

## Open-source repositories used

| Package | Repository | Purpose |
|---|---|---|
| openai | https://github.com/openai/openai-python | OpenAI-compatible client for InferX |
| rich | https://github.com/Textualize/rich | Terminal UI, colors, panels, spinners |
| requests | https://github.com/psf/requests | HTTP client for web fetch/search |
| beautifulsoup4 | https://www.crummy.com/software/BeautifulSoup | HTML parsing for web scraping |
| playwright | https://github.com/microsoft/playwright-python | Headless browser automation |
| python-dotenv | https://github.com/theskumar/python-dotenv | .env config loading |

## Judging criteria coverage

- **Functional Prototype** — working CLI, `aura run` starts immediately
- **Autonomous Reasoning** — planner breaks goals, agent fixes errors without user input
- **Tool Integration** — 13 tools across shell, filesystem, web, browser
- **Innovation & Usability** — arcade welcome, session memory, open-weight model, no external APIs
