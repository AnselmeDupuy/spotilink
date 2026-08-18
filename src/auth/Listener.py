from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


class OAuthCallbackHandler(BaseHTTPRequestHandler):

    authorization_code = None

    def do_GET(self):

        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)

        OAuthCallbackHandler.authorization_code = \
            query.get("code", [None])[0]

        self.send_response(200)
        self.end_headers()

        self.wfile.write(
            b"Authorization successful! You can close this window."
        )


def wait_for_callback(host, port):

    server = HTTPServer(
        (host, port),
        OAuthCallbackHandler
    )

    print(f"Waiting for OAuth callback on {host}:{port}...")

    server.handle_request()

    return OAuthCallbackHandler.authorization_code