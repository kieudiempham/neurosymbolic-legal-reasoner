"""HTTP API and demo page for the pipeline (standard library only; one user at a time, enough for a demo).

    PYTHONPATH=src .venv_diag/Scripts/python -m legalkb.server --sample --port 8000     # then open http://localhost:8000

    POST /api/chat     {"session_id": "..." | null, "message": "..."}  -> answer of the turn (chat.Dialogue.say)
    POST /api/reset    {"session_id": "..."}                           -> next message starts a new question
    GET  /api/runs     latest runs                       GET /api/run/<id>   one run as text (trace.show_run)
    GET  /             the demo page (web/index.html)
Every turn is stored as a run in data/legalkb/runs.sqlite, as with the terminal.
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from .ask import Asker
from .chat import Dialogue
from .trace import show_run

WEB = Path(__file__).with_name("web")
DIALOGUE: Dialogue | None = None


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        runs = DIALOGUE.asker.runs
        if self.path in ("/", "/index.html"):
            self._send(200, (WEB / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/runs":
            rows = runs.execute("SELECT run_id, time, session_id, turn, question FROM runs ORDER BY run_id DESC "
                                "LIMIT 50").fetchall()
            self._json([dict(zip(["run_id", "time", "session_id", "turn", "question"], r)) for r in rows])
        elif self.path.startswith("/api/run/"):
            self._send(200, show_run(runs, int(self.path.rsplit("/", 1)[1])).encode("utf-8"),
                       "text/plain; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            if self.path == "/api/chat":
                self._json(DIALOGUE.say(body.get("session_id"), body["message"]))
            elif self.path == "/api/reset":
                DIALOGUE.reset(body.get("session_id", ""))
                self._json({"ok": True})
            else:
                self._send(404, b"not found", "text/plain")
        except Exception as e:  # noqa: BLE001
            self._json({"error": f"{type(e).__name__}: {e}"}, 500)

    def log_message(self, fmt, *args) -> None:
        sys.stderr.write("%s %s\n" % (self.command, self.path))


def main() -> None:
    global DIALOGUE
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true", help="use the hand-encoded sample KB")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    DIALOGUE = Dialogue(Asker(args.sample))
    print(f"demo: http://localhost:{args.port}  (KB: {DIALOGUE.asker.kb})", flush=True)
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
