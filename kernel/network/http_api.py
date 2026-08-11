"""N2.4 — HTTP transport for network fabric (stdlib only)."""

from __future__ import annotations
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional
from urllib.parse import urlparse
from kernel.network.fabric import NetworkNode
from kernel.network.protocol import ReplicationRequest


class _Handler(BaseHTTPRequestHandler):
    node: NetworkNode

    def log_message(self, fmt, *args):
        pass

    def _json(self, code: int, obj):
        body = json.dumps(obj, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n) if n else b"{}"
        return json.loads(raw.decode() or "{}")

    def do_GET(self):
        path = urlparse(self.path).path
        node = self.node
        if path == "/identity":
            self._json(200, json.loads(node.identity.model_dump_json()))
        elif path == "/health":
            h = node.head()
            self._json(200, {"status": "ok" if h.chain_valid else "degraded", "head": h.model_dump()})
        elif path == "/replication/head":
            self._json(200, node.head().model_dump())
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        node = self.node
        data = self._read_json()
        if path == "/replication/pull":
            from_seq = int(data.get("from_sequence", 0))
            req = node.build_push_request(data.get("receiver_node", "unknown"), from_sequence=from_seq)
            self._json(200, json.loads(req.model_dump_json()))
        elif path == "/replication/push":
            try:
                req = ReplicationRequest.model_validate(data)
            except Exception as e:
                self._json(400, {"error": str(e)})
                return
            resp = node.handle_request(req)
            self._json(200, json.loads(resp.model_dump_json()))
        else:
            self._json(404, {"error": "not found"})


class NetworkHTTPServer:
    def __init__(self, node: NetworkNode, host: str = "127.0.0.1", port: int = 0):
        handler = type("H", (_Handler,), {"node": node})
        self.httpd = HTTPServer((host, port), handler)
        self.node = node
        self.host, self.port = self.httpd.server_address
        self._thread: Optional[threading.Thread] = None

    def start(self) -> "NetworkHTTPServer":
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self.httpd.shutdown()

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


def http_push(base_url: str, req: ReplicationRequest) -> dict:
    import urllib.request
    data = req.model_dump_json().encode()
    r = urllib.request.Request(
        f"{base_url}/replication/push", data=data,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(r, timeout=10) as resp:
        return json.loads(resp.read().decode())


def http_head(base_url: str) -> dict:
    import urllib.request
    with urllib.request.urlopen(f"{base_url}/replication/head", timeout=10) as resp:
        return json.loads(resp.read().decode())
