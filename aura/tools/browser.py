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
            
            user_data_dir = r"C:\Users\Abhishek Pandey\AppData\Local\Google\Chrome\User Data"
            
            try:
                # 1) Try to connect via CDP if they launched Chrome with remote debugging
                self._browser = self._playwright.chromium.connect_over_cdp("http://localhost:9222")
                context = self._browser.contexts[0] if self._browser.contexts else self._browser
                self._page = context.pages[0] if getattr(context, 'pages', []) else context.new_page()
                print("\n[ AURA ] Connected to existing Chrome via remote debugging.")
                
            except Exception:
                try:
                    # 2) Try to launch their persistent Google Chrome profile
                    self._browser_context = self._playwright.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        channel="chrome",
                        headless=False,
                        args=["--start-maximized"]
                    )
                    self._browser = None # Using context instead
                    self._page = self._browser_context.pages[0] if self._browser_context.pages else self._browser_context.new_page()
                    print("\n[ AURA ] Launched your existing Chrome profile.")
                except Exception as e:
                    print("\n[ AURA ] Could not launch your real Chrome profile (is Chrome already open?)")
                    print("[ AURA ] Please completely close your Google Chrome browser and try again, or launch it with --remote-debugging-port=9222.")
                    print("[ AURA ] Falling back to a clean isolated Chromium window...")
                    # 3) Fallback
                    self._browser = self._playwright.chromium.launch(headless=False)
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
            # Try CSS selector first, then visible text (fail fast with 3s timeout)
            try:
                self._page.click(selector, timeout=3000)
            except Exception:
                self._page.get_by_text(selector).first.click(timeout=3000)
            return f"[ AURA ] Clicked: {selector}"
        except Exception as e:
            return f"[ AURA ] Click failed: {e}"

    def fill(self, selector: str, value: str) -> str:
        if not confirm_browser("fill input", f"{selector} = '{value}'"):
            return "[ AURA ] Browser action cancelled."
        self._ensure_started()
        try:
            # Try CSS selector with fast timeout
            try:
                self._page.fill(selector, value, timeout=3000)
            except Exception:
                # Fallback to placeholder text
                self._page.get_by_placeholder(selector).first.fill(value, timeout=3000)
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
        if hasattr(self, '_browser_context') and self._browser_context:
            self._browser_context.close()
        elif self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self._page = None
        self._browser = None
        if hasattr(self, '_browser_context'):
            self._browser_context = None
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
