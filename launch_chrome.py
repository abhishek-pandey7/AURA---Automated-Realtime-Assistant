import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth

async def launch_chrome():
    async with async_playwright() as p:
        user_data_dir = r"C:\Users\Abhishek Pandey\AppData\Local\Google\Chrome\User Data"
        
        try:
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel="chrome",
                headless=False,
                args=[
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            
            page = browser_context.pages[0] if browser_context.pages else await browser_context.new_page()
            
            # Use the standard stealth function
            await stealth(page)
            
            print(f"Launched Chrome. Current page title: {await page.title()}")
            
            # Keep the browser open
            await asyncio.sleep(100) 
            await browser_context.close()
        except Exception as e:
            print(f"Error: {e}")
            print("\nNote: If you see 'user data directory is already in use', please close all Chrome windows and try again.")

if __name__ == "__main__":
    asyncio.run(launch_chrome())
