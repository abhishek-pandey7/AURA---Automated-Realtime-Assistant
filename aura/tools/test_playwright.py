from playwright.sync_api import sync_playwright

def main():
    try:
        with sync_playwright() as p:
            print("Playwright started")
            browser = p.chromium.launch(headless=False)
            print("Browser launched")
            page = browser.new_page()
            print("Page created")
            page.goto("https://www.example.com")
            print("Navigated to example.com")
            browser.close()
            print("Success")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
