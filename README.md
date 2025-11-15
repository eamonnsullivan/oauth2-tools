# Managing OAuth 2.0-style credentials

A small collection of scripts for managing my credentials for gmail (and, hopefully, others in the future). I use them to configure [Mu/Mu4e](https://www.djcbsoftware.nl/code/mu/), an offline email client for Emacs, [msmtp](https://marlam.de/msmtp/), an SMTP client, and [OfflineIMAP](https://github.com/OfflineIMAP/offlineimap3), an IMAP mailbox synchronising utility, to securely connect to and send through multiple gmail accounts. Mu4e, msmtp and OfflineIMAP can be configured for multiple accounts and have various smarts for choosing between them.

These scripts are very heavily inspired by [Kuibin Lin's blog](https://linsnotes.com/posts/sending-email-from-raspberry-pi-using-msmtp-with-gmail-oauth2/) for setting up a Raspberry Pi to use gmail as a relay (which I also needed to do). The main changes I did was to use [uv](https://github.com/astral-sh/uv) for the package manager and refactoring the code a bit to handle multiple gmail accounts.

The scripts (or at least my changes) are quite new and *not* battle tested, but I hope others find them useful or instructive.

## Prerequisites
 * You'll need to set up an OAuth 2.0 client using Google's [cloud console](https://console.cloud.google.com/).
   * Create a new project, or use an existing one.
   * Navigate to API & Services, then to OAuth consent screen, click Get Started.
   * Fill out the form. The important bit is to choose 'External.'
   * Create new OAuth client (API & Services -> Credentials -> Create Credentials -> OAuth client ID)
   * For Application Type choose 'Desktop App.'
   * When created, download the client secret (json) file.

You'll need to do this for each gmail account you want to use.

## Security considerations

The secrets JSON file and the `credentials.json` files generated with this tool (see below) are sensitive data. Store them carefully and guard them like you would a password (e.g., ideally encrypted at rest). At a bare minimum, make them accessible only to you.

```
chmod 0600 *.json
```

If they are lost or stolen, you can disable the client id in the Google console and create another one.
## Usage

For each account you want to access, run `authorise.py` to generate a `credentials.json` file.

```
authorise.py --client-secret client_secret.json \
             --token-file credentials.json \
             --listen-port 0
``

**client-secret** -- This is the json file you downloaded when the client was created.

**token-file** -- This is where the credentials will be saved. It will be used by the other scripts to generate an access token or provide the settings you'll need.

**listen-port** -- If you set this to 0 (the default), the flow will run locally (on some random available port), opening a browser tab for you automatically. If you set it to 8888, the url you need to open will be printed for you to copy & paste to a browser. This latter is for when you are running this on a headless server via an SSH connection. You need to set up a tunnel on your local machine to complete the process.

```
get_token.py --credentials-file credentials.json

``
**credentials-file** -- The credentials file created by the `authorise.py` script.

The output (to stdout) is a valid access token, based on the credentials file. It will be refreshed automatically, if necessary.

```
get_auth_creds.py credentials.json client_id
get_auth_creds.py credentials.json client_secret
get_auth_creds.py credentials.json refresh_token
```
Given the credentials file to use, output (to stdout) the value of the given field.

## Example uses with msmtp

What *I* do is create symbolic links in my local `~/bin` directory (which is in my path), like so:
```
ln -s ~/git/oauth2-tools/get_token.py ~/bin/get_token
ln -s ~/git/oauth2-tools/get_auth_creds.py ~/bin/get_auth_creds
```

In `msmtp` I use the `get_token` script like this:
```
defaults
logfile ~/.maildir/msmtp.log
tls_trust_file ~/.maildir/certificates/root-certificates.pem

account gmail-1
auth oauthbearer
host smtp.gmail.com
port 587
protocol smtp
from user.name@gmail.com
user user.name@gmail.com
passwordeval "get_token -c ~/path/to/my/gmail1/credentials.json"
tls on
tls_starttls on

account gmail-2
auth oauthbearer
host smtp.gmail.com
port 587
protocol smtp
from another.name@gmail.com
user another.name@gmail.com
passwordeval "get_token -c ~/path/to/my/gmail2/credentials.json"
tls on
tls_starttls on

account default : gmail-1
```

In OfflineIMAP, I can provide a path to a Python file with some helpers functions. However, I find that OfflineIMAP can get confused if that file contains any dependencies beyond the standard library, so this file just contains a very simple wrapper around the command-line scripts. Here's an example from my `offlineimap_helper.py`:

```python
def get_refresh_token(credentials: str) -> str:
    """
    Retrieve the OAuth2 refresh token from the given credentials.

    Args: credentials (str): The credentials.json file from which to
        retrieve the client secret.

    Returns:
        str: The retrieved client refresh token.

    """
    return check_output(
        [
            "get_auth_creds",
            credentials,
            "refresh_token"
        ],
        encoding="utf-8",
        env=os.environ
    ).strip()

```

I use this in my `.offlineimap` config file like this:

```
[general]
accounts = Gmail1,Gmail2
pythonfile = ~/bin/offlineimap_helper.py

[Account Gmail1]
localrepository = Local
remoterepository = Remote
synclabels = yes

[Repository Local]
type = GmailMaildir
localfolders = ~/.maildir/gmail-1/

[Repository Remote]
type = Gmail
auth_mechanisms = XOAUTH2
oauth2_client_id_eval = get_client_id("/path/to/my/gmail1/credentials.json")
oauth2_client_secret_eval = get_client_secret("/path/to/my/gmail1/credentials.json")
oauth2_request_url = https://oauth2.googleapis.com/token
oauth2_refresh_token_eval = get_refresh_token("/path/to/my/gmail1/credentials.json")
remotehost = imap.gmail.com
remoteuser = user.name@gmail.com
ssl = yes
sslcacertfile = ~/.maildir/certificates/root-certificates.pem

[Account Gmail2]
localrepository = Local2
remoterepository = Remote2
synclabels = yes
maxage = 60

[Repository Local2]
type = GmailMaildir
localfolders = ~/.maildir/gmail-svp/

[Repository Remote2]
type = Gmail
auth_mechanisms = XOAUTH2
oauth2_client_id_eval = get_client_id("/path/to/my/gmail2/credentials.json")
oauth2_client_secret_eval = get_client_secret("/path/to/my/gmail2/credentials.json")
oauth2_request_url = https://oauth2.googleapis.com/token
oauth2_refresh_token_eval = get_refresh_token("/path/to/my/gmail2/credentials.json")
remotehost = imap.gmail.com
remoteuser = another.name@gmail.com
ssl = yes
sslcacertfile = ~/.maildir/certificates/root-certificates.pem
```
