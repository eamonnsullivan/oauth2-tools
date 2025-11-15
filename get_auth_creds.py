#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "google-auth",
#     "google-auth-httplib2",
#     "google-auth-oauthlib",
# ]
# ///

"""-----------------------------------------------------------
get_auth_creds.py -- retrieve several fields from OAuth 2.0
credentials file and output them to standard out, for use in
configuration scripts, such as OfflineIMAP.

For example:
get_auth_creds.py my-credentials.json client_id
get_auth_creds.py my-credentials.json client_secret
get_auth_creds.py my-credentials.json refresh_token

If you just need the client token (e.g., to login), see get_token.py.
"""

import sys
import argparse
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        prog="get_auth_creds.py",
        description="Return various fields from an OAuth 2.0 credentials file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("credentials")
    parser.add_argument(
        "field",
        choices=["client_id", "client_secret", "refresh_token"],
        help="The field to query.",
    )
    return parser.parse_args()


def get_field(credentials: Path, field: str) -> str:
    """Return the given field from the given creds file"""

    if not credentials.exists():
        sys.exit(f"{credentials} file not found.")

    creds = Credentials.from_authorized_user_file(credentials)

    if not creds.valid:
        if creds.expired and creds.refresh_token:
            print("Refreshing expired credentials.")
            creds.refresh(Request())
            credentials.write_text(creds.to_json())
        else:
            sys.exit("No valid refresh-token - re-run authorise.py")

    if field == "client_id":
        return creds.client_id
    elif field == "client_secret":
        return creds.client_secret
    elif field == "refresh_token":
        return creds.refresh_token
    else:
        raise ValueError(f"Unknown field: {field}")


if __name__ == "__main__":
    args = parse_args()
    creds_file = args.credentials
    field = args.field
    result = get_field(Path(creds_file), field)
    print(f"{result}")
