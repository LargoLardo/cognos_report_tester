import os, getpass, time, logging, csv, random
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright, expect
from playwright.sync_api import TimeoutError as PWT

COGNOS_BASE = os.getenv("COGNOS_BASE")
AUTH_FILE = Path("cognos_auth_state.json")

load_dotenv()

def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        contextPresent = False

        try: 
            context = browser.new_context(storage_state=str(AUTH_FILE))
            contextPresent = True
            page = context.new_page()
        except FileNotFoundError:
            page = browser.new_page()
            
        page.goto(COGNOS_BASE, wait_until="networkidle")
        page.get_by_role("button", name="Continue").click()
        
        expect(page).to_have_title("Content")

        if not contextPresent:
            context = browser.new_context()
            context.storage_state(path=str(AUTH_FILE))
        
        context.close()
        browser.close()
        

if __name__ == "__main__":
    main()
