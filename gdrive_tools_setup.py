from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import uuid
import os
from datetime import datetime
from google_drive_integration import GoogleDriveAPIClient


# ---------------------------
# Pydantic Request/Response Models
# ---------------------------

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


class ToolResponse(BaseModel):
    status: str
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


# ---------------------------
# Google Drive Tool
# ---------------------------

class GoogleDriveTool:
    """
    Google Drive operations tool class.
    Uses real Google Drive API for all operations, falls back to mock if unavailable.
    """

    def __init__(self, use_real_api: bool = True):
        self.use_real_api = use_real_api
        self.api_authenticated = False

        # Mock fallback data
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
            try:
                self.gdrive_client = GoogleDriveAPIClient(
                    credentials_file=os.getenv("GOOGLE_DRIVE_CREDENTIALS", "credentials.json"),
                    token_file=os.getenv("GOOGLE_DRIVE_TOKEN", "token.pickle")
                )
                self.api_authenticated = self.gdrive_client.authenticate()
                if self.api_authenticated:
                    print("✅ Google Drive API authenticated successfully")
                else:
                    print("⚠️ Google Drive API authentication failed - using mock mode")
            except Exception as e:
                print(f"⚠️ Google Drive API setup failed: {e} - using mock mode")
                self.api_authenticated = False

    def create_folder(self, name: str, parent_id: str = "root") -> Dict[str, Any]:
        if self.use_real_api and self.api_authenticated:
            return self.gdrive_client.create_folder(name, parent_id)
        else:
            folder_id = f"folder_{uuid.uuid4().hex[:8]}"
            folder_info = {
                "id": folder_id,
                "name": name,
                "type": "folder",
                "parent": parent_id,
                "created_at": datetime.now().isoformat(),
                "children": []
            }
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
        if self.use_real_api and self.api_authenticated:
            return self.gdrive_client.list_directory(folder_id, max_results)
        else:
            if folder_id not in self.mock_files:
                return {"status": "error", "message": f"Folder with ID '{folder_id}' not found"}
            folder = self.mock_files[folder_id]
            if folder["type"] != "folder":
                return {"status": "error", "message": f"ID '{folder_id}' is not a folder"}
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
                }
            }

    def navigate_path(self, path: str) -> Dict[str, Any]:
        if self.use_real_api and self.api_authenticated:
            return self.gdrive_client.navigate_path(path)
        else:
            if path == "/" or path == "":
                target_id, target_name = "root", "My Drive"
            elif path == "/Documents":
                target_id, target_name = "folder1", "Documents"
            else:
                return {"status": "error", "message": f"Path '{path}' not found (mock mode)"}
            folder_contents = self.list_directory(target_id)
            return {
                "status": "success",
                "data": {
                    "path": path,
                    "folder_id": target_id,
                    "folder_name": target_name,
                    "contents": folder_contents["data"]["contents"] if folder_contents["status"] == "success" else [],
                    "note": "Mock response - Google Drive API not authenticated"
                }
            }

    def read_file(self, file_id: str, encoding: str = "utf-8") -> Dict[str, Any]:
        if self.use_real_api and self.api_authenticated:
            return self.gdrive_client.read_file(file_id, encoding)
        else:
            if file_id not in self.mock_files:
                return {"status": "error", "message": f"File with ID '{file_id}' not found"}
            file_info = self.mock_files[file_id]
            if file_info["type"] != "file":
                return {"status": "error", "message": f"ID '{file_id}' is not a file"}
            return {
                "status": "success",
                "data": {
                    "file_id": file_id,
                    "name": file_info["name"],
                    "content": file_info.get("content", ""),
                    "size": file_info.get("size", 0),
                    "encoding": encoding,
                    "mime_type": "text/plain",
                    "last_modified": datetime.now().isoformat(),
                    "note": "Mock response - Google Drive API not authenticated"
                }
            }

    def write_file(self, name: str, content: str, file_id: Optional[str] = None, parent_id: str = "root") -> Dict[str, Any]:
        if self.use_real_api and self.api_authenticated:
            return self.gdrive_client.write_file(name, content, file_id, parent_id)
        else:
            if file_id and file_id in self.mock_files:
                file_info = self.mock_files[file_id]
                file_info["content"] = content
                file_info["size"] = len(content.encode("utf-8"))
                return {
                    "status": "success",
                    "data": {
                        "file_id": file_id,
                        "name": file_info["name"],
                        "size": file_info["size"],
                        "operation": "updated",
                        "last_modified": datetime.now().isoformat(),
                        "note": "Mock response - Google Drive API not authenticated"
                    }
                }
            else:
                new_file_id = f"file_{uuid.uuid4().hex[:8]}"
                file_info = {
                    "id": new_file_id,
                    "name": name,
                    "type": "file",
                    "parent": parent_id,
                    "content": content,
                    "size": len(content.encode("utf-8")),
                    "created_at": datetime.now().isoformat()
                }
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
                    }
                }
