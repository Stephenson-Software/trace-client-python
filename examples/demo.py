"""A self-contained run of trace-client against a stand-in trace server.

Starts a tiny HTTP server on a free loopback port that answers
``POST /api/metrics`` the way a trace server does (``201``), points a
``TraceClient`` at it, reports a few events, and prints what reached the
server. Then shows the opt-outs: the same constructor with
``DO_NOT_TRACK=1``, with ``enabled="false"`` and with no key.

Nothing leaves the machine. Run from the repository root:

    python examples/demo.py
"""
import json
import os
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from trace_client import TraceClient, __version__, allows_reporting  # noqa: E402

received = []


class StandIn(BaseHTTPRequestHandler):
    """Answers like a trace server: 201 for every POST to /api/metrics."""

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        received.append((self.path, self.headers.get("Authorization"),
                         self.headers.get("User-Agent"), json.loads(body)))
        self.send_response(201 if self.path == "/api/metrics" else 404)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *args):
        pass


def main():
    for name in ("TRACE_USAGE_REPORTING", "DO_NOT_TRACK"):
        os.environ.pop(name, None)
    server = ThreadingHTTPServer(("127.0.0.1", 0), StandIn)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d" % server.server_address[1]

    print("trace-client-python %s, stand-in trace server on a loopback port\n" % __version__)
    with tempfile.TemporaryDirectory() as settings_dir:
        trace = TraceClient(url, "demo-game", "1.4.0", key="demo-key",
                            enabled=allows_reporting("true"),
                            install_id_file=os.path.join(settings_dir, "trace-install-id"))
        print("enabled=%s  disabled_reason=%s" % (trace.enabled, trace.disabled_reason))
        trace.report("startup")
        trace.report("world-load", tags={"kind": "procedural"})
        trace.report("level-complete", value=42.5, tags={"level": "3"})
        trace.close()  # drains the queue before returning

    print("\nThe server received %d events:" % len(received))
    path, authorization, user_agent, _ = received[0]
    print("  POST %s" % path)
    print("  Authorization: %s" % authorization)
    print("  User-Agent: %s" % user_agent)
    for _, _, _, event in received:
        install = event.get("tags", {}).get("install")
        if install:  # a fresh random UUID each run; shortened for the screen
            event["tags"]["install"] = install[:8] + "..."
        print("  " + json.dumps(event, separators=(",", ":")))
    server.shutdown()

    print("\nEvery opt-out yields a client that sends nothing:")
    os.environ["DO_NOT_TRACK"] = "1"
    off = TraceClient(url, "demo-game", "1.4.0", key="demo-key")
    print("  DO_NOT_TRACK=1       -> enabled=%s  disabled_reason=%r" % (off.enabled, off.disabled_reason))
    del os.environ["DO_NOT_TRACK"]
    off = TraceClient(url, "demo-game", "1.4.0", key="demo-key", enabled="false")
    print("  enabled=\"false\"      -> enabled=%s  disabled_reason=%r" % (off.enabled, off.disabled_reason))
    off = TraceClient(url, "demo-game", "1.4.0", key="")
    print("  key=\"\"               -> enabled=%s  disabled_reason=%r" % (off.enabled, off.disabled_reason))


if __name__ == "__main__":
    main()
