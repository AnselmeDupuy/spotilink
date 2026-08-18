import asyncio

from .auth.TwitchAuth import CLIENT_ID as TWITCH_CLIENT_ID, refresh_access_token as refresh_twitch_access_token
from .auth.TwitchBotAuth import CLIENT_ID as TWITCH_BOT_CLIENT_ID, refresh_access_token as refresh_twitch_bot_access_token

from .chatBot.TwitchSocket import TwitchSocket

from .auth.TokenManager import TokenManager




tokenManager = TokenManager()

refresh_twitch_access_token()

try:
    refresh_twitch_bot_access_token()
except ValueError:
    pass

twitch_tokens = tokenManager.load("twitch")
twitch_bot_tokens = tokenManager.load("twitch_bot")

twitch_socket = TwitchSocket(
    TWITCH_CLIENT_ID,
    twitch_tokens["access_token"],
    bot_client_id=twitch_bot_tokens.get("client_id", TWITCH_BOT_CLIENT_ID),
)


async def main():
    await twitch_socket.connect()


if __name__ == "__main__":
    asyncio.run(main())