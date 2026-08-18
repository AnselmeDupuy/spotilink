import json
import urllib.request

import websockets

from .TwitchChatApi import TwitchChatApi

from ..auth.TokenManager import TokenManager

from ..chatBot.SpotifyApi import SpotifyApi

tokenManager = TokenManager()

class TwitchSocket:

    def __init__(self, main_client_id, access_token, bot_client_id=None):
        self.main_client_id = main_client_id
        self.main_access_token = access_token
        self.bot_tokens = tokenManager.load("twitch_bot")
        self.bot_access_token = self.bot_tokens["access_token"]
        self.bot_client_id = bot_client_id or self.bot_tokens.get("client_id") or self.main_client_id

        self.twitch_chat_api = TwitchChatApi(
            client_id=self.bot_client_id,
            app_access_token=self.bot_access_token,
            broadcaster_id=tokenManager.load("twitch")["user_id"],
            bot_user_id=tokenManager.load("twitch_bot")["user_id"]
        )

        self.ws = None
        self.session_id = None

        self.user_id = tokenManager.load("twitch")["user_id"]
        self.bot_user_id = tokenManager.load("twitch_bot")["user_id"]
        self.broadcaster_id = tokenManager.load("twitch")["user_id"]

        self.spotify_api = SpotifyApi(tokenManager)

        self.user_added_music = {}
        self.keepalive_count = 0

    def send_chat_message(self, text):
        payload = {
            "broadcaster_id": self.broadcaster_id,
            "sender_id": self.bot_user_id,
            "message": text,
        }

        request = urllib.request.Request(
            "https://api.twitch.tv/helix/chat/messages",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.bot_access_token}",
                "Client-Id": self.bot_client_id,
                "Content-Type": "application/json",
            },
        )

        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode("utf-8"))
            print("Sent message:", result)

    async def connect(self):

        async with websockets.connect(
            "wss://eventsub.wss.twitch.tv/ws"
        ) as ws:

            self.ws = ws

            while True:

                message = await ws.recv()
                data = json.loads(message)

                message_type = data["metadata"]["message_type"]

                if message_type == "session_welcome":

                    self.session_id = data["payload"]["session"]["id"]

                    print("Connected to Twitch!")
                    print("Session ID:", self.session_id)

                    self.user_id = self.get_user_id()

                    print("Twitch User ID:", self.user_id)

                    self.subscribe_to_chat()

                elif message_type == "session_keepalive":

                    self.keepalive_count += 1
                    print(f"\rKeepalive ({self.keepalive_count})\r", end="", flush=True)
                    
                elif message_type == "notification":


                    text = data["payload"]["event"]["message"].get("text", "")
                    user = data["payload"]["event"].get("chatter_user_name", "")
                    time = data["metadata"]["message_timestamp"].split("T")[1].split(".")[0]

                    if user == "spotilink":
                        print(f"bot command:", text)
                        continue

                    if "!" not in text:
                        print(f"{time} {user}: {text}")
                        continue
                    elif text.startswith("!"):
                        print(f"{time} {user}: {text}")
                        if text.startswith("!add "):
                            query = text.split(" ", 1)[1]

                            if "https://open.spotify.com/" in query:
                                try:
                                    track_uri = self.spotify_api.get_track_uri_from_url(query)
                                    track_name = self.spotify_api.get_track(track_uri.split(":")[-1])["name"]
                                    track_artist = self.spotify_api.get_track(track_uri.split(":")[-1])["artists"][0]["name"]

                                    try:
                                        self.spotify_api.add_to_queue(track_uri)
                                        self.twitch_chat_api.send_message(f"Adding to queue: {track_name} by {track_artist}, added by {user}")
                                        self.user_added_music[track_name] = user
                                    except ValueError as e:
                                        self.twitch_chat_api.send_message(str(e))
                                except ValueError as e:
                                    self.twitch_chat_api.send_message(str(e))
                            else:
                                self.twitch_chat_api.send_message("Invalid Spotify URL. Please provide a valid URL.")
                        elif text == "!help" or text == "!commands" or text == "!h":
                            self.twitch_chat_api.send_message("Available commands:")
                            self.twitch_chat_api.send_message("!help or !commands - Displays this help message.")
                            self.twitch_chat_api.send_message("!add <Spotify URL> - Adds a track to the queue.")
                            self.twitch_chat_api.send_message("!q - Displays the next 3 tracks in the queue.")
                        elif text == "!q" or text == "!queue":
                            try:
                                queue = self.spotify_api.display_queue()
                                queue = self.spotify_api.get_queue()
                                i = 0
                                for track in queue["queue"]:
                                    if i >= 3:
                                        break
                                    track_name = track["name"]
                                    track_artist = track["artists"][0]["name"]
                                    added_by = self.user_added_music.get(track_name, user)
                                    self.twitch_chat_api.send_message(f"{i + 1} - {track_name} by {track_artist} added by {added_by} ")
                                    i += 1
                            except ValueError as e:
                                self.twitch_chat_api.send_message(str(e))
                        else:
                            print("Received:", message_type)

    def get_user_id(self):
        try:
            request = urllib.request.Request(
                "https://api.twitch.tv/helix/users",
                headers={
                    "Authorization": f"Bearer {self.main_access_token}",
                    "Client-Id": self.main_client_id,
                }
            )

            with urllib.request.urlopen(request) as response:
                data = json.loads(response.read().decode())

            return data["data"][0]["id"]
        except (KeyError, IndexError):
            raise ValueError("User ID not found")

    def subscribe_to_chat(self):
        try:
            data = {
                "type": "channel.chat.message",
                "version": "1",
                "condition": {
                    "broadcaster_user_id": self.broadcaster_id,
                    "user_id": self.bot_user_id
                },
                "transport": {
                    "method": "websocket",
                    "session_id": self.session_id
                }
            }

            body = json.dumps(data).encode()

            request = urllib.request.Request(
                "https://api.twitch.tv/helix/eventsub/subscriptions",
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.bot_access_token}",
                    "Client-Id": self.bot_client_id,
                    "Content-Type": "application/json",
                }
            )

            with urllib.request.urlopen(request) as response:

                result = json.loads(response.read().decode())

                print("Chat subscription created!")
                print(result)
        except Exception as e:
            print("Error subscribing to chat:", e)

    # def ban_user(self, user_id):
    #     try:
    #         data = {
    #             "data": {
    #                 "user_id": user_id,
    #                 "broadcaster_id": self.broadcaster_id
    #             }
    #         }

    #         body = json.dumps(data).encode()

    #         request = urllib.request.Request(
    #             "https://api.twitch.tv/helix/moderation/bans",
    #             data=body,
    #             method="POST",
    #             headers={
    #                 "Authorization": f"Bearer {self.bot_access_token}",
    #                 "Client-Id": self.client_id,
    #                 "Content-Type": "application/json",
    #             }
    #         )

    #         with urllib.request.urlopen(request) as response:

    #             result = json.loads(response.read().decode())

    #             print(f"User {user_id} banned!")
    #             print(result)
    #     except Exception as e:
    #         print("Error banning user:", e)