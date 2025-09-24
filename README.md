# Google Drive MCP Tool Server

This project provides a **Model Context Protocol (MCP)** server for interacting with **Google Drive**.  
It uses [`fastmcp`]([https://github.com/modelcontextprotocol/python-sdk]) as the MCP server framework and exposes tools for common Drive operations such as:

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

# Google Drive API Setup Guide

This guide will help you set up Google Drive API credentials for the MCP server.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Note your project ID

## Step 2: Enable Google Drive API

1. In Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click "Enable"

## Step 3: Create OAuth 2.0 Credentials

### For Development/Testing:
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Choose "Desktop application" 
4. Name it "MCP Google Drive Client"
5. Download the JSON file
6. Rename it to `credentials.json` and place in `gdrive-mcp/` folder
7. Add Test Users (Important for unverified apps):
   - Go to APIs & Services → OAuth consent screen → audience → Test users → Add users
   - Enter your Gmail address (e.g., `your_email@gmail.com`)
   - Only these users can authenticate during testing

### For Production/Server:
1. Choose "Web application" instead
2. Add authorized redirect URIs:
   - `http://localhost:3007/oauth/callback` (for local testing)
   - Your production callback URL
3. Download and rename to `credentials.json`

## Step 4: Environment Configuration

Create a `.env` file in `gdrive-mcp/` folder:

```bash
# Google Drive API Configuration
GOOGLE_DRIVE_CREDENTIALS=credentials.json
GOOGLE_DRIVE_TOKEN=token.pickle

```

## Step 5: First-Time Authentication

For the first run, you'll need to authenticate:

```bash
python auth_setup.py
```

This will:
1. Open a browser for OAuth consent
2. Save refresh token for future use
3. Test the connection

## Run the server:

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

- Make sure credentials.json is not committed to GitHub.
- Add credentials.json and token.pickle to .gitignore.
- If you encounter access_denied errors, ensure your Google Cloud OAuth consent screen has your email as a Test User.
