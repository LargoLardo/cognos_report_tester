from typing import List, Tuple
from playwright.async_api import Page
import csv
import os
from dotenv import load_dotenv
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright, expect
from rest import status_codes
import time

load_dotenv(override=True)

AUTH_FILE = Path("cognos_auth_state.json")
COGNOS_BASE = os.getenv("COGNOS_BASE")
 
def get_context(page):
    """Return VA FrameLocator (prod)"""
    return page.frame_locator('iframe')
 
# 2) Scan the entire page of text for incorrect keywords (simple and straightforward method)
async def page_has_error(page: Page) -> bool:
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
        "could not be found"
    ]
    iframe = get_context(page)
    for keyword in ERROR_KEYWORDS:
        selector = iframe.get_by_text(keyword)
        if await selector.count() > 0:
            for i in range(await selector.count()):
                sel = selector.nth(i)
                if await sel.is_visible():
                    return True
    return False
 
# 3) Open each URL one by one and check.
async def check_reports(page: Page, out_path: str = "report_checks.csv", ids: List = []):
    print(f"Loaded {len(ids)} reports.")
 
    # Result file header (optional)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ID", "Status"])
        writer.writeheader()
 
    for idx, id in enumerate(ids, 1):
        print(f"[{idx}/{len(ids)}] Opening: {id}")
        url = f"{COGNOS_BASE.removesuffix("?perspective=home")}?objRef={id}"
        # start_time = time.time()
        # Open the page (using domcontentloaded is faster; for better stability, you can change it to 'networkidle').
        await page.goto(url, wait_until="domcontentloaded", timeout=200000)
        # print(time.time() - start_time, " domcontent")
        # start_time = time.time()
        # Allow some rendering time (many reports are rendered by the front end).
        await page.wait_for_load_state("networkidle", timeout=200000)
        # print(time.time() - start_time, "network idle")
        
        # start_time = time.time()
        has_err = await page_has_error(page)
        # print(time.time() - start_time, "error checking")

        status = "ERROR" if has_err else "OK"
 
        # Append write results
        with open(out_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["ID", "Status"])
            row = {
                "ID": id,
                "Status": status,
            }
            writer.writerow(row)
 
    print(f"Done. Results saved to: {out_path}")

async def worker(worker_id, browser):
    context = await browser.new_context()
    context =  await browser.new_context(storage_state=str(AUTH_FILE))
    page = await context.new_page()
    ids = []
    names = []
    with open(f"logs/run_logs_{worker_id}", "r") as f:
        for line in f:
            linearr = line.split("|")
            names.append(linearr[0].strip())
            ids.append(linearr[1].strip())
    await check_reports(page, "report_checks.csv", ids)
    await context.close()

async def main():
    # …This is the logic for your login, context creation, and page setup…
    # page = context.new_page()
    start = time.perf_counter()
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        tasks = [
            worker(i, browser)
            for i in range(10)
        ]
        await asyncio.gather(*tasks)
        await browser.close()
    total = time.perf_counter() - start
    print(f"Total runtime: {total:.2f} seconds")
 
 
if __name__ == "__main__":
    asyncio.run(main())
 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 
"""
读取 report_checks.csv（表头：name,status,url），当 status 为 'error' 的行存在时，
把这些行汇总进 HTML 邮件并通过 SMTP 发送。
- TLS(587) 或 SSL(465) 均支持
- HTML 正文 + 纯文本回退
- 无错误是否发送可配置（SEND_WHEN_NO_ERROR）
"""