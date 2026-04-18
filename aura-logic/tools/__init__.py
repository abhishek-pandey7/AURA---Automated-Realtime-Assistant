from aura.tools import shell, filesystem, web, browser

ALL_TOOL_DEFS = (
    [shell.TOOL_DEF]
    + filesystem.TOOL_DEFS
    + web.TOOL_DEFS
    + browser.TOOL_DEFS
)

def dispatch(name: str, inputs: dict) -> str:
    match name:
        case "bash":
            return shell.run(inputs["command"], inputs.get("timeout", 60))
        case "read_file":
            return filesystem.read_file(inputs["path"])
        case "write_file":
            return filesystem.write_file(inputs["path"], inputs["content"])
        case "patch_file":
            return filesystem.patch_file(inputs["path"], inputs["old_str"], inputs["new_str"])
        case "list_dir":
            return filesystem.list_dir(inputs.get("path", "."))
        case "delete_file":
            return filesystem.delete_file(inputs["path"])
        case "web_fetch":
            return web.web_fetch(inputs["url"], inputs.get("max_chars", 4000))
        case "web_search":
            return web.web_search(inputs["query"], inputs.get("max_results", 5))
        case "browser_navigate":
            return browser.browser_navigate(inputs["url"])
        case "browser_click":
            return browser.browser_click(inputs["selector"])
        case "browser_fill":
            return browser.browser_fill(inputs["selector"], inputs["value"])
        case "browser_get_text":
            return browser.browser_get_text()
        case "browser_screenshot":
            return browser.browser_screenshot(inputs["path"])
        case _:
            return f"[ AURA ] Unknown tool: {name}"
