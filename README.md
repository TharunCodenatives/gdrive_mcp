# Google Drive MCP Tool Server

A FastAPI server that exposes MCP-compatible tools for Google Drive operations with OAuth 2.1 authorization. Currently implements mock responses that can be easily replaced with actual Google Drive API calls.

## Features

- **MCP-Compatible**: Designed to work with Model Context Protocol
- **OAuth 2.1 Authorization**: Full OAuth 2.1 implementation with PKCE support
- **5 Core Operations**: Create folders, list directories, navigate paths, read files, and write files
- **Mock Implementation**: All operations return realistic mock data for testing
- **Authorization Server Metadata**: RFC8414 compliant metadata discovery
- **Dynamic Client Registration**: RFC7591 compliant client registration
- **Input Validation**: Uses Pydantic models for request validation
- **Modular Design**: Easy to replace mock logic with actual Google Drive API calls
- **FastAPI Documentation**: Automatic API documentation at `/docs`

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
cd gdrive-mcp-main
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

4. Run the server:
```bash
python gdrive_mcp_tool_server.py
```

The server will start on `http://localhost:3007`

## API Endpoints

### OAuth 2.1 Authorization Endpoints
- `GET /.well-known/oauth-authorization-server` - Authorization server metadata (RFC8414)
- `POST /register` - Dynamic client registration (RFC7591)
- `GET /authorize` - Authorization endpoint with PKCE support
- `POST /token` - Token endpoint for authorization code and client credentials grants

### Health Check
- `GET /health` - Returns server health status

### Tool Endpoints (Protected - Requires Authorization)
All tool endpoints require OAuth 2.1 Bearer token authorization:

- `POST /tool/create_folder` - Create a new folder
- `POST /tool/list_directory` - List folder contents
- `POST /tool/navigate_path` - Navigate to a specific path
- `POST /tool/read_file` - Read file content
- `POST /tool/write_file` - Write/create file content

### Documentation
- `GET /` - API information and available endpoints
- `GET /docs` - Interactive Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Example Usage

### OAuth 2.1 Authorization Flow

#### 1. Dynamic Client Registration
```bash
curl -X POST "http://localhost:3007/register" \
     -H "Content-Type: application/json" \
     -d '{
       "client_name": "My MCP Client",
       "redirect_uris": ["http://localhost:3000/callback"],
       "scope": "gdrive:read gdrive:write"
     }'
```

#### 2. Authorization Request (PKCE)
```bash
# First, generate PKCE code verifier and challenge
code_verifier=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-43)
code_challenge=$(echo -n $code_verifier | sha256sum | xxd -r -p | base64 | tr -d "=+/" | cut -c1-43)

# Authorization URL (user visits this in browser)
http://localhost:3007/authorize?client_id=client_abc123&response_type=code&redirect_uri=http://localhost:3000/callback&code_challenge=$code_challenge&code_challenge_method=S256&scope=gdrive:read%20gdrive:write
```

#### 3. Token Exchange
```bash
curl -X POST "http://localhost:3007/token" \
     -H "Content-Type: application/json" \
     -d '{
       "grant_type": "authorization_code",
       "code": "auth_code_from_redirect",
       "redirect_uri": "http://localhost:3000/callback",
       "client_id": "client_abc123",
       "code_verifier": "'$code_verifier'"
     }'
```

### Tool Usage (With Authorization)

All tool endpoints require a Bearer token in the Authorization header:

#### Create Folder
```bash
curl -X POST "http://localhost:3007/tool/create_folder" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your_access_token_here" \
     -d '{"name": "My New Folder", "parent_id": "root"}'
```

#### List Directory
```bash
curl -X POST "http://localhost:3007/tool/list_directory" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your_access_token_here" \
     -d '{"folder_id": "root", "max_results": 50}'
```

#### Navigate Path
```bash
curl -X POST "http://localhost:3007/tool/navigate_path" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your_access_token_here" \
     -d '{"path": "/Documents"}'
```

#### Read File
```bash
curl -X POST "http://localhost:3007/tool/read_file" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your_access_token_here" \
     -d '{"file_id": "file1", "encoding": "utf-8"}'
```

#### Write File
```bash
curl -X POST "http://localhost:3007/tool/write_file" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer your_access_token_here" \
     -d '{"name": "test.txt", "content": "Hello World!", "parent_id": "root"}'
```

## Request/Response Format

All tool endpoints return JSON responses with the following structure:

```json
{
  "status": "success|error",
  "data": {
    // Operation-specific data
  },
  "message": "Human-readable status message"
}
```

## Mock Data

The server includes mock Google Drive data for testing:
- Root folder with sample files and folders
- Realistic file metadata (names, sizes, types)
- Hierarchical folder structure
- Sample file content

## Integration with Actual Google Drive API

To replace mock implementations with actual Google Drive API calls:

1. Install Google Drive API dependencies:
```bash
pip install google-api-python-client google-auth-oauthlib
```

2. Set up Google Drive API credentials
3. Replace methods in the `GoogleDriveTool` class with actual API calls
4. Update authentication and error handling

The current mock implementation provides the exact interface structure needed for seamless integration.

## Development

### Running in Development Mode
```bash
uvicorn gdrive_mcp_tool_server:app --reload --host 0.0.0.0 --port 3007
```

### Testing
Visit `http://localhost:3007/docs` for interactive API testing with Swagger UI.

## Architecture

- **GoogleDriveTool**: Core business logic class with methods for each operation
- **Pydantic Models**: Input validation for all endpoints
- **FastAPI Endpoints**: HTTP interface with proper error handling
- **Mock Storage**: In-memory data structure simulating Google Drive hierarchy 
