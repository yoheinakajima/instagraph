import http.server
import threading
import unittest

import main

SECRET_TEXT = "INTERNAL-SECRET"


class _Secret(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"<p>{SECRET_TEXT}</p>".encode())

    def log_message(self, *args: object) -> None:
        pass


class TestScrapeTextFromUrl(unittest.TestCase):
    def setUp(self) -> None:
        self.server = http.server.HTTPServer(("127.0.0.1", 0), _Secret)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def assertNotScraped(self, url: str) -> None:
        with self.assertLogs(level="WARNING") as logs:
            result = main.scrape_text_from_url(url)
        self.assertNotIn(SECRET_TEXT, result)
        self.assertTrue(result.startswith("Error:"))
        self.assertIn(
            "refusing to connect to non-public address", "\n".join(logs.output)
        )

    def test_internal_url_is_not_scraped(self) -> None:
        self.assertNotScraped(f"http://127.0.0.1:{self.server.server_port}/")

    def test_hostname_resolving_internally_is_not_scraped(self) -> None:
        self.assertNotScraped(f"http://localhost:{self.server.server_port}/")

    def test_unsupported_scheme_returns_error(self) -> None:
        self.assertTrue(
            main.scrape_text_from_url("httpx://example.com/").startswith("Error:")
        )


if __name__ == "__main__":
    unittest.main()
