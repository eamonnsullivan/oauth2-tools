#!/usr/bin/env -S uv run
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
--------------------------------------------------------------------------
authorise.py · interactive one-time OAuth 2.0 flow for msmtp + Gmail
SMTP and Mu4e + Gmail mail.
--------------------------------------------------------------------------

Heavily inspired by the code in this blog:
https://linsnotes.com/posts/sending-email-from-raspberry-pi-using-msmtp-with-gmail-oauth2/

I just added some flexibility for multiple accounts.

"""

import pathlib
import sys
import argparse
from google_auth_oauthlib.flow import InstalledAppFlow

BASE_DIR = pathlib.Path(__file__).resolve().parent
DEFAULT_CLIENT_SECRET = BASE_DIR / "client_secret.json"  # OAuth client downloaded
DEFAULT_TOKEN_FILE = BASE_DIR / "credentials.json"  # output used by get_token.py
DEFAULT_LISTEN_PORT = 0  # 0 ⇒ default, 8888 ⇒ headless mode

SCOPES = ["https://mail.google.com/"]  # full Gmail SMTP scope


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="authorize.py",
        description="Run the interactive OAuth consent flow and save the credentials into a file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--client-secret",
        type=pathlib.Path,
        default=DEFAULT_CLIENT_SECRET,
        help="Path to client_secret.json file (default: %(default)s)",
    )
    parser.add_argument(
        "--token-file",
        type=pathlib.Path,
        default=DEFAULT_TOKEN_FILE,
        help="Path to output credentials.json file (default: %(default)s)",
    )
    parser.add_argument(
        "--listen-port",
        type=int,
        default=DEFAULT_LISTEN_PORT,
        help="Port for local HTTP server to listen on (default: %(default)s)",
    )
    return parser.parse_args()


def main() -> None:
    """Run the interactive OAuth consent flow and save credentials.json."""
    args = parse_args()
    print("EAMONN DEBUG: args", args)

    if not args.client_secret.exists():
        sys.exit(
            "❌  client_secret.json not found\n\n"
            "  To generate it:\n"
            "  1. Open https://console.cloud.google.com and create (or select) a project.\n"
            "  2. In the left menu choose  ▶ APIs & Services ▸ OAuth consent screen.\n"
            "     • Pick ‘External’, fill in the bare-minimum fields, and save.\n"
            "  3. Still under ▶ APIs & Services, go to ▸ Credentials ▸ “+ CREATE CREDENTIALS”\n"
            "     • Choose **OAuth client ID**.\n"
            "     • Application type → **Desktop app** (name it anything).\n"
            "  4. Click **Download JSON**.\n"
            "  5. Run this script again and use the `--client-secret` option to point to this downloaded json file. \n"
        )
    flow = InstalledAppFlow.from_client_secrets_file(
        args.client_secret,
        SCOPES,
    )

    open_browser = True if args.listen_port == 0 else False
    headline_prompt_message = f"""
    🔑  ACTION REQUIRED

     🚧 BEFORE YOU CONTINUE 🚧

         Make sure the SSH tunnel is already running; otherwise the server can’t
         receive the browser’s callback and the OAuth flow will fail.

            ssh -NT -L {args.listen_port}:localhost:{args.listen_port} <your-user>@<server-ip>

         1. Copy the URL below into a browser.
         2. Sign in with your Google account and click Allow.
         3. When browser shows “✅  All done – you may now close this tab/window.”, return here.
    """
    authorization_prompt_message = (
        None if args.listen_port == 0 else headline_prompt_message
    )
    creds = flow.run_local_server(
        port=args.listen_port,
        open_browser=open_browser,
        authorization_prompt_message=authorization_prompt_message,
        success_message=("✅  All done – you may now close this tab/window."),
    )
    args.token_file.write_text(creds.to_json())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nAborted by user.")
