from __future__ import annotations

import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


APP_DATA_DIR = (
    Path(os.environ["LOCALAPPDATA"])
    / "DesktopCalendar"
)

APP_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

TOKEN_FILE = APP_DATA_DIR / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/tasks",
]


def _credentials_file() -> Path:
    """Return bundled OAuth client credentials in source or PyInstaller."""

    if getattr(sys, "frozen", False):
        base_dir = Path(
            getattr(
                sys,
                "_MEIPASS",
                Path(sys.executable).parent,
            )
        )
    else:
        base_dir = (
            Path(__file__)
            .resolve()
            .parent
            .parent
        )

    return base_dir / "credentials.json"


def google_token_exists() -> bool:
    return TOKEN_FILE.exists()


def get_google_credentials() -> Credentials:
    credentials = None

    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES,
        )

    if (
        not credentials
        or not credentials.valid
    ):
        if (
            credentials
            and credentials.expired
            and credentials.refresh_token
        ):
            try:
                credentials.refresh(
                    Request()
                )
            except Exception:
                # If the saved grant has been revoked, perform a fresh OAuth
                # sign-in instead of leaving the application unusable.
                credentials = None

        if not credentials or not credentials.valid:
            credentials_file = _credentials_file()

            if not credentials_file.exists():
                raise FileNotFoundError(
                    "Google OAuth credentials were not found."
                )

            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file,
                SCOPES,
            )

            credentials = flow.run_local_server(
                port=0
            )

        TOKEN_FILE.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )

    return credentials
