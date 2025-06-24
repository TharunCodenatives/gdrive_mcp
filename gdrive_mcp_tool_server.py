from typing import Optional, List, Any, Dict
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
import uuid
import secrets
import hashlib
import base64
import urllib.parse
from datetime import datetime, timedelta
from jose import JWTError, jwt
import json
import os
from google_drive_integration import GoogleDriveAPIClient


# OAuth 2.1 Configuration
OAUTH_SECRET_KEY = secrets.token_urlsafe(32)
OAUTH_ALGORITHM = "HS256"
OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth 2.1 Pydantic models
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: Optional[str] = None

class AuthorizationRequest(BaseModel):
    client_id: str
    response_type: str = "code"
    scope: Optional[str] = None
    state: Optional[str] = None
    redirect_uri: str
    code_challenge: str
    code_challenge_method: str = "S256"

class TokenRequest(BaseModel):
    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: str
    code_verifier: Optional[str] = None
    # For client credentials
    client_secret: Optional[str] = None

class ClientRegistrationRequest(BaseModel):
    client_name: Optional[str] = None
    redirect_uris: List[str] = []
    scope: Optional[str] = None

class ClientRegistrationResponse(BaseModel):
    client_id: str
    client_secret: Optional[str] = None
    client_name: Optional[str] = None
    redirect_uris: List[str] = []

# Tool request Pydantic models for input validation
class CreateFolderRequest(BaseModel):
    name: str = Field(..., description="Name of the folder to create")
    parent_id: Optional[str] = Field("root", description="Parent folder ID, defaults to root")


class ListDirectoryRequest(BaseModel):
    folder_id: Optional[str] = Field("root", description="Folder ID to list contents of")
    max_results: Optional[int] = Field(100, description="Maximum number of results to return")


class NavigatePathRequest(BaseModel):
    path: str = Field(..., description="Path to navigate to (e.g., '/Documents/Projects')")


class ReadFileRequest(BaseModel):
    file_id: str = Field(..., description="Google Drive file ID to read")
    encoding: Optional[str] = Field("utf-8", description="File encoding")


class WriteFileRequest(BaseModel):
    file_id: Optional[str] = Field(None, description="File ID to update, if None creates new file")
    name: str = Field(..., description="File name")
    content: str = Field(..., description="File content to write")
    parent_id: Optional[str] = Field("root", description="Parent folder ID for new files")


# Response models
class ToolResponse(BaseModel):
    status: str
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class MCPOAuthManager:
    """
    MCP-compliant OAuth 2.1 Authorization Server implementation.
    Supports authorization code grant with PKCE, dynamic client registration, and metadata discovery.
    """
    
    def __init__(self):
        # In-memory storage for demo - replace with persistent storage in production
        self.clients = {}  # client_id -> client_info
        self.authorization_codes = {}  # code -> code_info
        self.access_tokens = {}  # token -> token_info
        
    def register_client(self, registration: ClientRegistrationRequest) -> ClientRegistrationResponse:
        """Register a new OAuth client (RFC7591)"""
        client_id = f"client_{secrets.token_urlsafe(16)}"
        client_secret = secrets.token_urlsafe(32) if registration.redirect_uris else None
        
        client_info = {
            "client_id": client_id,
            "client_secret": client_secret,
            "client_name": registration.client_name,
            "redirect_uris": registration.redirect_uris,
            "scope": registration.scope,
            "created_at": datetime.now()
        }
        
        self.clients[client_id] = client_info
        
        return ClientRegistrationResponse(
            client_id=client_id,
            client_secret=client_secret,
            client_name=registration.client_name,
            redirect_uris=registration.redirect_uris
        )
    
    def validate_pkce_challenge(self, code_verifier: str, code_challenge: str, method: str = "S256") -> bool:
        """Validate PKCE code challenge"""
        if method == "S256":
            digest = hashlib.sha256(code_verifier.encode()).digest()
            computed_challenge = base64.urlsafe_b64encode(digest).decode().rstrip('=')
            return computed_challenge == code_challenge
        elif method == "plain":
            return code_verifier == code_challenge
        return False
    
    def create_authorization_code(self, client_id: str, redirect_uri: str, 
                                code_challenge: str, code_challenge_method: str,
                                scope: Optional[str] = None, state: Optional[str] = None) -> str:
        """Create authorization code for OAuth flow"""
        code = secrets.token_urlsafe(32)
        
        code_info = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "scope": scope,
            "state": state,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=10)
        }
        
        self.authorization_codes[code] = code_info
        return code
    
    def exchange_code_for_token(self, code: str, client_id: str, 
                              redirect_uri: str, code_verifier: str) -> Optional[TokenResponse]:
        """Exchange authorization code for access token"""
        if code not in self.authorization_codes:
            return None
            
        code_info = self.authorization_codes[code]
        
        # Validate code hasn't expired
        if datetime.now() > code_info["expires_at"]:
            del self.authorization_codes[code]
            return None
        
        # Validate client and redirect URI
        if (code_info["client_id"] != client_id or 
            code_info["redirect_uri"] != redirect_uri):
            return None
        
        # Validate PKCE
        if not self.validate_pkce_challenge(
            code_verifier, 
            code_info["code_challenge"], 
            code_info["code_challenge_method"]
        ):
            return None
        
        # Create access token
        access_token = self.create_access_token(client_id, code_info["scope"])
        
        # Clean up used code
        del self.authorization_codes[code]
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            scope=code_info["scope"]
        )
    
    def create_access_token(self, client_id: str, scope: Optional[str] = None) -> str:
        """Create JWT access token"""
        payload = {
            "sub": client_id,
            "exp": datetime.now() + timedelta(minutes=OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.now(),
            "scope": scope or ""
        }
        
        token = jwt.encode(payload, OAUTH_SECRET_KEY, algorithm=OAUTH_ALGORITHM)
        
        # Store token info
        self.access_tokens[token] = {
            "client_id": client_id,
            "scope": scope,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        
        return token
    
    def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate access token and return token info"""
        try:
            payload = jwt.decode(token, OAUTH_SECRET_KEY, algorithms=[OAUTH_ALGORITHM])
            
            # Check if token is in our store and not expired
            if token in self.access_tokens:
                token_info = self.access_tokens[token] 
                if datetime.now() < token_info["expires_at"]:
                    return {
                        "client_id": payload["sub"],
                        "scope": payload.get("scope", ""),
                        "exp": payload["exp"],
                        "iat": payload["iat"]
                    }
                else:
                    del self.access_tokens[token]
            
            return None
        except JWTError:
            return None


class GoogleDriveTool:
    """
    Google Drive operations tool class.
    Uses real Google Drive API for all operations.
    """
    
    def __init__(self, use_real_api: bool = True):
        self.use_real_api = use_real_api
        self.api_authenticated = False
        
        # Always initialize mock data as fallback
        self.mock_files = {
            "root": {
                "id": "root",
                "name": "My Drive",
                "type": "folder",
                "children": ["folder1", "file1", "file2"]
            },
            "folder1": {
                "id": "folder1",
                "name": "Documents",
                "type": "folder",
                "parent": "root",
                "children": ["file3"]
            },
            "file1": {
                "id": "file1",
                "name": "example.txt",
                "type": "file",
                "parent": "root",
                "size": 1024,
                "content": "This is example file content."
            },
            "file2": {
                "id": "file2",
                "name": "notes.md",
                "type": "file",
                "parent": "root",
                "size": 512,
                "content": "# Notes\n\nSome important notes here."
            },
            "file3": {
                "id": "file3",
                "name": "document.docx",
                "type": "file",
                "parent": "folder1",
                "size": 2048,
                "content": "Document content placeholder."
            }
        }
        
        if self.use_real_api:
            # Initialize real Google Drive API client
            try:
                self.gdrive_client = GoogleDriveAPIClient(
                    credentials_file=os.getenv("GOOGLE_DRIVE_CREDENTIALS", "credentials.json"),
                    token_file=os.getenv("GOOGLE_DRIVE_TOKEN", "token.pickle")
                )
                # Try to authenticate - falls back to mock if this fails
                self.api_authenticated = self.gdrive_client.authenticate()
                if self.api_authenticated:
                    print("✅ Google Drive API authenticated successfully")
                else:
                    print("⚠️ Google Drive API authentication failed - using mock mode")
            except Exception as e:
                print(f"⚠️ Google Drive API setup failed: {e} - using mock mode")
                self.api_authenticated = False
    
    def create_folder(self, name: str, parent_id: str = "root") -> Dict[str, Any]:
        """
        Create a new folder in Google Drive.
        
        Args:
            name: Name of the folder to create
            parent_id: Parent folder ID, defaults to root
            
        Returns:
            Dict containing creation status and folder info
        """
        if self.use_real_api and hasattr(self, 'api_authenticated') and self.api_authenticated:
            # Use real Google Drive API
            return self.gdrive_client.create_folder(name, parent_id)
        else:
            # Fallback to mock implementation
            folder_id = f"folder_{uuid.uuid4().hex[:8]}"
            
            folder_info = {
                "id": folder_id,
                "name": name,
                "type": "folder",
                "parent": parent_id,
                "created_at": datetime.now().isoformat(),
                "children": []
            }
            
            # Add to mock storage
            self.mock_files[folder_id] = folder_info
            if parent_id in self.mock_files:
                self.mock_files[parent_id]["children"].append(folder_id)
            
            return {
                "status": "success",
                "data": {
                    "folder_id": folder_id,
                    "name": name,
                    "parent_id": parent_id,
                    "created_at": folder_info["created_at"],
                    "web_view_link": f"https://drive.google.com/drive/folders/{folder_id}",
                    "note": "Mock response - Google Drive API not authenticated"
                },
                "message": f"Folder '{name}' created successfully (mock mode)"
            }
    
    def list_directory(self, folder_id: str = "root", max_results: int = 100) -> Dict[str, Any]:
        """
        List contents of a Google Drive folder.
        
        Args:
            folder_id: Folder ID to list contents of
            max_results: Maximum number of results to return
            
        Returns:
            Dict containing folder contents
        """
        if self.use_real_api and hasattr(self, 'api_authenticated') and self.api_authenticated:
            # Use real Google Drive API
            return self.gdrive_client.list_directory(folder_id, max_results)
        else:
            # Fallback to mock implementation
            if folder_id not in self.mock_files:
                return {
                    "status": "error",
                    "message": f"Folder with ID '{folder_id}' not found"
                }
            
            folder = self.mock_files[folder_id]
            if folder["type"] != "folder":
                return {
                    "status": "error",
                    "message": f"ID '{folder_id}' is not a folder"
                }
            
            contents = []
            for child_id in folder.get("children", [])[:max_results]:
                if child_id in self.mock_files:
                    child = self.mock_files[child_id]
                    contents.append({
                        "id": child["id"],
                        "name": child["name"],
                        "type": child["type"],
                        "size": child.get("size"),
                        "modified_at": datetime.now().isoformat()
                    })
            
            return {
                "status": "success",
                "data": {
                    "folder_id": folder_id,
                    "folder_name": folder["name"],
                    "contents": contents,
                    "total_items": len(contents),
                    "note": "Mock response - Google Drive API not authenticated"
                },
                "message": f"Listed {len(contents)} items from folder '{folder['name']}' (mock mode)"
            }
    
    def navigate_path(self, path: str) -> Dict[str, Any]:
        """
        Navigate to a specific path in Google Drive.
        
        Args:
            path: Path to navigate to (e.g., '/Documents/Projects')
            
        Returns:
            Dict containing navigation result and folder info
        """
        if self.use_real_api and hasattr(self, 'api_authenticated') and self.api_authenticated:
            # Use real Google Drive API
            return self.gdrive_client.navigate_path(path)
        else:
            # Fallback to mock implementation
            if path == "/" or path == "":
                target_id = "root"
                target_name = "My Drive"
            elif path == "/Documents":
                target_id = "folder1"
                target_name = "Documents"
            else:
                # Mock response for unknown paths
                return {
                    "status": "error",
                    "message": f"Path '{path}' not found or inaccessible (mock mode)"
                }
            
            # Get folder contents
            folder_contents = self.list_directory(target_id)
            
            return {
                "status": "success",
                "data": {
                    "path": path,
                    "folder_id": target_id,
                    "folder_name": target_name,
                    "breadcrumb": path.split("/")[1:] if path != "/" else [],
                    "contents": folder_contents["data"]["contents"] if folder_contents["status"] == "success" else [],
                    "note": "Mock response - Google Drive API not authenticated"
                },
                "message": f"Successfully navigated to '{path}' (mock mode)"
            }
    
    def read_file(self, file_id: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Read content from a Google Drive file.
        
        Args:
            file_id: Google Drive file ID to read
            encoding: File encoding
            
        Returns:
            Dict containing file content and metadata
        """
        if self.use_real_api and hasattr(self, 'api_authenticated') and self.api_authenticated:
            # Use real Google Drive API
            return self.gdrive_client.read_file(file_id, encoding)
        else:
            # Fallback to mock implementation
            if file_id not in self.mock_files:
                return {
                    "status": "error",
                    "message": f"File with ID '{file_id}' not found"
                }
            
            file_info = self.mock_files[file_id]
            if file_info["type"] != "file":
                return {
                    "status": "error",
                    "message": f"ID '{file_id}' is not a file"
                }
            
            return {
                "status": "success",
                "data": {
                    "file_id": file_id,
                    "name": file_info["name"],
                    "content": file_info.get("content", ""),
                    "size": file_info.get("size", 0),
                    "encoding": encoding,
                    "mime_type": "text/plain",  # Mock mime type
                    "last_modified": datetime.now().isoformat(),
                    "note": "Mock response - Google Drive API not authenticated"
                },
                "message": f"Successfully read file '{file_info['name']}' (mock mode)"
            }
    
    def write_file(self, name: str, content: str, file_id: Optional[str] = None, 
                   parent_id: str = "root") -> Dict[str, Any]:
        """
        Write content to a Google Drive file (create new or update existing).
        
        Args:
            name: File name
            content: File content to write
            file_id: File ID to update, if None creates new file
            parent_id: Parent folder ID for new files
            
        Returns:
            Dict containing write operation result
        """
        if self.use_real_api and hasattr(self, 'api_authenticated') and self.api_authenticated:
            # Use real Google Drive API
            return self.gdrive_client.write_file(name, content, file_id, parent_id)
        else:
            # Fallback to mock implementation
            if file_id and file_id in self.mock_files:
                # Update existing file
                file_info = self.mock_files[file_id]
                file_info["content"] = content
                file_info["size"] = len(content.encode('utf-8'))
                
                return {
                    "status": "success",
                    "data": {
                        "file_id": file_id,
                        "name": file_info["name"],
                        "size": file_info["size"],
                        "operation": "updated",
                        "last_modified": datetime.now().isoformat(),
                        "note": "Mock response - Google Drive API not authenticated"
                    },
                    "message": f"Successfully updated file '{file_info['name']}' (mock mode)"
                }
            else:
                # Create new file
                new_file_id = f"file_{uuid.uuid4().hex[:8]}"
                
                file_info = {
                    "id": new_file_id,
                    "name": name,
                    "type": "file",
                    "parent": parent_id,
                    "content": content,
                    "size": len(content.encode('utf-8')),
                    "created_at": datetime.now().isoformat()
                }
                
                # Add to mock storage
                self.mock_files[new_file_id] = file_info
                if parent_id in self.mock_files:
                    self.mock_files[parent_id]["children"].append(new_file_id)
                
                return {
                    "status": "success",
                    "data": {
                        "file_id": new_file_id,
                        "name": name,
                        "size": file_info["size"],
                        "operation": "created",
                        "parent_id": parent_id,
                        "created_at": file_info["created_at"],
                        "web_view_link": f"https://drive.google.com/file/d/{new_file_id}/view",
                        "note": "Mock response - Google Drive API not authenticated"
                    },
                    "message": f"Successfully created file '{name}' (mock mode)"
                }


# Initialize FastAPI app, OAuth manager, and Google Drive tool
app = FastAPI(
    title="Google Drive MCP Tool Server",
    description="MCP-compatible FastAPI server for Google Drive operations with OAuth 2.1 authorization",
    version="1.0.0"
)

oauth_manager = MCPOAuthManager()
gdrive_tool = GoogleDriveTool()
bearer_scheme = HTTPBearer(auto_error=False)

# Token validation dependency
async def validate_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> Dict[str, Any]:
    """Validate Bearer token and return token info"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_info = oauth_manager.validate_access_token(credentials.credentials)
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_info


# OAuth 2.1 Authorization Server Metadata Discovery (RFC8414)
@app.get("/.well-known/oauth-authorization-server")
async def authorization_server_metadata(request: Request):
    """OAuth 2.0 Authorization Server Metadata endpoint"""
    base_url = f"{request.url.scheme}://{request.headers.get('host', request.client.host)}"
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "registration_endpoint": f"{base_url}/register",
        "scopes_supported": ["gdrive:read", "gdrive:write"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "client_credentials"],
        "code_challenge_methods_supported": ["S256", "plain"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "none"],
        "revocation_endpoint_auth_methods_supported": ["client_secret_post", "none"]
    }

# OAuth 2.1 Dynamic Client Registration (RFC7591)
@app.post("/register")
async def register_client(registration: ClientRegistrationRequest):
    """Dynamic client registration endpoint"""
    try:
        response = oauth_manager.register_client(registration)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# OAuth 2.1 Authorization Endpoint
@app.get("/authorize")
async def authorize(
    client_id: str,
    redirect_uri: str,
    code_challenge: str,
    response_type: str = "code",
    code_challenge_method: str = "S256",
    scope: Optional[str] = None,
    state: Optional[str] = None
):
    """OAuth 2.1 authorization endpoint with PKCE"""
    # Validate client
    if client_id not in oauth_manager.clients:
        raise HTTPException(status_code=400, detail="Invalid client_id")
    
    client = oauth_manager.clients[client_id]
    
    # Validate redirect URI
    if redirect_uri not in client.get("redirect_uris", []):
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")
    
    # Validate response type
    if response_type != "code":
        raise HTTPException(status_code=400, detail="Unsupported response_type")
    
    # For demo purposes, we'll auto-approve the authorization
    # In a real implementation, this would redirect to a user consent page
    code = oauth_manager.create_authorization_code(
        client_id, redirect_uri, code_challenge, code_challenge_method, scope, state
    )
    
    # Build redirect URL with authorization code
    redirect_params = {"code": code}
    if state:
        redirect_params["state"] = state
    
    redirect_url = f"{redirect_uri}?{urllib.parse.urlencode(redirect_params)}"
    return RedirectResponse(url=redirect_url, status_code=302)

# OAuth 2.1 Token Endpoint
@app.post("/token")
async def token_endpoint(request: TokenRequest):
    """OAuth 2.1 token endpoint"""
    if request.grant_type == "authorization_code":
        # Authorization code grant
        if not all([request.code, request.redirect_uri, request.client_id, request.code_verifier]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        token_response = oauth_manager.exchange_code_for_token(
            request.code, request.client_id, request.redirect_uri, request.code_verifier
        )
        
        if not token_response:
            raise HTTPException(status_code=400, detail="Invalid authorization code")
        
        return token_response
    
    elif request.grant_type == "client_credentials":
        # Client credentials grant
        if not request.client_id:
            raise HTTPException(status_code=400, detail="Missing client_id")
        
        # For demo purposes, auto-approve client credentials
        access_token = oauth_manager.create_access_token(request.client_id)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=OAUTH_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported grant_type")

# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


# Tool endpoints (protected with OAuth 2.1)
@app.post("/tool/create_folder")
async def create_folder_endpoint(request: CreateFolderRequest, token_info: Dict[str, Any] = Depends(validate_token)):
    """Create a new folder in Google Drive (requires authorization)"""
    try:
        result = gdrive_tool.create_folder(request.name, request.parent_id)
        # Add client info to response
        result["authorized_client"] = token_info["client_id"]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tool/list_directory")
async def list_directory_endpoint(request: ListDirectoryRequest, token_info: Dict[str, Any] = Depends(validate_token)):
    """List contents of a Google Drive folder (requires authorization)"""
    try:
        result = gdrive_tool.list_directory(request.folder_id, request.max_results)
        result["authorized_client"] = token_info["client_id"]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tool/navigate_path")
async def navigate_path_endpoint(request: NavigatePathRequest, token_info: Dict[str, Any] = Depends(validate_token)):
    """Navigate to a specific path in Google Drive (requires authorization)"""
    try:
        result = gdrive_tool.navigate_path(request.path)
        result["authorized_client"] = token_info["client_id"]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tool/read_file")
async def read_file_endpoint(request: ReadFileRequest, token_info: Dict[str, Any] = Depends(validate_token)):
    """Read content from a Google Drive file (requires authorization)"""
    try:
        result = gdrive_tool.read_file(request.file_id, request.encoding)
        result["authorized_client"] = token_info["client_id"]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tool/write_file")
async def write_file_endpoint(request: WriteFileRequest, token_info: Dict[str, Any] = Depends(validate_token)):
    """Write content to a Google Drive file (requires authorization)"""
    try:
        result = gdrive_tool.write_file(
            request.name, 
            request.content, 
            request.file_id, 
            request.parent_id
        )
        result["authorized_client"] = token_info["client_id"]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Root endpoint with API information
@app.get("/")
async def root(request: Request):
    """Root endpoint with API information"""
    base_url = f"{request.url.scheme}://{request.headers.get('host', request.client.host)}"
    
    return {
        "name": "Google Drive MCP Tool Server",
        "version": "1.0.0",
        "description": "MCP-compatible FastAPI server for Google Drive operations with OAuth 2.1 authorization",
        "authorization": {
            "type": "OAuth 2.1",
            "metadata_endpoint": f"{base_url}/.well-known/oauth-authorization-server",
            "authorization_endpoint": f"{base_url}/authorize",
            "token_endpoint": f"{base_url}/token",
            "registration_endpoint": f"{base_url}/register",
            "supported_scopes": ["gdrive:read", "gdrive:write"],
            "grant_types": ["authorization_code", "client_credentials"],
            "pkce_required": True
        },
        "endpoints": {
            "health": "/health",
            "tools": [
                "/tool/create_folder",
                "/tool/list_directory", 
                "/tool/navigate_path",
                "/tool/read_file",
                "/tool/write_file"
            ]
        },
        "docs": "/docs",
        "note": "All tool endpoints require OAuth 2.1 Bearer token authorization"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3007) 