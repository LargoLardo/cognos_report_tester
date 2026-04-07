from playwright.sync_api import Page
import csv
import os
from dotenv import load_dotenv
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from rest import status_codes
import time
import threading
from queue import Queue

load_dotenv(override=True)

AUTH_FILE = Path("cognos_auth_state.json")
COGNOS_BASE = os.getenv("COGNOS_BASE")

queue = Queue()
 
def get_context(page):
    """Return VA FrameLocator (prod)"""
    return page.frame_locator('iframe')

def start_manual_validator():
    """Starts sync playwright and worker thread."""
    out_path = "report_checks.csv"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=str(AUTH_FILE))
        page = context.new_page()

        # Prepare CSV
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Status", "URL"])
            writer.writeheader()

        print("here")

        # Start worker thread
        worker = threading.Thread(target=manual_check, args=(page, out_path), daemon=True)
        worker.start() 

        print("got here")

        return

 
def page_has_error(page: Page) -> bool:
    ERROR_KEYWORDS = [
        "an error has occurred",
        "failed",
        "contact your administrator",
        "not found",
        "error has been logged",
        "secureerrorid",
        "timeout",
        "server error",
        "invalid",
        "does not exist",
        "security settings",
        "not able to",
        "not allowed to",
        "could not find",
    ]
    iframe = get_context(page)
    for keyword in ERROR_KEYWORDS:
        selector = iframe.get_by_text(keyword)
        if selector.count() > 0:
            for i in range(selector.count()):
                sel = selector.nth(i)
                if sel.is_visible():
                    return True
    return False
 
def manual_check(page: Page, out_path: str = "report_checks.csv"):
    global queue
    count = 1
    print("boomalicious")
    while True:
        print("boomtjing")
        item = queue.get(block=True)
        if item is None:
            break
        id = item.id
        print("boom")
        url = f"{COGNOS_BASE.removesuffix("?perspective=home")}?objRef={item.id}"

        print(f"[{count}] Opening: {id} -> {url}")

        # Open the page (using domcontentloaded is faster; for better stability, you can change it to 'networkidle').
        page.goto(url, wait_until="domcontentloaded", timeout=200000)
        # Allow some rendering time (many reports are rendered by the front end).
        page.wait_for_load_state("networkidle", timeout=200000)

        has_err = page_has_error(page)
        status = "ERROR" if has_err else "OK"
        print(f"  -> {status}")

        # Append write results
        with open(out_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Name", "Status", "URL"])
            row = {
                "ID": id,
                "Status": status,
                "URL": url,
            }
            writer.writerow(row)
        count += 1
        queue.task_done()
    print(f"Done. Results saved to: {out_path}")
 
# def main():
#     # …This is the logic for your login, context creation, and page setup…
#     # page = context.new_page()
#     start = time.perf_counter()
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         context = browser.new_context(storage_state=str(AUTH_FILE))
#         page = context.new_page()
#         check_reports_from_file(page, out_path="report_checks.csv")
#     total = time.perf_counter() - start
#     print(f"Total runtime: {total:.2f} seconds")
 
 
# if __name__ == "__main__":
#     main()
 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 
"""
读取 report_checks.csv（表头：name,status,url），当 status 为 'error' 的行存在时，
把这些行汇总进 HTML 邮件并通过 SMTP 发送。
- TLS(587) 或 SSL(465) 均支持
- HTML 正文 + 纯文本回退
- 无错误是否发送可配置（SEND_WHEN_NO_ERROR）
"""