#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "google-auth",
#     "google-auth-httplib2",
#     "google-auth-oauthlib",
#     "requests",
# ]
# ///


"""
get_token.py
============

Heavily inspired by the code in this blog:
https://linsnotes.com/posts/sending-email-from-raspberry-pi-using-msmtp-with-gmail-oauth2/

I just added some flexibility for multiple accounts.

"""

import pathlib
import sys
import argparse
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

BASE_DIR = pathlib.Path(__file__).resolve().parent
DEFAULT_TOKEN_FILE = BASE_DIR / "credentials.json"  # produced by authorize.py

SCOPES = ["https://mail.google.com/"]  # full Gmail SMTP scope


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="get_token.py",
        description="Return a fresh OAuth 2.0 access-token for Gmail SMTP.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--credentials-file",
        type=pathlib.Path,
        default=DEFAULT_TOKEN_FILE,
        help="Path to credentials.json file (default: %(default)s)",
    )
    return parser.parse_args()


def fresh_token(token_file: pathlib.Path) -> str:
    """
    Return a valid access-token, refreshing credentials if required.
    Exits with an error message (non-zero code) if no usable refresh-token
    is present.
    """
    if not token_file.exists():
        sys.exit(f"{token_file} missing – run authorize.py first")

    creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            # Refresh
            creds.refresh(Request())
            token_file.write_text(creds.to_json())
        else:
            sys.exit("No valid refresh-token – re-run authorize.py")

    return creds.token


# ─── CLI entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # msmtp reads whatever is printed to stdout.
    print(fresh_token(parse_args().credentials_file))
