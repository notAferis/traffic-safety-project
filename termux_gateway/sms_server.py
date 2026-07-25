#!/usr/bin/env python3
"""
Local SMS + call gateway, runs on the Android phone under Termux.

Accepts POST /sms with JSON {"recipients": ["0540..."], "message": "..."}
and sends each via termux-sms-send (Termux:API), using the phone's own SIM.

Accepts POST /call with JSON {"recipients": ["0540..."]} and places a real
phone call via termux-telephony-call, using the phone's own SIM. Only dials
the first recipient — a phone call ties up the SIM's one call slot, so
dialing a list back-to-back the way SMS does isn't meaningful. This is meant
as an attention-getting nudge ("check your SMS"), not a way to deliver a
spoken message — that's still handled by the (online, mnotify-based) voice
alert path.

No internet or external API involved in either endpoint.

Start with:
    python sms_server.py

Optionally set an auth token so random devices on the same Wi-Fi can't
trigger SMS sends/calls through your phone:
    SMS_GATEWAY_TOKEN=some-secret python sms_server.py
"""
import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("SMS_GATEWAY_PORT", "8080"))
AUTH_TOKEN = os.environ.get("SMS_GATEWAY_TOKEN", "")


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path == "/sms":
            self._handle_sms()
        elif self.path == "/call":
            self._handle_call()
        else:
            self._send_json(404, {"error": "not found"})

    def _handle_sms(self):
        if AUTH_TOKEN and self.headers.get("X-Auth-Token") != AUTH_TOKEN:
            self._send_json(401, {"error": "unauthorized"})
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length))
            recipients = data["recipients"]
            message = data["message"]
        except Exception as e:
            self._send_json(400, {"error": f"bad request: {e}"})
            return

        results = {}
        for number in recipients:
            try:
                proc = subprocess.run(
                    ["termux-sms-send", "-n", number, message],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                results[number] = (
                    "sent" if proc.returncode == 0 else f"failed: {proc.stderr.strip()}"
                )
            except Exception as e:
                results[number] = f"error: {e}"

        self._send_json(200, {"results": results})

    def _handle_call(self):
        if AUTH_TOKEN and self.headers.get("X-Auth-Token") != AUTH_TOKEN:
            self._send_json(401, {"error": "unauthorized"})
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(length))
            recipients = data["recipients"]
            if not recipients:
                raise ValueError("recipients list is empty")
        except Exception as e:
            self._send_json(400, {"error": f"bad request: {e}"})
            return

        # Only dial the first recipient — a phone call occupies the SIM's one call slot,
        # so calling every recipient in sequence the way SMS does isn't meaningful/reliable.
        number = recipients[0]
        try:
            proc = subprocess.run(
                ["termux-telephony-call", number],
                capture_output=True,
                text=True,
                timeout=15,
            )
            result = "dialed" if proc.returncode == 0 else f"failed: {proc.stderr.strip()}"
        except Exception as e:
            result = f"error: {e}"

        self._send_json(200, {"results": {number: result}})

    def log_message(self, format, *args):
        print(f"[sms-gateway] {self.address_string()} - {format % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"SMS gateway listening on 0.0.0.0:{PORT}")
    server.serve_forever()
