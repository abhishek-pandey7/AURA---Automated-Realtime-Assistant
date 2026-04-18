# Changelog

All notable changes to AURA will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.1.0] — 2026-04-19

### Added
- Interactive REPL (`aura run`) with ASCII welcome screen
- Single-goal non-interactive mode (`aura run "goal"`)
- Upfront task planner — breaks goals into ordered subtasks
- Core observe→think→act agent loop with tool calling
- **Shell tool** — bash with timeout and stderr capture
- **Filesystem tools** — read, write, patch, list, delete
- **Web tools** — search (no API key) and fetch with HTML-to-text
- **Browser tools** — headless Playwright (navigate, click, fill, screenshot)
- Session memory — persist and resume past conversations
- Safe mode — Y/N confirmation before writes, shell, and deletes
- `/help`, `/clear`, `/sessions`, `/resume`, `/tools`, `/cwd`, `/exit` REPL commands
- `install.sh` one-shot setup script
