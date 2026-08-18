import json

FILE = "src/tokens.json"

class TokenManager:
    def save(self, service, tokens):
        try:
            with open(FILE, "r") as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}

        existing = data.get(service, {})

        data[service] = {
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token", existing.get("refresh_token")),
            "user_id": tokens.get("user_id", existing.get("user_id")),
            "client_id": tokens.get("client_id", existing.get("client_id")),
        }

        with open(FILE, "w") as file:
            json.dump(data, file, indent=4)


    def load(self, service):
        with open(FILE, "r") as file:
            data = json.load(file)

        return data[service]