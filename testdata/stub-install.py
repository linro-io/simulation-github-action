#!/usr/bin/env python3
"""A stand-in for a Linro install's simulator download, for CI.

It serves GET /api/simulator/download/{version}/{os}-{arch}.tar.gz the way an
install does (Authorization: Bearer <token>, X-Linro-Sha256), so the action's
download is tested with no install and no secret. The tarball itself comes
from the public marketplace, anonymously; once the marketplace requires a key
for /artifacts this needs one too.

    stub-install.py <port-file> <request-log>

Environment: STUB_TOKEN (the token to accept), STUB_MODE (ok | bad-sha |
no-sha), STUB_SOURCE (marketplace base URL).
"""
import hashlib
import http.server
import os
import re
import sys
import urllib.error
import urllib.request

TOKEN = os.environ["STUB_TOKEN"]
MODE = os.environ.get("STUB_MODE", "ok")
SOURCE = os.environ.get("STUB_SOURCE", "https://marketplace.linro.io").rstrip("/")
PATH = re.compile(r"^/api/simulator/download/([A-Za-z0-9][A-Za-z0-9._+-]{0,63})/([a-z0-9]+-[a-z0-9]+)\.tar\.gz$")
port_file, log_file = sys.argv[1], sys.argv[2]


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        auth = self.headers.get("Authorization", "")
        with open(log_file, "a") as log:
            log.write(f"{self.path} auth={'ok' if auth == 'Bearer ' + TOKEN else 'bad'}\n")
        m = PATH.match(self.path)
        if not m:
            return self.send_error(404)
        if auth != "Bearer " + TOKEN:
            return self.send_error(401)
        version, platform = m.groups()
        req = urllib.request.Request(
            f"{SOURCE}/artifacts/simulators/linro-simulator/{version}/{platform}.tar.gz",
            # A User-Agent of its own: the default Python-urllib one is refused.
            headers={"X-Linro-Client": "simulation-github-action/ci-stub", "User-Agent": "linro-ci-stub/1"},
        )
        try:
            body = urllib.request.urlopen(req, timeout=120).read()
        except urllib.error.HTTPError as e:
            return self.send_error(404 if e.code in (404, 410) else 502)
        sha = hashlib.sha256(body).hexdigest()
        self.send_response(200)
        self.send_header("Content-Type", "application/gzip")
        self.send_header("Content-Length", str(len(body)))
        if MODE == "bad-sha":
            self.send_header("X-Linro-Sha256", "0" * 64)
        elif MODE != "no-sha":
            self.send_header("X-Linro-Sha256", sha)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
with open(port_file, "w") as f:
    f.write(str(server.server_address[1]))
server.serve_forever()
