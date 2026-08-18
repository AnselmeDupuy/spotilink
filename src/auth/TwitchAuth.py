# twitch_auth.py

import os
import urllib.parse
import urllib.request
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

from .TokenManager import TokenManager
from .Listener import wait_for_callback

from dotenv import load_dotenv

load_dotenv()

tokenManager = TokenManager()

CLIENT_ID = os.getenv("CLIENT_ID_TWITCH")
CLIENT_SECRET = os.getenv("CLIENT_SECRET_TWITCH")

REDIRECT_URI = "http://localhost:3000/callback"

SCOPES = [
    "channel:bot",
]


def get_auth_url():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
    }

    return (
        "https://id.twitch.tv/oauth2/authorize?"
        + urllib.parse.urlencode(params)
    )


def exchange_code(code):
    data = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }).encode()

    request = urllib.request.Request(
        "https://id.twitch.tv/oauth2/token",
        data=data,
        method="POST"
    )

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def refresh_access_token():
    tokens = tokenManager.load("twitch")
    refresh_token = tokens.get("refresh_token")

    if not refresh_token:
        raise ValueError("No Twitch refresh token found. Re-authenticate the Twitch account.")

    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }).encode("utf-8")

    request = urllib.request.Request(
        "https://id.twitch.tv/oauth2/token",
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    with urllib.request.urlopen(request) as response:
        new_tokens = json.loads(response.read().decode())

    tokenManager.save("twitch", {
        "access_token": new_tokens["access_token"],
        "refresh_token": new_tokens.get("refresh_token", refresh_token),
        "user_id": tokens.get("user_id"),
        "client_id": CLIENT_ID,
    })

    return tokenManager.load("twitch")

def get_user(access_token):
    request = urllib.request.Request(
        "https://api.twitch.tv/helix/users",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Client-Id": CLIENT_ID,
        }
    )

    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode())

    return data["data"][0]


def main():
    url = get_auth_url()

    print("Open this URL:")
    print(url)

    webbrowser.open(url)

    code = wait_for_callback(
        "localhost",
        3000
    )

    if code:
        tokens = exchange_code(code)

        user = get_user(tokens["access_token"])

        tokens["user_id"] = user["id"]
        tokens["client_id"] = CLIENT_ID

        tokenManager.save("twitch", tokens)

        print("Twitch authenticated!")
        print("User:", user["login"])
        print("User ID:", user["id"])

if __name__ == "__main__":
    main()