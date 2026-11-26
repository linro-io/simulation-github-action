#!/usr/bin/env python3
"""A stand-in for a Linro install's simulator download, for CI.

It serves GET /api/simulator/download/{version}/{os}-{arch}.tar.gz the way an
install does (Authorization: Bearer <token>, X-Linro-Sha256), so the action's
download is tested with no install. The tarball itself comes from the
marketplace, which requires an API key on /artifacts: STUB_SOURCE_KEY, an
lmk_ key scoped artifacts:read, sent to STUB_SOURCE and not to the object
store it redirects to.

    stub-install.py <port-file> <request-log>

Environment: STUB_TOKEN (the token to accept), STUB_MODE (ok | bad-sha |
no-sha), STUB_SOURCE (marketplace base URL), STUB_SOURCE_KEY (marketplace key).
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
SOURCE_KEY = os.environ["STUB_SOURCE_KEY"]
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
        # The marketplace answers with a 302 to a presigned object-store URL.
        # Unredirected: the key goes to the marketplace only. urllib copies
        # ordinary headers onto the redirect, which hands the key to the store,
        # and the store refuses a presigned GET that carries a second credential.
        req.add_unredirected_header("Authorization", "Bearer " + SOURCE_KEY)
        try:
            body = urllib.request.urlopen(req, timeout=120).read()
        except urllib.error.HTTPError as e:
            return self.send_error(404 if e.code in (404, 410) else 502)
        except OSError:
            return self.send_error(502)
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
