import time
import pyautogui

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "search_bloom_model_huggingface",
            "description": "Navigates to Hugging Face and searches for the BLOOM model.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

def search_bloom_model_huggingface():
    pyautogui.FAILSAFE = True
    
    # Click address bar/browser area
    pyautogui.click(1303, 1064)
    time.sleep(1.6)
    
    # Focus address bar
    pyautogui.click(620, 10)
    time.sleep(0.5)
    # Type huggingface and enter
    pyautogui.write('huggingface')
    pyautogui.press('enter')
    time.sleep(2.8)
    
    # Click search bar
    pyautogui.click(521, 374)
    time.sleep(4.7)
    
    # Click search input field
    pyautogui.click(597, 163)
    time.sleep(0.7)
    
    # Type BLOOM
    pyautogui.write('BLOOM')
    time.sleep(4.6)
    
    # Re-click/ensure focus and type BLOOM again as per trace
    pyautogui.click(597, 163)
    time.sleep(0.4)
    pyautogui.write('BLOOM')
    time.sleep(3.3)
    
    # Click the result
    pyautogui.click(479, 237)
    time.sleep(5.3)