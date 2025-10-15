from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, json, pickle
from passlib.hash import bcrypt
from google_drive_integration import GoogleDriveAPIClient
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

app = FastAPI()

USERS_FILE = "users.json"
TOKENS_DIR = "tokens"
SCOPES = ["https://www.googleapis.com/auth/drive"]

os.makedirs(TOKENS_DIR, exist_ok=True)

class UserAuth(BaseModel):
    user_id: str
    password: str

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def authenticate_google(user_id: str):
    """Run Google OAuth and save token for user"""
    token_file = os.path.join(TOKENS_DIR, f"{user_id}_token.pickle")
    creds = None

    if os.path.exists(token_file):
        with open(token_file, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Must have a valid credentials.json file
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=8080)  # opens browser

        with open(token_file, "wb") as f:
            pickle.dump(creds, f)

    return True

@app.get("/")
def sample():
    """Demo sample endpoint"""
    return {
        "message": "🚀 FastAPI is running!",
        "tip": "Try POST /auth with user_id and password to log in."
    }

@app.get("/health")
def health_check():
    """Simple health check endpoint"""
    users = load_users()
    return {
        "status": "ok",
        "users_registered": len(users),
        "tokens_dir": os.path.abspath(TOKENS_DIR)
    }


@app.post("/auth")
def auth(data: UserAuth):
    users = load_users()

    # Case 1: New user → create account
    if data.user_id not in users:
        hashed_pw = bcrypt.hash(data.password[:72])
        users[data.user_id] = {"password": hashed_pw}
        save_users(users)
        authenticate_google(data.user_id)
        return {"message": f"✅ User '{data.user_id}' created, Google token saved, and logged in."}

    # Case 2: Existing user → check password
    if not bcrypt.verify(data.password[:72], users[data.user_id]["password"]):
        raise HTTPException(status_code=401, detail="❌ Invalid password")

    # Case 3: Existing user but no token → run OAuth again
    token_file = os.path.join(TOKENS_DIR, f"{data.user_id}_token.pickle")
    if not os.path.exists(token_file):
        authenticate_google(data.user_id)
        return {"message": f"✅ User '{data.user_id}' re-authenticated and token saved"}

    # Case 4: Existing user with valid token
    client = GoogleDriveAPIClient(data.user_id)
    if client.authenticate():
        return {"message": f"✅ Logged in as {data.user_id}"}
    else:
        raise HTTPException(status_code=500, detail="❌ Token error")
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9000)