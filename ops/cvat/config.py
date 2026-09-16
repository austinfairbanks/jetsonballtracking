"""Read the private endpoint from the environment or an ignored local file."""
import os
from pathlib import Path


def cvat_base_url():
    configured = os.environ.get('CVAT_BASE_URL')
    if configured:
        return configured.rstrip('/')
    local = Path(__file__).resolve().parent / '.local/base-url'
    if local.exists():
        return local.read_text().strip().rstrip('/')
    return 'http://127.0.0.1:8082'
