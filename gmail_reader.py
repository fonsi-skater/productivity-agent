import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    credentials = None

    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE), SCOPES
        )

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE), SCOPES
        )
        credentials = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=credentials)


def main():
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            "credentials.json is missing from the project folder."
        )

    service = get_gmail_service()

    profile = service.users().getProfile(userId="me").execute()
    print("Gmail authorization successful.")
    print(f"Messages in mailbox: {profile.get('messagesTotal', 'unknown')}")

    results = service.users().messages().list(
        userId="me",
        maxResults=5,
        q="newer_than:30d {invite.ics meeting invitation}"
    ).execute()

    messages = results.get("messages", [])
    print(f"Matching recent messages found: {len(messages)}")

    for message in messages:
        details = service.users().messages().get(
            userId="me",
            id=message["id"],
            format="metadata",
            metadataHeaders=["Subject", "From", "Date"]
        ).execute()

        headers = {
            header["name"].lower(): header["value"]
            for header in details.get("payload", {}).get("headers", [])
        }

        print("-" * 40)
        print("Date:", headers.get("date", "Unknown"))
        print("From:", headers.get("from", "Unknown"))
        print("Subject:", headers.get("subject", "No subject"))


if __name__ == "__main__":
    main()
