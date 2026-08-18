import os
import urllib.parse
import urllib.request
import base64
import json
import webbrowser

from .TokenManager import TokenManager

from dotenv import load_dotenv

load_dotenv()

tokenManager = TokenManager()

try:
    from .Listener import wait_for_callback
except ImportError:
    from Listener import wait_for_callback

CLIENT_ID = os.getenv("CLIENT_ID_SPotify")
CLIENT_SECRET = os.getenv("CLIENT_SECRET_SPotify")

REDIRECT_URI = "http://127.0.0.1:8000/callback"

SCOPES = [
    "user-read-playback-state",
    "user-modify-playback-state",
]


def get_auth_url():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
    }

    return (
        "https://accounts.spotify.com/authorize?"
        + urllib.parse.urlencode(params)
    )


def exchange_code(code):
    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }).encode()

    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"

    encoded_credentials = base64.b64encode(
        credentials.encode()
    ).decode()

    request = urllib.request.Request(
        "https://accounts.spotify.com/api/token",
        data=data,
        method="POST"
    )

    request.add_header(
        "Authorization",
        f"Basic {encoded_credentials}"
    )

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def main():
    url = get_auth_url()

    print("Open this URL:")
    print(url)

    webbrowser.open(url)

    code = wait_for_callback(
        "127.0.0.1",
        8000
    )

    if code:
        tokens = exchange_code(code)
        tokenManager.save("spotify", tokens)
        print("Spotify authenticated!")


if __name__ == "__main__":
    main()

