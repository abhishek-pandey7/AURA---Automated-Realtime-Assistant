import time
import pyautogui
import webbrowser
from aura.confirm import confirm_desktop

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "jiohotstar_play",
            "description": "Play a movie or TV show on JioHotstar by automating the browser. Will open jiohotstar.com, hover left, search, and play the first video.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The name of the movie or show to play."}
                },
                "required": ["query"]
            }
        }
    }
]

def jiohotstar_play(query: str) -> str:
    if not confirm_desktop("jiohotstar play", query):
        return "[ AURA ] JioHotstar play cancelled."

    # Fail-safe helps if the mouse goes wild
    pyautogui.FAILSAFE = True

    try:
        # 1. Open website
        webbrowser.open("https://www.jiohotstar.com")
        time.sleep(7) # Wait for page to load
        
        # 2. Hover on the left of the screen
        screen_w, screen_h = pyautogui.size()
        pyautogui.moveTo(10, screen_h // 2, duration=0.5)
        time.sleep(1.5) # Wait for sidebar to expand
        
        # 3. Click search button
        # Search is usually near the top of the expanded sidebar.
        pyautogui.click(50, screen_h // 4)
        time.sleep(1.5)
        
        # 4. Type the content
        pyautogui.write(query, interval=0.05)
        time.sleep(2)
        pyautogui.press('enter')
        time.sleep(4) # Wait for search results
        
        # 5. Play the first video
        pyautogui.click(screen_w // 3, screen_h // 2)
        
        return f"[ AURA ] Initiated sequence to play '{query}' on JioHotstar."
    except Exception as e:
        return f"[ AURA ] Failed to play on JioHotstar: {e}"
