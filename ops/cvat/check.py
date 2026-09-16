"""Read-only task/import verification from inside the CVAT server."""
import json
from pathlib import Path
import requests

s = requests.Session()
s.trust_env = False
base = 'http://localhost:8080/api'
r = s.post(base + '/auth/login', json=json.loads(Path('/home/django/data/volleyball-login.json').read_text()), timeout=30)
r.raise_for_status()
if r.json().get('key'):
    s.headers['Authorization'] = 'Token ' + r.json()['key']

def get(path):
    r = s.get(base + path, timeout=120)
    r.raise_for_status()
    return r.json()

tasks = get('/tasks')
assert tasks['count'] == 1, tasks['count']
t = tasks['results'][0]
print('Task:', json.dumps({k: t.get(k) for k in ['id', 'name', 'size', 'mode', 'status', 'jobs']}))
print('Requests:', json.dumps(get('/requests')))
print('Labels:', json.dumps(get('/labels?task_id=1')))
if t['size'] == 644:
    frames = get('/tasks/1/data/meta')['frames']
    expected = sorted(p.name for p in Path('/home/django/share/keyframes').glob('*.png'))
    assert [Path(f['name']).name for f in frames] == expected
    jobs = get('/jobs?task_id=1')['results']
    assert len(jobs) == 1
    a = get('/tasks/1/annotations')
    print('Verified: all 644 filenames match, single job.')
    print('Annotation counts:', {k: len(a[k]) for k in ['shapes', 'tracks', 'tags']})
    print('Job:', jobs[0]['id'])
    for index in [0, 643]:
        r = s.get(base + f'/tasks/1/data?type=frame&number={index}&quality=original', timeout=120)
        r.raise_for_status()
        assert r.content.startswith(b'\x89PNG'), r.headers
        print('Original frame', index, 'readable:', len(r.content), 'bytes')
