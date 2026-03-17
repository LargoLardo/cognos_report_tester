from playwright.sync_api import sync_playwright, expect
from playwright.sync_api import TimeoutError as PWT
import time
import os
from dotenv import load_dotenv

load_dotenv()

AUTH_FILE = 'cognos_auth_state.json'
COGNOS_BASE = os.getenv("COGNOS_BASE")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(COGNOS_BASE)
 
        time.sleep(2)
       
        cont = page.get_by_role("button", name="Continue")
        if cont.count() > 0:
            cont.click()
 
        page.wait_for_load_state("networkidle", timeout=300000)
   
        context.storage_state(path=str(AUTH_FILE))
       
        browser.close()

if __name__ == "__main__":
    main()