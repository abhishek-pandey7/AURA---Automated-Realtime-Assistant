from aura.tools import shell, filesystem, web, desktop

ALL_TOOL_DEFS = (
    [shell.TOOL_DEF]
    + filesystem.TOOL_DEFS
    + web.TOOL_DEFS
    + desktop.TOOL_DEFS
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
        case "desktop_click":
            return desktop.desktop_click(inputs["x"], inputs["y"], inputs.get("clicks", 1), inputs.get("button", "left"))
        case "desktop_move_mouse":
            return desktop.desktop_move_mouse(inputs["x"], inputs["y"])
        case "desktop_type":
            return desktop.desktop_type(inputs["text"], inputs.get("press_enter", False))
        case "desktop_press":
            return desktop.desktop_press(inputs["keys"])
        case "desktop_scroll":
            return desktop.desktop_scroll(inputs["x"], inputs["y"], inputs["clicks"])
        case "desktop_get_position":
            return desktop.desktop_get_position()
        case "desktop_read_screen":
            return desktop.desktop_read_screen()
        case "desktop_find_text":
            return desktop.desktop_find_text(inputs["text"])
        case "desktop_analyze_screen":
            return desktop.desktop_analyze_screen(inputs["reason"])
        case _:
            return f"[ AURA ] Unknown tool: {name}"
