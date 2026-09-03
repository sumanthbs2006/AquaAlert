import requests
import time
import re

url = 'https://frog-games-earned-radar.trycloudflare.com'
t0 = time.time()
r_html = requests.get(url, timeout=15)
print(f'HTML Status: {r_html.status_code}, Time: {round(time.time() - t0, 2)}s, Size: {len(r_html.text)} bytes')

match = re.search(r'src="(/assets/[^"]+\.js)"', r_html.text)
if match:
    js_url = url + match.group(1)
    t1 = time.time()
    r_js = requests.get(js_url, timeout=15)
    print(f'JS Bundle Status: {r_js.status_code}, Time: {round(time.time() - t1, 2)}s, Size: {len(r_js.content)} bytes')

t2 = time.time()
r_api = requests.get(f'{url}/api/sensors/summary', timeout=15)
print(f'API Status: {r_api.status_code}, Time: {round(time.time() - t2, 2)}s: {r_api.json().get("active_scenario_name")}')
