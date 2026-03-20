import requests
import urllib3
import os
import time
from dotenv import load_dotenv

load_dotenv(override=True)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

passport = os.getenv("PASSPORT")
caf = os.getenv("CAF")
api_base = os.getenv("API_BASE")
cms_base = os.getenv("CMS_BASE")
headers = {
    "IBM-BA-Authorization": "CAM " + passport
}
cookies = {
    "cam_passport": passport,
    "caf": caf
}
status_codes = {} 
# Common codes include: 
# 200 (success) 
# 400 (too much data being returned)
# 408 (timeout)
# 500 (error in running)
# 100 (non-report type, to be handled by manual checker)

class Report:
    def __init__(self, type: str, id: str, status_code: int):
        self.type = type
        self.id = id
        self.status_code = status_code

    def set_status(self, new_status_code: int):
        self.status_code = new_status_code
        return True

def update_headers_and_cookies():
    global passport, caf, headers, cookies
    passport = os.getenv("PASSPORT")
    caf = os.getenv("CAF")
    headers = {
        "IBM-BA-Authorization": "CAM " + passport
    }
    cookies = {
        "cam_passport": passport,
        "caf": caf
    }

def session():
    return requests.get(
        api_base + "/session", 
        headers=headers,
        verify=False
    )

def content(extension: str = ''):
    return requests.get(
        api_base + "/content" + extension, 
        headers=headers,
        verify=False
    )

def write_status_codes():
    with open('status_codes', 'w') as codes:
        for code, arr in status_codes.items():
            print(f"{code}: {len(arr)}", file=codes)
        print("\n", file=codes)
        for code, arr in status_codes.items():
            print(f"{code}:", file=codes)
            for report in arr:
                print(report.id, file=codes)
            print("\n", file=codes)

def run(report_id: str, item):
    global status_codes
    name = item['defaultName']
    type = item['type']
    with open('run_logs', 'a', encoding='utf-8') as logs:
        logs.write(f"{name}: ")
    report_id = report_id.replace('/items', '')
    report_id = report_id.strip('/')
    try:
        res = requests.get(
            cms_base + f"/bi/v1/disp/rds/ReportData/storeID/{report_id}?fmt=Dataset",
            cookies=cookies,
            verify=False,
            timeout=60
        )
        status_code = res.status_code
    except requests.exceptions.ReadTimeout:
        res = 'Timeout Exception'
        status_code = 408
    report = Report(type, report_id, status_code)
    status_codes.setdefault(status_code, list()).append(report)
    write_status_codes()
    with open('run_logs', 'a', encoding='utf-8') as logs:
        logs.write(f"{status_code} ")
        if status_code != 200 and status_code != 408:
            try:
                text = res.text.split('<rds:message>')[1].split('</rds:message>')[0]
            except:
                text = res.text
            logs.write(f"({text})")
        elif status_code == 408:
            logs.write('(Timeout Exception)')
        logs.write('\n')
    return status_code

def action_by_type(new_extension: str, item):
    type = item['type']
    if type == 'report' or type == 'reportView':
        run(new_extension, item)
    elif type == 'folder':
        nav_reports(new_extension)
    else:
        id = new_extension.replace('/items', '')
        id = id.strip('/')
        object = Report(type, id, 100)
        status_codes.setdefault(100, list()).append(object)
        ############ Handle other types using manual checker ##############

def nav_reports(extension: str):
    res = content(extension)
    res = res.json()
    try:
        for link in res['links']:
            if link['rel'] != 'self':
                new_extension = link['href'].replace("/api/v1/content", '')
                action_by_type(new_extension, res)
    except KeyError:
        content_items = res['content']
        for item in content_items:
            for link in item['links']:
                if link['rel'] != 'self':
                    new_extension = link['href'].replace("/api/v1/content", '')
                    action_by_type(new_extension, item)

def debug_content():
    extension = "Not None"
    while extension != None:
        extension = str(input()).strip()
        print(api_base + "/content" + extension)
        res = requests.get(
            api_base + "/content" + extension,
            headers=headers,
            verify=False
        )
        print(res.text)
        res = res.json()
        try:
            print(res['defaultName'])
            for link in res['links']:
                if link['rel'] != 'self':
                    print(link['href'])
        except KeyError:
            for item in res['content']:
                print(item['defaultName'])
                for link in item['links']:
                    if link['rel'] != 'self':
                        print(link['href'])