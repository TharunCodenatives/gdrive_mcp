# Google Drive MCP Tool Server

This project provides a **Model Context Protocol (MCP)** server for interacting with **Google Drive**.  
It uses [`fastmcp`](https://github.com/modelcontextprotocol/python-sdk) as the MCP server framework and exposes tools for common Drive operations such as:

- Creating folders
- Listing directory contents
- Navigating paths
- Writing files
- Reading files

## 🚀 Features

- ✅ Create folders inside Google Drive  
- ✅ List contents of any folder  
- ✅ Navigate to a path inside Google Drive  
- ✅ Read and write files
- ✅ Authenticate using service account
- ✅ Supports Workspace Shared Drives (prod) or Shared Folder workaround (dev/testing)

## Python Version Dependencies

- **Working**: Python 3.11, Python 3.12
- **Not Working**: Python 3.13
    - **Reason**: pydantic-core does not have pre-built wheels for Python 3.13.
    - Installing on 3.13 requires Rust compiler to build pydantic-core from source.
    - **Recommended**: Use Python 3.11 or 3.12 for seamless installation with pip install -r requirements.txt.

## Installation

1. Clone the repo and navigate into it:
```bash
git clone <repo_url>
cd gdrive-mcp
```

2. Create virtual environment (recommended):
```bash
python3.12 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

# Google Drive Service Account Setup

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Note your project ID

## Step 2: Enable Google Drive API

1. In Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click "Enable"

## Step 3: Create Service Account

1. Go to IAM & Admin → Service Accounts
2. Click Create Service Account
3. Enter a name, e.g., mcp-drive-sa
4. Assign Editor or Drive Admin role (depending on needs)
5. Click Done

## Step 4: Create Service Account Key

1. Click the created service account → Keys → Add Key → Create New Key
2. Choose JSON
3. Download the JSON file
4. Rename it to service_account.json and place in the gdrive-mcp/ folder

# Providing Drive Access to Service Account
Service accounts do not have their own Drive unless it’s a Workspace account. You have two options:

## Option 1: Workspace Shared Drive (Recommended for Prod)

1. Sign in to your Google Workspace account (e.g., yourname@company.com)
2. Go to [Shared Drives](https://drive.google.com/drive/u/0/shared-drives)
3. Create a new Shared Drive or select an existing one
4. Go to Manage Members → Add your service account email with Editor permissions
5. Note the Shared Drive ID and add it to your .env (you can hardcode this ID for prod):

```bash
DEFAULT_SHARED_FOLDER_ID=<shared_drive_id>
```
✅ This is production-ready and preferred because the service account can access the drive independently.

## Option 2: Shared Folder Workaround (Personal Drive, Testing Only)

1. Go to your My Drive
2. Create a new folder, e.g., `MCP_Test`
3. Right-click → Share → Add your service account email with Editor permissions
4. Note the Folder ID and add it to your `.env`:

```bash
DEFAULT_SHARED_FOLDER_ID=<shared_folder_id>
```
⚠️ This approach is not recommended for production, as it depends on a personal account and folder ID must be hardcoded per environment.

# Environment Configuration (.env)
```bash
# Google Drive Service Account JSON
GOOGLE_DRIVE_SERVICE_ACCOUNT=service_account.json

# Default folder / Shared Drive ID
DEFAULT_SHARED_FOLDER_ID=<folder_or_drive_id>
```
No OAuth token file (token.pickle) is required — service account handles authentication automatically.

# Running the MCP Server:

```bash
uv run gdrive_mcp_server.py
```
By default, the server will run using streamable-http transport at:

```bash
http://127.0.0.1:8000
```

The MCP server will start using streamable-http transport.

### Available MCP Tools

| Tool Name | Description | Parameters |
| --------- | ----------- | ---------- |
| `create_folder` | Create a new folder in Google Drive | `name: str`, `parent_id: str = "root"` |
| `list_directory` | List contents of a folder | `folder_id: str = "root"`, `max_results: int = 100` |
| `navigate_path` | Navigate to a specific path in Drive | `path: str` |
| `write_file` | Write content to a file | `name: str`, `content: str`, `file_id: str`, `parent_id: str = "root"` |
| `read_file` | Read content from a file | `file_id: str`, `encoding: str = "utf-8"` |

### Testing with Postman

1. Open Postman (latest version with MCP support).
2. Click New → MCP Request.
3. Enter the MCP server URL:

```bash
http://127.0.0.1:8000/mcp
```

4. Click Connect.
5. You will now see all available tools (create_folder, list_directory, etc.) listed in the Messages block automatically.
6. Select a tool and provide input arguments.
7. Run the request — you will get the live response from Google Drive.

✅ No need to craft raw JSON manually — Postman MCP automatically lists and formats available tools for you.

### Notes

- Do not commit service_account.json or .env to GitHub
- Workspace Shared Drive ID can be hardcoded for production
- Personal Drive shared folder is only for testing
- Ensure the shared folder or Shared Drive is shared with the service account email
