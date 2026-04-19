from aura.tools import shell, filesystem, web, desktop, calendar, gmail, meet, forms

ALL_TOOL_DEFS = (
    [shell.TOOL_DEF]
    + filesystem.TOOL_DEFS
    + web.TOOL_DEFS
    + desktop.TOOL_DEFS
    + calendar.TOOL_DEFS
    + gmail.TOOL_DEFS
    + meet.TOOL_DEFS
    + forms.TOOL_DEFS
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
        case "calendar_list_events":
            return calendar.calendar_list_events(inputs.get("max_results", 10))
        case "calendar_add_event":
            return calendar.calendar_add_event(
                inputs["title"],
                inputs["start_datetime"],
                inputs.get("end_datetime"),
                inputs.get("description", ""),
                inputs.get("reminder_minutes", 10)
            )
        case "calendar_delete_event":
            return calendar.calendar_delete_event(inputs["title"])
        case "gmail_send":
            return gmail.gmail_send(
                inputs["to"],
                inputs["subject"],
                inputs["body"],
                inputs.get("cc", "")
            )
        case "gmail_read_inbox":
            return gmail.gmail_read_inbox(inputs.get("max_results", 5))
        case "meet_create":
            return meet.meet_create(
                inputs["title"],
                inputs["start_datetime"],
                inputs.get("end_datetime"),
                inputs.get("attendees", []),
                inputs.get("email_link_to", []),
                inputs.get("description", "")
            )
        case "forms_load_profile":
            return forms.forms_load_profile()
        case "forms_update_profile":
            return forms.forms_update_profile(inputs["field"], inputs["value"])
        case "forms_generate_prefill_url":
            return forms.forms_generate_prefill_url(inputs["form_url"], inputs["field_values"])
        case _:
            return f"[ AURA ] Unknown tool: {name}"

