import urllib.request
import json


class TwitchChatApi:

    def __init__(
        self,
        client_id,
        app_access_token,
        broadcaster_id,
        bot_user_id
    ):
        self.client_id = client_id
        self.app_access_token = app_access_token
        self.broadcaster_id = broadcaster_id
        self.bot_user_id = bot_user_id

    def send_message(self, message):

        payload = {
            "broadcaster_id": self.broadcaster_id,
            "sender_id": self.bot_user_id,
            "message": message
        }

        request = urllib.request.Request(
            "https://api.twitch.tv/helix/chat/messages",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.app_access_token}",
                "Client-Id": self.client_id,
                "Content-Type": "application/json"
            }
        )

        with urllib.request.urlopen(request) as response:
            return json.loads(
                response.read().decode("utf-8")
            )

