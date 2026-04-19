import time
import pyautogui

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "check_bitcoin_price_coinmarketcap",
            "description": "Opens a browser, navigates to CoinMarketCap, and searches for the current price of Bitcoin.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

def check_bitcoin_price_coinmarketcap():
    pyautogui.FAILSAFE = True
    
    # Open browser/address bar (Cmd/Win key)
    pyautogui.press('cmd')
    time.sleep(1.5)
    
    # Click address bar area
    pyautogui.click(1287, 1052)
    time.sleep(0.5)
    
    # Type URL: coinmarketcap.com
    pyautogui.write('coinmarketcap.com')
    pyautogui.press('enter')
    time.sleep(5.0)
    
    # Navigate to search or specific menu items based on trace
    pyautogui.click(1456, 150)
    time.sleep(1.0)
    pyautogui.click(1455, 178)
    time.sleep(2.0)
    
    # Search for Bitcoin
    pyautogui.write('Bitcoin')
    time.sleep(3.0)
    
    # Click the Bitcoin result
    pyautogui.click(490, 365)
    time.sleep(2.0)