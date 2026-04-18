from aura.confirm import confirm_browser

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "browser_navigate",
            "description": "Open a URL in a headless browser. Use before other browser actions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to navigate to."},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click",
            "description": "Click an element on the current browser page by CSS selector or text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector or visible text of element."},
                },
                "required": ["selector"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_fill",
            "description": "Fill a text input field on the current page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector for the input field."},
                    "value": {"type": "string", "description": "Text to type into the field."},
                },
                "required": ["selector", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_get_text",
            "description": "Extract all visible text from the current browser page.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_screenshot",
            "description": "Take a screenshot of the current browser page and save it to a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to save screenshot (PNG)."},
                },
                "required": ["path"],
            },
        },
    },
]


class BrowserSession:
    """Manages a single persistent headless browser session."""

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._page = None

    def _ensure_started(self):
        if self._page is None:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            self._page = self._browser.new_page()

    def navigate(self, url: str) -> str:
        if not confirm_browser("navigate", url):
            return "[ AURA ] Browser action cancelled."
        self._ensure_started()
        try:
            self._page.goto(url, wait_until="domcontentloaded", timeout=15000)
            return f"[ AURA ] Navigated to: {url} — title: {self._page.title()}"
        except Exception as e:
            return f"[ AURA ] Navigate failed: {e}"

    def click(self, selector: str) -> str:
        if not confirm_browser("click", selector):
            return "[ AURA ] Browser action cancelled."
        self._ensure_started()
        try:
            # Try CSS selector first, then visible text
            try:
                self._page.click(selector, timeout=5000)
            except Exception:
                self._page.get_by_text(selector).first.click(timeout=5000)
            return f"[ AURA ] Clicked: {selector}"
        except Exception as e:
            return f"[ AURA ] Click failed: {e}"

    def fill(self, selector: str, value: str) -> str:
        if not confirm_browser("fill input", f"{selector} = '{value}'"):
            return "[ AURA ] Browser action cancelled."
        self._ensure_started()
        try:
            self._page.fill(selector, value)
            return f"[ AURA ] Filled '{selector}' with value."
        except Exception as e:
            return f"[ AURA ] Fill failed: {e}"

    def get_text(self) -> str:
        self._ensure_started()
        try:
            text = self._page.inner_text("body")
            return text[:4000] + ("..." if len(text) > 4000 else "")
        except Exception as e:
            return f"[ AURA ] get_text failed: {e}"

    def screenshot(self, path: str) -> str:
        self._ensure_started()
        try:
            self._page.screenshot(path=path, full_page=True)
            return f"[ AURA ] Screenshot saved: {path}"
        except Exception as e:
            return f"[ AURA ] Screenshot failed: {e}"

    def close(self):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self._page = None
        self._browser = None
        self._playwright = None


# Module-level singleton — one browser per AURA session
_session: BrowserSession | None = None


def _get_session() -> BrowserSession:
    global _session
    if _session is None:
        _session = BrowserSession()
    return _session


# ── Public tool functions ─────────────────────────────────────────────────────

def browser_navigate(url: str) -> str:
    return _get_session().navigate(url)

def browser_click(selector: str) -> str:
    return _get_session().click(selector)

def browser_fill(selector: str, value: str) -> str:
    return _get_session().fill(selector, value)

def browser_get_text() -> str:
    return _get_session().get_text()

def browser_screenshot(path: str) -> str:
    return _get_session().screenshot(path)

def close_browser():
    if _session:
        _session.close()
