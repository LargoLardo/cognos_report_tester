import urllib3
import requests
import os
import json
import re
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv(override=True)

BASE = "https://rest-bidacog-0000-ist.apps.ocp8.8lex.p1.openshiftapps.com:443"
STORE_ID = "i6E54FC74C77A4CE9861510308D7347E7"
FMT = "HTML"

cookies = {
    "cam_passport": os.getenv("PASSPORT"),
    "caf": os.getenv("CAF")
}

def open_prompt_page_HTML(url: str):
    res = requests.get(url, cookies=cookies, verify=False)
    with open('prompt_page_html', 'w') as file:
        file.write(res.text)
    return res.text

def get_prompt_page(id: str):
    prompts_url = f"{BASE}/bi/v1/disp/rds/promptPage/storeID/{id}"
    rp = requests.get(f"{prompts_url}?v=3", cookies=cookies, timeout=30, verify=False)
    rp.raise_for_status()

    with open('prompt_page', "w") as file:
        file.write(rp.text)

    print(rp.text + "\n")

    prompt_page_XML = rp.text
    prompt_page_URL = prompt_page_XML.split('<rds:url>')[1].split('</rds:url>')[0]
    prompt_page_URL = prompt_page_URL.replace('&amp;', '&')

    return prompt_page_URL

def parse_HTML_for_params(html: str):
    pattern = r"G_PM_THIS_\.F_Add\((\{.*?\})\s*,\s*\{"
    matches = re.findall(pattern, html, flags=re.DOTALL)

    parameters = []

    for block in matches:
        # Fix JSON-like syntax: single quotes → double quotes
        block = block.replace("'", '"')
        info = {}
        info['parameter'] = block.split('"@parameter"')[1].split('"', 2)[1]
        info['required'] = True if block.split('"@required":')[1].lower().startswith('true') else False
        info['multiselect'] = True if block.split('"@multiSelect":')[1].lower().startswith('true') else False
        info['control_type'] = block.split('"', 2)[1]
        
        print("\n")
        print(info)
        # print(block)

        parameters.append(block)



url = get_prompt_page(STORE_ID)
html = open_prompt_page_HTML(url)
params = parse_HTML_for_params(html)