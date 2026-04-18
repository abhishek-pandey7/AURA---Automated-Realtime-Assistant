# AURA — Automated Realtime Assistant

> A CLI-based autonomous AI agent that plans, executes, and adapts — powered by open-weight LLMs via an OpenAI-compatible endpoint.

## What it does

You type a goal in plain English. AURA breaks it into steps, executes them using tools (shell, files, web, browser, desktop), reads the results, fixes errors, and reports back — without you doing anything else.

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
git clone https://github.com/your-username/aura
cd aura
cp .env.example .env
# Edit .env with your endpoint URL and API key
```

### macOS / Linux

```bash
bash install.sh
source .venv/bin/activate
aura run
```

### Windows

```bat
install.bat
.venv\Scripts\activate
aura run
```

### Manual install

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
playwright install chromium      # optional — for browser tools
```

## Platform Notes

### macOS (Apple Silicon & Intel)

`pyaudio` and `SpeechRecognition` require native system libraries. The `install.sh` script handles these automatically. If you install manually:

```bash
# Required for /voice command
brew install portaudio flac

pip install -e .

# Fix SpeechRecognition's bundled flac binary on Apple Silicon
# (it ships an Intel x86 binary that won't run on arm64)
FLAC_DST=".venv/lib/$(python3 -c 'import sys; print(f"python{sys.version_info.major}.{sys.version_info.minor}")')/site-packages/speech_recognition/flac-mac"
cp /opt/homebrew/bin/flac "$FLAC_DST"
```

### Windows

All dependencies install via pip. If `pyaudio` fails (no pre-built wheel):

```bat
pip install pipwin
pipwin install pyaudio
```

The `desktop_find_text` tool uses Windows OCR (`winsdk`) and is Windows-only. All other tools work cross-platform.

## Configuration

Copy `.env.example` to `.env` and fill in your values:

| Variable | Description | Default |
|---|---|---|
| `INFERX_BASE_URL` | OpenAI-compatible API base URL | `https://api.openai.com/v1` |
| `INFERX_API_KEY` | API key | *(required)* |
| `INFERX_MODEL` | Model name | `gemma-4-31b` |
| `AURA_SAFE_MODE` | Prompt before writes/shell/delete | `true` |

## Commands

| Command | Description |
|---|---|
| `aura run` | Start interactive session |
| `aura run "goal"` | Run one goal and exit |
| `aura version` | Show version |

Inside the REPL:

| Command | Description |
|---|---|
| `/voice` | Speak a command using your microphone |
| `/help` | Show help |
| `/clear` | Clear conversation |
| `/sessions` | List past sessions |
| `/resume` | Resume a saved session |
| `/tools` | List all tools |
| `/cwd` | Show current working directory |
| `/exit` | Quit |

## How it differs from Claude Code / Codex

| Feature | Claude Code | AURA |
|---|---|---|
| LLM backend | Anthropic (closed) | Any OpenAI-compatible endpoint |
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
    ├── shell.py        bash / cmd execution
    ├── filesystem.py   read / write / patch / delete
    ├── web.py          web search + fetch (no API)
    ├── browser.py      headless Playwright
    └── desktop.py      mouse, keyboard, screen capture, OCR (Windows)
```

## Testing

```bash
# Verify tools work (no API key needed)
python tests/test_tools.py

# Smoke-test your API endpoint
python tests/test_endpoint.py
```

## Dependencies

| Package | Purpose | Platform |
|---|---|---|
| [openai](https://github.com/openai/openai-python) | OpenAI-compatible API client | All |
| [rich](https://github.com/Textualize/rich) | Terminal UI, colors, panels, spinners | All |
| [requests](https://github.com/psf/requests) | HTTP client for web fetch/search | All |
| [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup) | HTML parsing for web scraping | All |
| [playwright](https://github.com/microsoft/playwright-python) | Headless browser automation | All |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | `.env` config loading | All |
| [PyAutoGUI](https://github.com/asweigart/pyautogui) | Mouse/keyboard desktop control | All |
| [Pillow](https://github.com/python-pillow/Pillow) | Image processing for screenshots | All |
| [SpeechRecognition](https://github.com/Uberi/speech_recognition) | Voice input via microphone | All (needs portaudio) |
| [pyaudio](https://people.csail.mit.edu/hubert/pyaudio/) | Audio capture for voice mode | All (needs brew install portaudio on Mac) |
| [pyttsx3](https://github.com/nateshmbhat/pyttsx3) | Text-to-speech output | All |
| [winsdk](https://github.com/pywinrt/python-winsdk) | Windows OCR for `desktop_find_text` | Windows only |

## License

MIT
