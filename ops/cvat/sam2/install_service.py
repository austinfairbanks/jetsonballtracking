"""Register the already-installed native GPU worker as a macOS login service."""
import os
from pathlib import Path
import plistlib
import secrets
import subprocess

root = Path(__file__).resolve().parents[1]
local = root / '.local'
local.mkdir(exist_ok=True, mode=0o700)
token = local / 'sam2-token'
if not token.exists():
    fd = os.open(token, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(secrets.token_hex(32))
label = 'com.austinfairbanks.volleyball-sam2'
domain = f'gui/{os.getuid()}'
plist = Path.home() / 'Library/LaunchAgents' / f'{label}.plist'
plist.parent.mkdir(parents=True, exist_ok=True)
config = {
    'Label': label,
    'ProgramArguments': [str(local / 'sam2-venv/bin/python'), str(root / 'sam2/server.py')],
    'WorkingDirectory': str(root.parent.parent),
    'EnvironmentVariables': {'SAM2_TOKEN_FILE': str(token),
                             'SAM2_CHECKPOINT': str(local / 'sam2.1_hiera_large.pt'),
                             'PYTHONUNBUFFERED': '1', 'OMP_NUM_THREADS': '2'},
    'RunAtLoad': True, 'KeepAlive': True, 'ThrottleInterval': 10,
    'StandardOutPath': str(local / 'sam2-gpu.log'),
    'StandardErrorPath': str(local / 'sam2-gpu.log'),
}
plist.write_bytes(plistlib.dumps(config))
plist.chmod(0o600)
subprocess.run(['launchctl', 'bootout', f'{domain}/{label}'], capture_output=True)
subprocess.run(['launchctl', 'bootstrap', domain, str(plist)], check=True)
print('Native GPU service registered:', label)
