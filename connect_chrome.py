import asyncio
from playwright.async_api import async_playwright

async def connect_chrome():
    async with async_playwright() as p:
        try:
            # Attempt to connect to a Chrome instance already running with remote debugging enabled
            # Default port is 9222
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            
            print(f"Successfully connected to Chrome. Current page title: {await page.title()}")
            
            # List all open tabs
            print("\nOpen Tabs:")
            for i, p in enumerate(context.pages):
                print(f"{i}: {await p.title()} - {p.url}")
                
            await browser.close()
        except Exception as e:
            print(f"Error: {e}")
            print("\nTo use this method, you must launch Chrome with the remote-debugging-port flag:")
            print(r'chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\Users\Abhishek Pandey\AppData\Local\Google\Chrome\User Data"')

if __name__ == "__main__":
    asyncio.run(connect_chrome())
