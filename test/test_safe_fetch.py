import http.server
import threading
import unittest
from collections.abc import Callable
from unittest import mock

import requests

from safe_fetch import guarded_session
from url_safety import is_public_address

SECRET = b"<p>INTERNAL-SECRET</p>"
BLOCKED_MESSAGE = "refusing to connect to non-public address"
TIMEOUT_S = 5


def _serve(handler: type[http.server.BaseHTTPRequestHandler]) -> http.server.HTTPServer:
    server = http.server.HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class _Secret(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()
        self.wfile.write(SECRET)

    def log_message(self, *args: object) -> None:
        pass


def _redirect_to(target: str) -> type[http.server.BaseHTTPRequestHandler]:
    class Redirect(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(302)
            self.send_header("Location", target)
            self.end_headers()

        def log_message(self, *args: object) -> None:
            pass

    return Redirect


def _allow_first_connection_only() -> Callable[[str], bool]:
    seen: list[str] = []

    def policy(address: str) -> bool:
        seen.append(address)
        return len(seen) == 1

    return policy


class TestGuardedSession(unittest.TestCase):
    def setUp(self) -> None:
        self.secret = _serve(_Secret)
        self.secret_url = f"http://127.0.0.1:{self.secret.server_port}/"

    def tearDown(self) -> None:
        self.secret.shutdown()
        self.secret.server_close()

    def assertRefused(self, url: str, policy: Callable[[str], bool]) -> None:
        with guarded_session(policy) as session, self.assertRaises(
            requests.ConnectionError
        ) as raised:
            session.get(url, timeout=TIMEOUT_S)
        self.assertIn(BLOCKED_MESSAGE, str(raised.exception))

    def test_loopback_is_refused_by_default(self) -> None:
        self.assertRefused(self.secret_url, is_public_address)

    def test_allowed_address_is_fetched(self) -> None:
        with guarded_session(lambda address: True) as session:
            response = session.get(self.secret_url, timeout=TIMEOUT_S)
        self.assertEqual(response.content, SECRET)

    def test_redirect_target_is_checked(self) -> None:
        redirect = _serve(_redirect_to(self.secret_url))
        self.addCleanup(redirect.server_close)
        self.addCleanup(redirect.shutdown)
        url = f"http://127.0.0.1:{redirect.server_port}/"
        with guarded_session(
            _allow_first_connection_only()
        ) as session, self.assertRaises(requests.ConnectionError):
            session.get(url, timeout=TIMEOUT_S)

    def test_hostname_resolving_to_loopback_is_refused(self) -> None:
        self.assertRefused(
            f"http://localhost:{self.secret.server_port}/", is_public_address
        )

    def test_environment_proxy_is_ignored(self) -> None:
        with mock.patch.dict(
            "os.environ", {"HTTP_PROXY": "http://93.184.216.34:9", "NO_PROXY": ""}
        ):
            with guarded_session(lambda address: True) as session:
                response = session.get(self.secret_url, timeout=TIMEOUT_S)
        self.assertEqual(response.content, SECRET)


if __name__ == "__main__":
    unittest.main()
