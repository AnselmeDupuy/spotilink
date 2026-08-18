# SpotifyLink

## Requirements

- Python 3.13 or later from https://www.python.org
- The built-in `venv` module, which normally ships with Python

## Quick Start

1. Download the git repo.

2. Create a virtual environment at the root of the project:

```bash
python -m venv .venv
```

If `python -m venv` is not available on your machine, reinstall Python and make sure the standard library components, including `venv`, are included.

3. Install the Python dependencies inside the virtual environment:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

4. Copy `.env.dist` to `.env`, then fill in all required secrets and IDs.

5. Authenticate the accounts you want to use.

Each account has its own authentication entry point:

```bash
python -m src.auth.SpotifyAuth
python -m src.auth.TwitchAuth
python -m src.auth.TwitchBotAuth
```

The bot account is optional. If you use `TwitchAuth` and `TwitchBotAuth`, remember that they are two different accounts, so you must be connected to the account you want to authenticate before running each command.

6. Start the app with the batch file:

```bat
PyVenv.bat
```

`PyVenv.bat` activates the virtual environment and launches `python -m src.main` for you.

## Notes

- Make sure the `.env` file is complete before authenticating.
- If you do not want to use a bot account, you can skip `TwitchBotAuth`.
