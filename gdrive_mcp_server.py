import os, json
from getpass import getpass
from mcp.server.fastmcp import FastMCP
from google_drive_integration import GoogleDriveAPIClient
from passlib.hash import bcrypt

mcp = FastMCP("gdrive")
USERS_FILE = "users.json"
TOKENS_DIR = "tokens"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}

def login_user():
    os.makedirs(TOKENS_DIR, exist_ok=True)
    users = load_users()

    if not users:
        print("⚠️ No users found. Run auth_setup.py first.")
        return None

    print("Existing users:", ", ".join(users.keys()))
    user_id = input("Enter user ID: ").strip()
    if user_id not in users:
        print(f"❌ User {user_id} not found!")
        return None

    password = getpass("Enter password: ").strip()[:72]
    if not bcrypt.verify(password, users[user_id]["password"]):
        print("❌ Incorrect password!")
        return None

    # Load token for Google Drive
    client = GoogleDriveAPIClient(user_id)
    if client.authenticate():
        print(f"✅ Logged in as {user_id}")
        return client
    else:
        print(f"❌ Failed to load token for {user_id}")
        return None

# Login at startup
gdrive_client = login_user()
if gdrive_client is None:
    print("❌ Cannot start server without a valid user. Exiting...")
    exit(1)

# ----------------------
# MCP Tools
# ----------------------
@mcp.tool("create_folder", description="Create a folder in Google Drive")
def create_folder(name: str, parent_id: str = "root"):
    return gdrive_client.create_folder(name, parent_id)

@mcp.tool("list_directory", description="List files inside a folder")
def list_directory(folder_id: str = "root", max_results: int = 100):
    return gdrive_client.list_directory(folder_id, max_results)

@mcp.tool("navigate_path", description="Navigate to a folder by path")
def navigate_path(path: str):
    return gdrive_client.navigate_path(path)

@mcp.tool("read_file", description="Read a file by name or ID")
def read_file(file_name_or_id: str, encoding: str = "utf-8", parent_id: str = "root"):
    return gdrive_client.read_file(file_name_or_id, encoding, parent_id)

@mcp.tool("write_file", description="Write a file (supports txt, pdf, json, csv, docx, etc.)")
def write_file(name: str, content: str, file_id: str, parent_id: str = "root"):
    return gdrive_client.write_file(name, content, file_id, parent_id)

# ----------------------
# Run MCP server
# ----------------------
if __name__ == "__main__":
    print("✅ Starting Google Drive MCP Server...")
    mcp.run(transport="streamable-http")