import time
import pyautogui

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "skip_youtube_ads",
            "description": "Automatically clicks the skip ad button on YouTube based on recorded coordinates.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

def skip_youtube_ads():
    pyautogui.FAILSAFE = True
    
    # Click 1: Initial interaction/ad area
    pyautogui.click(1292, 956)
    time.sleep(2.18)
    
    # Click 2: Potential skip button location
    pyautogui.click(1154, 678)
    time.sleep(3.43)
    
    # Click 3: Final skip button confirmation
    pyautogui.click(1271, 835)