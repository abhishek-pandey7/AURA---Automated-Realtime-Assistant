import time
import base64
import re
from io import BytesIO
from pathlib import Path

import pyautogui
from pynput import mouse, keyboard
from PIL import Image
from rich.console import Console
import httpx
from openai import OpenAI

from aura.config import INFERX_BASE_URL, INFERX_API_KEY, INFERX_MODEL

console = Console()

class Recorder:
    def __init__(self):
        self.events = []
        self.start_time = None
        self.mouse_listener = None
        self.keyboard_listener = None
        self.running = False
        
    def _get_time(self):
        return round(time.time() - self.start_time, 2)

    def on_click(self, x, y, button, pressed):
        if pressed and self.running:
            self.events.append(f"T+{self._get_time()}s: Clicked {button} at ({x}, {y})")

    def on_press(self, key):
        if not self.running: return
        try:
            self.events.append(f"T+{self._get_time()}s: Typed '{key.char}'")
        except AttributeError:
            self.events.append(f"T+{self._get_time()}s: Pressed {key}")

    def on_release(self, key):
        if key == keyboard.Key.esc:
            self.running = False
            return False # Stop listener

    def record(self, duration_sec: int = 60):
        self.start_time = time.time()
        self.running = True
        
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.keyboard_listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        # Take start screenshot
        start_img_b64 = self._take_screenshot()
        
        console.print(f"\n[bold red]Recording started...[/bold red] (Press ESC or wait {duration_sec}s to stop)")
        
        while self.running and (time.time() - self.start_time) < duration_sec:
            time.sleep(0.5)
            
        self.running = False
        self.mouse_listener.stop()
        self.keyboard_listener.stop()
        
        end_img_b64 = self._take_screenshot()
        console.print("[bold green]Recording finished.[/bold green]\n")
        
        return self.events, start_img_b64, end_img_b64

    def _take_screenshot(self):
        try:
            img = pyautogui.screenshot()
            img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=75)
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception:
            return ""

def generate_tool_code(goal: str, events: list[str], start_img: str, end_img: str) -> str | None:
    client = OpenAI(
        base_url=INFERX_BASE_URL,
        api_key=INFERX_API_KEY,
        timeout=httpx.Timeout(timeout=180.0, connect=15.0),
    )
    
    events_str = "\n".join(events)
    prompt = f"""You are generating an autonomous AURA tool for the goal: '{goal}'.
The user performed this task manually, and recorded their physical actions. 
Here is their trace log:
```
{events_str}
```

Write ONLY a valid, self-contained Python script (NO markdown formatting or fences around the whole file, I will write it directly to .py). 
The script must contain:
1. An import statement for `time` and `pyautogui`.
2. `TOOL_DEFS` which is a list dict containing the JSON function schema for this new tool (with type, function, name, description, parameters). Use a clear snake_case function name built from the goal (e.g. `check_bank_balance`).
3. The actual Python function corresponding to `TOOL_DEFS` name, using `pyautogui` to execute the clicks/types sequentially with sensible `time.sleep()` between them.
Add `pyautogui.FAILSAFE = True` at the start of the function.
Ignore the 'Esc' press at the very end of the event trace as it was used to stop recording.
Condense sequential typing of characters into simple `pyautogui.write()`.
Do NOT enclose your output in ```python ... ```, literally output only code.
"""

    messages = [
        {"role": "system", "content": "You are a senior python developer creating AURA tools."},
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
        ]}
    ]
    
    if start_img:
        messages[1]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{start_img}"}})
    if end_img:
        messages[1]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{end_img}"}})

    try:
        response = client.chat.completions.create(
            model=INFERX_MODEL,
            max_tokens=2048,
            messages=messages,
            temperature=0.1,
        )
        return response.choices[0].message.content
    except Exception as e:
        console.print(f"[bold red]Generation Error:[/bold red] {e}")
        return None

def learn_workflow(goal: str, duration: int = 60):
    recorder = Recorder()
    events, start_img, end_img = recorder.record(duration)
    
    if not events:
        console.print("  [yellow]No input detected. Cancelling watch & learn task.[/yellow]")
        return
        
    console.print("  [cyan]Generating macro script from trace...[/cyan]")
    code = generate_tool_code(goal, events, start_img, end_img)
    if not code:
        return
        
    if code.startswith("```python"):
        code = code.split("```python")[1]
    if code.startswith("```"):
        code = code.split("```", 1)[1]
    if code.endswith("```"):
        code = code.rsplit("```", 1)[0]
    code = code.strip()
    
    match = re.search(r'def\s+([a-zA-Z0-9_]+)\(', code)
    if not match:
        console.print("  [red]Could not parse function name from generated code.[/red]")
        return
        
    tool_name = match.group(1)
    
    import aura.tools
    tools_dir = Path(aura.tools.__file__).resolve().parent
    file_path = tools_dir / f"{tool_name}.py"
    
    try:
        file_path.write_text(code, encoding="utf-8")
        aura.tools._init_tools()
        console.print(f"  [bold green]✓ Watch & Learn Complete![/bold green] Tool registered as '{tool_name}'.")
    except Exception as e:
        console.print(f"  [bold red]Failed to save tool:[/bold red] {e}")
