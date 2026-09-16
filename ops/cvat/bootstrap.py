"""Run through manage.py shell in this project's CVAT server only."""

import json
import secrets
from pathlib import Path

import requests
from django.contrib.auth import get_user_model

credential_path = Path('/home/django/data/volleyball-login.json')
User = get_user_model()
if credential_path.exists():
    credentials = json.loads(credential_path.read_text())
else:
    if User.objects.filter(username='volleyball').exists():
        raise RuntimeError('Existing user without bootstrap credentials; refusing to reset password')
    credentials = {'username': 'volleyball', 'password': secrets.token_urlsafe(18)}
    User.objects.create_superuser(email='', **credentials)
    credential_path.write_text(json.dumps(credentials, indent=2))
    credential_path.chmod(0o600)

session = requests.Session()
base = 'http://localhost:8080/api'
response = session.post(f'{base}/auth/login', json=credentials, timeout=30)
response.raise_for_status()
if response.json().get('key'):
    session.headers['Authorization'] = 'Token ' + response.json()['key']
if session.cookies.get('csrftoken'):
    session.headers['X-CSRFToken'] = session.cookies['csrftoken']

def api(method, path, **kwargs):
    response = session.request(method, base + path, timeout=120, **kwargs)
    if not response.ok:
        raise RuntimeError(f'{method} {path}: {response.status_code} {response.text[:2000]}')
    return response.json()

tasks = api('GET', '/tasks')['results']
name = 'Volleyball — all keyframes — polygon segmentation'
if any(task['name'] != name for task in tasks):
    raise RuntimeError('Unexpected tasks in instance; refusing to change anything')
if tasks:
    task = tasks[0]
else:
    task = api('POST', '/tasks', json={
        'name': name,
        'labels': [{'name': 'volleyball', 'type': 'polygon', 'color': '#32cd32', 'attributes': []}],
        'segment_size': 1000,
        'overlap': 0,
    })
    frames = sorted(Path('/home/django/share/keyframes').glob('*.png'))
    assert len(frames) == 644, f'Expected 644 PNGs, found {len(frames)}'
    request = api('POST', f"/tasks/{task['id']}/data", json={
        'server_files': [f'keyframes/{frame.name}' for frame in frames],
        'image_quality': 100,
        'sorting_method': 'lexicographical',
        'use_cache': True,
        'copy_data': True,
        'chunk_size': 16,
    })
    Path('/home/django/data/volleyball-import.json').write_text(json.dumps(request, indent=2))
    print('Import request:', json.dumps(request))
print('Task:', task['id'], task['name'])
print('Credentials saved in project-private data volume; not printed.')
