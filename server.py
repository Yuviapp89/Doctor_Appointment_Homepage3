"""
Server entry point for Doctor's Appointment Web Application.
Runs a multi-threaded HTTP server hosting both the static frontend and REST API.
Zero external dependencies, standard Python 3.
"""

import os
import sys
import json
import mimetypes
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer

from backend.database import Database
from backend.auth_service import AuthService
from backend.chatbot_engine import ChatbotEngine
from backend.api_handler import APIHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
##PORT = 8000
PORT = int(os.environ.get("PORT", "8000"))

class HealthcareRequestHandler(SimpleHTTPRequestHandler):
    # Injected dependencies
    api_handler: APIHandler = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = dict(urllib.parse.parse_qsl(parsed.query))

        if path.startswith("/api/"):
            headers = {k: v for k, v in self.headers.items()}
            status, res_headers, body = self.api_handler.handle_request(
                method="GET",
                path=path,
                query_params=query_params,
                body_data=None,
                headers=headers
            )
            self._send_custom_response(status, res_headers, body)
            return

        # Serve index.html on root
        if path == "/" or path == "":
            self.path = "/index.html"

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = dict(urllib.parse.parse_qsl(parsed.query))

        if path.startswith("/api/"):
            content_length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(content_length) if content_length > 0 else b""
            body_data = {}
            if raw_body:
                try:
                    body_data = json.loads(raw_body.decode("utf-8"))
                except Exception:
                    body_data = {}

            headers = {k: v for k, v in self.headers.items()}
            status, res_headers, body = self.api_handler.handle_request(
                method="POST",
                path=path,
                query_params=query_params,
                body_data=body_data,
                headers=headers
            )
            self._send_custom_response(status, res_headers, body)
            return

        self.send_error(405, "Method Not Allowed")

    def _send_custom_response(self, status: int, headers: dict, body: bytes):
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Clean formatted console log
        sys.stderr.write(f"[{self.log_date_time_string()}] {self.address_string()} - {format % args}\n")


def run_server(port: int = PORT):
    # Initialize core services
    print("🚀 Initializing CarePulse Health backend database & services...")
    db = Database()
    auth_service = AuthService()
    chatbot_engine = ChatbotEngine(db)
    api_handler = APIHandler(db, auth_service, chatbot_engine)

    HealthcareRequestHandler.api_handler = api_handler

    ##server_address = ("", port)
    server_address = ("0.0.0.0", port)
    httpd = ThreadingHTTPServer(server_address, HealthcareRequestHandler)
    print(f"✨ CarePulse Healthcare Web App running at http://localhost:{port}/")
    print("📋 Credentials for Testing:")
    print("   • Guest   : No credentials needed (One-click login)")
    print("   • Patient : username: patient | password: healthcare")
    print("   • Admin   : username: admin   | password: admin")
    print("Press Ctrl+C to stop the server.")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server gracefully...")
        httpd.server_close()


if __name__ == "__main__":
    port = PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
