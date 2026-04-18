import time
import pyautogui
from aura.confirm import confirm_desktop

# Fail-safe helps if the mouse goes wild
pyautogui.FAILSAFE = True

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "desktop_click",
            "description": "Move the mouse to an (x, y) coordinate and click.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate."},
                    "y": {"type": "integer", "description": "Y coordinate."},
                    "clicks": {"type": "integer", "description": "Number of clicks (default 1)."},
                    "button": {"type": "string", "description": "'left', 'middle', or 'right' (default 'left')."}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "desktop_move_mouse",
            "description": "Move mouse to (x, y) WITHOUT clicking. Use this to hover over menus or elements before clicking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate to move to."},
                    "y": {"type": "integer", "description": "Y coordinate to move to."}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "desktop_type",
            "description": "Type a string of text using the keyboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type."},
                    "press_enter": {"type": "boolean", "description": "Whether to press Enter after typing."}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "desktop_press",
            "description": "Press a specific hotkey or key combination.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of keys to press together (e.g. ['ctrl', 't'] or ['win'] or ['enter'])."
                    }
                },
                "required": ["keys"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "desktop_scroll",
            "description": "Scroll the mouse wheel at a given (x, y) position. Positive clicks scroll up, negative scroll down.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate to scroll at."},
                    "y": {"type": "integer", "description": "Y coordinate to scroll at."},
                    "clicks": {"type": "integer", "description": "Number of scroll steps. Positive = up, negative = down."}
                },
                "required": ["x", "y", "clicks"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "desktop_get_position",
            "description": "Get the current mouse position on the screen.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "desktop_read_screen",
            "description": "Runs full-screen OCR and returns a complete spatial map of ALL visible text on screen with exact (x, y) coordinates. Use this to understand the current state of any application or webpage before interacting.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "desktop_find_text",
            "description": "Finds the exact (x, y) pixel coordinates of specific text visible on the screen using local OCR. Use desktop_read_screen for a full map, or this for targeting one specific element.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The exact text to search for on the screen."}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "desktop_analyze_screen",
            "description": "Take a screenshot and send it to the vision model for visual analysis. Use this when OCR alone is insufficient and you need to visually understand layout, images, or icons.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"}
                },
                "required": ["reason"]
            }
        }
    }
]


def desktop_click(x: int, y: int, clicks: int = 1, button: str = "left") -> str:
    if not confirm_desktop("click", f"x={x}, y={y}, clicks={clicks}, button={button}"):
        return "[ AURA ] Desktop action cancelled."
    try:
        pyautogui.click(x=x, y=y, clicks=clicks, button=button)
        time.sleep(0.3)
        return f"[ AURA ] Clicked at ({x}, {y}) {clicks} time(s) with {button} button."
    except Exception as e:
        return f"[ AURA ] Desktop click failed: {e}"


def desktop_move_mouse(x: int, y: int) -> str:
    if not confirm_desktop("move mouse", f"x={x}, y={y}"):
        return "[ AURA ] Desktop action cancelled."
    try:
        pyautogui.moveTo(x, y, duration=0.3)
        time.sleep(0.2)
        return f"[ AURA ] Mouse moved to ({x}, {y})."
    except Exception as e:
        return f"[ AURA ] Mouse move failed: {e}"


def desktop_type(text: str, press_enter: bool = False) -> str:
    preview = text if len(text) < 50 else text[:47] + "..."
    if not confirm_desktop("type", f"'{preview}' (enter={press_enter})"):
        return "[ AURA ] Desktop action cancelled."
    try:
        time.sleep(0.5)
        pyautogui.write(text, interval=0.02)
        if press_enter:
            pyautogui.press('enter')
        time.sleep(0.5)
        return "[ AURA ] Typed text successfully."
    except Exception as e:
        return f"[ AURA ] Desktop type failed: {e}"


def desktop_press(keys: list[str]) -> str:
    if not confirm_desktop("hotkey", " + ".join(keys)):
        return "[ AURA ] Desktop action cancelled."
    try:
        pyautogui.hotkey(*keys)
        time.sleep(0.5)
        return f"[ AURA ] Pressed keys: {' + '.join(keys)}."
    except Exception as e:
        return f"[ AURA ] Desktop hotkey failed: {e}"


def desktop_scroll(x: int, y: int, clicks: int) -> str:
    if not confirm_desktop("scroll", f"x={x}, y={y}, clicks={clicks}"):
        return "[ AURA ] Desktop action cancelled."
    try:
        pyautogui.scroll(clicks, x=x, y=y)
        time.sleep(0.3)
        direction = "up" if clicks > 0 else "down"
        return f"[ AURA ] Scrolled {direction} {abs(clicks)} click(s) at ({x}, {y})."
    except Exception as e:
        return f"[ AURA ] Desktop scroll failed: {e}"


def desktop_get_position() -> str:
    try:
        x, y = pyautogui.position()
        width, height = pyautogui.size()
        return f"[ AURA ] Mouse Position: ({x}, {y}) | Screen Size: {width}x{height}"
    except Exception as e:
        return f"[ AURA ] Failed to get mouse position: {e}"


def desktop_read_screen() -> str:
    """Full-screen OCR. Returns a spatial map of all visible text with (x, y) centroids."""
    import asyncio
    import io
    from winsdk.windows.media.ocr import OcrEngine
    from winsdk.windows.graphics.imaging import BitmapDecoder
    from winsdk.windows.storage.streams import InMemoryRandomAccessStream, DataWriter

    async def _read():
        img = pyautogui.screenshot()
        screen_w, screen_h = img.size

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='BMP')

        stream = InMemoryRandomAccessStream()
        d_writer = DataWriter(stream.get_output_stream_at(0))
        d_writer.write_bytes(img_byte_arr.getvalue())
        await d_writer.store_async()
        await d_writer.flush_async()

        decoder = await BitmapDecoder.create_async(stream)
        software_bitmap = await decoder.get_software_bitmap_async()

        engine = OcrEngine.try_create_from_user_profile_languages()
        if not engine:
            return "[ AURA ] OCR Engine could not initialize."

        result = await engine.recognize_async(software_bitmap)

        lines_out = []
        for line in result.lines:
            words = list(line.words)
            if not words:
                continue
            xs = [w.bounding_rect.x + w.bounding_rect.width / 2 for w in words]
            ys = [w.bounding_rect.y + w.bounding_rect.height / 2 for w in words]
            cx = int(sum(xs) / len(xs))
            cy = int(sum(ys) / len(ys))
            lines_out.append(f"  [{cx:4d}, {cy:4d}]  {line.text}")

        if not lines_out:
            return "[ AURA ] Screen OCR returned no text — screen may be blank or fully graphical."

        header = f"[ AURA ] Screen Map ({screen_w}x{screen_h}) — {len(lines_out)} text regions found:\n"
        header += "   [  X ,   Y ]  Text\n"
        header += "  " + "-" * 55
        return header + "\n" + "\n".join(lines_out)

    try:
        return asyncio.run(_read())
    except Exception as e:
        return f"[ AURA ] Screen read failed: {e}"


def desktop_find_text(text: str) -> str:
    """Find the (x, y) centroid of lines containing the target text."""
    import asyncio
    import io
    from winsdk.windows.media.ocr import OcrEngine
    from winsdk.windows.graphics.imaging import BitmapDecoder
    from winsdk.windows.storage.streams import InMemoryRandomAccessStream, DataWriter

    async def _find():
        img = pyautogui.screenshot()
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='BMP')

        stream = InMemoryRandomAccessStream()
        d_writer = DataWriter(stream.get_output_stream_at(0))
        d_writer.write_bytes(img_byte_arr.getvalue())
        await d_writer.store_async()
        await d_writer.flush_async()

        decoder = await BitmapDecoder.create_async(stream)
        software_bitmap = await decoder.get_software_bitmap_async()

        engine = OcrEngine.try_create_from_user_profile_languages()
        if not engine:
            return "[ AURA ] OCR Engine failed to initialize."

        result = await engine.recognize_async(software_bitmap)

        matches = []
        target = text.lower()
        for line in result.lines:
            if target in line.text.lower():
                words = list(line.words)
                xs = [w.bounding_rect.x + w.bounding_rect.width / 2 for w in words]
                ys = [w.bounding_rect.y + w.bounding_rect.height / 2 for w in words]
                cx = int(sum(xs) / len(xs))
                cy = int(sum(ys) / len(ys))
                matches.append(f"  '{line.text}' at ({cx}, {cy})")

        if not matches:
            return f"[ AURA ] Text '{text}' not found on screen."
        return "[ AURA ] Matches found:\n" + "\n".join(matches)

    try:
        return asyncio.run(_find())
    except Exception as e:
        return f"[ AURA ] Screen OCR failed: {e}"


def desktop_analyze_screen(reason: str) -> str:
    """Screenshot → base64 JPEG for vision-capable LLM injection."""
    import base64
    from io import BytesIO
    from PIL import Image

    if not confirm_desktop("analyze screen", reason):
        return "[ AURA ] Action cancelled."
    try:
        img = pyautogui.screenshot()
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"[ IMAGE_BASE64: data:image/jpeg;base64,{img_str} ]"
    except Exception as e:
        return f"[ AURA ] Screen capture failed: {e}"
