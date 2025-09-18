from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os

# Google Drive scopes (read/write access)
SCOPES = ["https://www.googleapis.com/auth/drive"]

def main():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("gdrive_mcp/credentials.json", SCOPES)
            creds = flow.run_local_server(port=8080)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    print("✅ Token saved to token.pickle")

if __name__ == "__main__":
    main()
