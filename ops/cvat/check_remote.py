"""Verify browser-style login through the private HTTPS endpoint."""
import http.cookiejar
import json
from config import cvat_base_url
from pathlib import Path
import urllib.request

base = cvat_base_url()
credentials = json.loads((Path(__file__).parent / '.local/login.json').read_text())
cookies = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))

def request(path, payload=None):
    headers = {'Origin': base, 'Referer': base + '/', 'Content-Type': 'application/json'}
    for cookie in cookies:
        if cookie.name == 'csrftoken':
            headers['X-CSRFToken'] = cookie.value
    req = urllib.request.Request(base + path, data=None if payload is None else json.dumps(payload).encode(), headers=headers)
    with opener.open(req, timeout=60) as response:
        return response.read()

request('/api/auth/login', credentials)
user = json.loads(request('/api/users/self'))
tasks = json.loads(request('/api/tasks'))
print('HTTPS session login verified:', user['username'])
print('Task count:', tasks['count'])
print('Imported frames:', tasks['results'][0]['size'])
