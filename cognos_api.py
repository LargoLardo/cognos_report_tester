import os
import sys
import time
from playwright.sync_api import sync_playwright, expect
from dotenv import find_dotenv, load_dotenv, set_key
from rest import *

dotenv_path = find_dotenv()
load_dotenv(override=True)

# Consider using requests.Session(), persistent headers across calls with session.headers.update().

# Try calling the api first, if it doesn't work, get a new passport token from cookies
passport_works = True
res = session()

if res.status_code != 200:
    print("Saved passport did not work, opening window for manual authentication.")
    passport_works = False
    with sync_playwright() as playwright:
        COGNOS_BASE = os.getenv("COGNOS_BASE")

        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(COGNOS_BASE, wait_until="networkidle")
        page.get_by_role("button", name="Continue").click()

        try:
            expect(page).to_have_title("Home", timeout=600000)
            
            cookies = context.cookies()
            passport = ''
            caf = ''
            
            for cookie in cookies:
                if cookie['name'] == 'cam_passport':
                    passport = cookie['value']
            
            context.close()
            browser.close()

            set_key(
                dotenv_path = dotenv_path,
                key_to_set = "PASSPORT", 
                value_to_set = passport,
            )

            load_dotenv(override=True)
            update_headers_and_cookies()

            res = session()
            
            if res.status_code != 200:
                print(res.text)
                print(res.status_code)
                print("Passport is incorrect, or cannot get passport from cookies")
            else:
                passport_works = True
                res_data = res.json()
                caf = res_data['cafContextId']
                set_key(
                    dotenv_path = dotenv_path,
                    key_to_set = "CAF", 
                    value_to_set = caf,
                )
                load_dotenv(override=True)
                update_headers_and_cookies()
        except AssertionError:
            print("Timed out after 10 minutes, page either did not load in time or user did not log in. (Check if title of the page is still 'Home')")

if not passport_works:
    sys.exit(1)

print(res.text)
print(res.status_code)

res = content()

print(res.text)
print(res.status_code)

print("Starting report verification process at", time.ctime())
start_time = time.time()

nav_reports("/i70D61B7D0D5E4A3DB8A20CF9A60E6196/items")
# nav_reports("/i70D61B7D0D5E4A3DB8A20CF9A60E6196/items")
print("Finished at", time.ctime())
print(time.time() - start_time, "seconds elapsed")