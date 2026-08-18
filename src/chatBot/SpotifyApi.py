import urllib.request
import urllib.parse
import base64
import json

from src.auth.SpotifyAuth import CLIENT_ID, CLIENT_SECRET


class SpotifyApi:

    def __init__(self, token_manager):
        self.token_manager = token_manager

        tokens = self.token_manager.load("spotify")

        self.access_token = tokens["access_token"]
        self.refresh_token = tokens["refresh_token"]

    def search_track(self, query):
        try:
            params = urllib.parse.urlencode({
                "q": query,
                "type": "track",
                "limit": 5
            })

            request = urllib.request.Request(
                f"https://api.spotify.com/v1/search?{params}",
                method="GET",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                }
            )

            with urllib.request.urlopen(request) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.refresh_access_token()
            if e.code == 401:
                raise ValueError("Invalid or expired access token")
            else:
                raise

    def play_track(self, uri):
        try:
            data = json.dumps({
                "uris": [uri]
            }).encode("utf-8")

            request = urllib.request.Request(
                "https://api.spotify.com/v1/me/player/play",
                data=data,
                method="PUT",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                }
            )

            with urllib.request.urlopen(request) as response:
                print("Playback started:", response.status)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.refresh_access_token()
            if e.code == 404:
                raise ValueError("No active device found. Please start playback on a device.")
            else:
                raise

    def add_to_queue(self, uri):
        try:
            request = urllib.request.Request(
                f"https://api.spotify.com/v1/me/player/queue?uri={urllib.parse.quote(uri)}",
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                }
            )

            with urllib.request.urlopen(request) as response:
                print("Track added to queue:", response.status)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.refresh_access_token()
            if e.code == 404:
                raise ValueError("No active device found. Please start playback on a device.")
            else:
                raise

    def get_track_uri_from_url(self, url):
        try:
            parsed = urllib.parse.urlparse(url)

            parts = parsed.path.split("/")

            if "track" not in parts:
                raise ValueError("URL is not a Spotify track URL")

            track_index = parts.index("track")

            if track_index + 1 >= len(parts):
                raise ValueError("No track ID found")

            track_id = parts[track_index + 1]

            return f"spotify:track:{track_id}"
        except Exception as e:
            raise ValueError(f"Invalid Spotify track URL: {e}")
    
    def get_track(self, track_id):
        try:
            request = urllib.request.Request(
                f"https://api.spotify.com/v1/tracks/{track_id}",
                method="GET",
                headers={
                    "Authorization": f"Bearer {self.access_token}"
                }
            )

            with urllib.request.urlopen(request) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 401:
                self.refresh_access_token()
            if e.code == 404:
                raise ValueError("Track not found")
            else:
                raise

    def get_queue(self):

        try:

            request = urllib.request.Request(
                "https://api.spotify.com/v1/me/player/queue",
                method="GET",
                headers={
                    "Authorization": f"Bearer {self.access_token}"
                }
            )

            with urllib.request.urlopen(request) as response:
                return json.loads(response.read().decode("utf-8"))

        except urllib.error.HTTPError as e:

            if e.code == 401:
                self.refresh_access_token()

                return self.get_queue()

            if e.code == 404:
                raise ValueError(
                    "No active device found. Please start playback on a device."
                )

            raise

    def display_queue(self):
        data = self.get_queue()

        queue = data["queue"]

        if not queue:
            return "Queue is empty."

        i = 0

        for track in queue:
            if i >= 3:
                break
            track_name = track["name"]
            track_artist = track["artists"][0]["name"]
            print(f"- {track_name} by {track_artist}")
            i += 1

        return "\n".join(
            f"- {track['name']}"
            for track in queue
        )

    def refresh_access_token(self):

        credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"

        auth = base64.b64encode(
            credentials.encode()
        ).decode()

        data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }).encode()

        request = urllib.request.Request(
            "https://accounts.spotify.com/api/token",
            data=data,
            method="POST",
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )

        with urllib.request.urlopen(request) as response:
            tokens = json.loads(response.read().decode())

        self.access_token = tokens["access_token"]

        if "refresh_token" in tokens:
            self.refresh_token = tokens["refresh_token"]

        self.token_manager.save("spotify", {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
        })

        print("Spotify access token refreshed.")
