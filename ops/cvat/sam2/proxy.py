"""Private CVAT-to-native-GPU bridge. No model, data storage, or host port."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import urllib.error
import urllib.request

TOKEN = Path('/run/secrets/sam2_token').read_text().strip()
UPSTREAM = 'http://host.lima.internal:8071'
# Do not route image payloads through any inherited HTTP proxy.
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class Handler(BaseHTTPRequestHandler):
    def forward(self):
        if self.path not in ('/health', '/api/functions', '/api/functions/volleyball-sam2',
                             '/api/function_invocations'):
            self.send_error(404)
            return
        body = None
        if self.command == 'POST':
            try:
                length = int(self.headers.get('Content-Length', 0))
            except ValueError:
                self.send_error(400)
                return
            if not 0 < length <= 32 * 1024 * 1024:
                self.send_error(413)
                return
            body = self.rfile.read(length)
        headers = {'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json',
                   'x-nuclio-function-name': self.headers.get('x-nuclio-function-name', '')}
        request = urllib.request.Request(UPSTREAM + self.path, data=body,
                                         headers=headers, method=self.command)
        try:
            with OPENER.open(request, timeout=120) as response:
                code, payload = response.status, response.read()
        except urllib.error.HTTPError as error:
            code, payload = error.code, error.read()
        except (urllib.error.URLError, TimeoutError, OSError):
            code, payload = 502, json.dumps({'error': 'Native SAM 2 GPU service unavailable'}).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = forward
    do_POST = forward


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 8070), Handler).serve_forever()
