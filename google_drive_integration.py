#!/usr/bin/env python3
"""
Google Drive API Integration for MCP Server
Real implementation replacing mock responses
"""

import os
import json
import pickle
from typing import Dict, Any, List, Optional
from datetime import datetime
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleDriveAPIClient:
    """
    Real Google Drive API client for MCP server
    Handles authentication and all Drive operations
    """
    
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.pickle"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
    def authenticate(self, user_id: str = "default") -> bool:
        """
        Authenticate with Google Drive API
        Returns True if successful, False otherwise
        """
        try:
            creds = None
            token_file = f"{user_id}_{self.token_file}"
            
            # Load existing token
            if os.path.exists(token_file):
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # If no valid credentials, authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Credentials file {self.credentials_file} not found")
                        return False
                    
                    flow = Flow.from_client_secrets_file(
                        self.credentials_file, 
                        self.scopes
                    )
                    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                    
                    # For server environments, you might want to implement a different flow
                    auth_url, _ = flow.authorization_url(prompt='consent')
                    logger.info(f"Visit this URL to authorize: {auth_url}")
                    
                    # In production, you'd handle this differently
                    # For now, we'll use a service account or pre-authorized token
                    return False
                
                # Save credentials
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Successfully authenticated with Google Drive API")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def create_folder(self, name: str, parent_id: str = None) -> Dict[str, Any]:
        """
        Create a new folder in Google Drive
        """
        try:
            if not self.service:
                return {"status": "error", "message": "Not authenticated"}
            
            folder_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id and parent_id != "root":
                folder_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id,name,parents,createdTime,webViewLink'
            ).execute()
            
            return {
                "status": "success",
                "data": {
                    "folder_id": folder.get('id'),
                    "name": folder.get('name'),
                    "parent_id": parent_id or "root",
                    "created_at": folder.get('createdTime'),
                    "web_view_link": folder.get('webViewLink')
                },
                "message": f"Folder '{name}' created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating folder: {e}")
            return {
                "status": "error",
                "message": f"Failed to create folder: {str(e)}"
            }
    
    def list_directory(self, folder_id: str = None, max_results: int = 100) -> Dict[str, Any]:
        """
        List contents of a Google Drive folder
        """
        try:
            if not self.service:
                return {"status": "error", "message": "Not authenticated"}
            
            # Build query
            if folder_id and folder_id != "root":
                query = f"'{folder_id}' in parents and trashed=false"
            else:
                query = "'root' in parents and trashed=false"
            
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields="nextPageToken, files(id,name,mimeType,size,modifiedTime,webViewLink,parents)"
            ).execute()
            
            items = results.get('files', [])
            
            contents = []
            for item in items:
                file_type = "folder" if item['mimeType'] == 'application/vnd.google-apps.folder' else "file"
                contents.append({
                    "id": item['id'],
                    "name": item['name'],
                    "type": file_type,
                    "size": item.get('size'),
                    "modified_at": item.get('modifiedTime'),
                    "web_view_link": item.get('webViewLink')
                })
            
            # Get folder name
            folder_name = "My Drive"
            if folder_id and folder_id != "root":
                try:
                    folder_info = self.service.files().get(
                        fileId=folder_id,
                        fields='name'
                    ).execute()
                    folder_name = folder_info.get('name', 'Unknown Folder')
                except:
                    folder_name = "Unknown Folder"
            
            return {
                "status": "success",
                "data": {
                    "folder_id": folder_id or "root",
                    "folder_name": folder_name,
                    "contents": contents,
                    "total_items": len(contents)
                },
                "message": f"Listed {len(contents)} items from folder '{folder_name}'"
            }
            
        except Exception as e:
            logger.error(f"Error listing directory: {e}")
            return {
                "status": "error",
                "message": f"Failed to list directory: {str(e)}"
            }
    
    def navigate_path(self, path: str) -> Dict[str, Any]:
        """
        Navigate to a specific path in Google Drive
        """
        try:
            if not self.service:
                return {"status": "error", "message": "Not authenticated"}
            
            if path == "/" or path == "":
                return self.list_directory("root")
            
            # Split path and navigate
            path_parts = [p for p in path.split('/') if p]
            current_folder_id = "root"
            breadcrumb = []
            
            for part in path_parts:
                # Search for folder with this name in current directory
                query = f"'{current_folder_id}' in parents and name='{part}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
                
                results = self.service.files().list(
                    q=query,
                    fields="files(id,name)"
                ).execute()
                
                items = results.get('files', [])
                if not items:
                    return {
                        "status": "error",
                        "message": f"Path '{path}' not found - folder '{part}' doesn't exist"
                    }
                
                current_folder_id = items[0]['id']
                breadcrumb.append(part)
            
            # Get contents of final folder
            folder_contents = self.list_directory(current_folder_id)
            
            if folder_contents["status"] == "success":
                folder_contents["data"]["path"] = path
                folder_contents["data"]["breadcrumb"] = breadcrumb
                folder_contents["message"] = f"Successfully navigated to '{path}'"
            
            return folder_contents
            
        except Exception as e:
            logger.error(f"Error navigating path: {e}")
            return {
                "status": "error",
                "message": f"Failed to navigate to path: {str(e)}"
            }
    
    def read_file(self, file_id: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Read content from a Google Drive file
        """
        try:
            if not self.service:
                return {"status": "error", "message": "Not authenticated"}
            
            # Get file metadata
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='name,mimeType,size,modifiedTime'
            ).execute()
            
            # Download file content
            request = self.service.files().get_media(fileId=file_id)
            file_io = io.BytesIO()
            downloader = MediaIoBaseDownload(file_io, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Decode content
            file_content = file_io.getvalue().decode(encoding)
            
            return {
                "status": "success",
                "data": {
                    "file_id": file_id,
                    "name": file_metadata.get('name'),
                    "content": file_content,
                    "size": int(file_metadata.get('size', 0)),
                    "encoding": encoding,
                    "mime_type": file_metadata.get('mimeType'),
                    "last_modified": file_metadata.get('modifiedTime')
                },
                "message": f"Successfully read file '{file_metadata.get('name')}'"
            }
            
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return {
                "status": "error",
                "message": f"Failed to read file: {str(e)}"
            }
    
    def write_file(self, name: str, content: str, file_id: Optional[str] = None, 
                   parent_id: str = None) -> Dict[str, Any]:
        """
        Write content to a Google Drive file (create new or update existing)
        """
        try:
            if not self.service:
                return {"status": "error", "message": "Not authenticated"}
            
            # Prepare file content
            file_content = io.BytesIO(content.encode('utf-8'))
            media = MediaIoBaseUpload(file_content, mimetype='text/plain')
            
            if file_id:
                # Update existing file
                file_metadata = {'name': name}
                updated_file = self.service.files().update(
                    fileId=file_id,
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,size,modifiedTime,webViewLink'
                ).execute()
                
                return {
                    "status": "success",
                    "data": {
                        "file_id": updated_file.get('id'),
                        "name": updated_file.get('name'),
                        "size": int(updated_file.get('size', 0)),
                        "operation": "updated",
                        "last_modified": updated_file.get('modifiedTime'),
                        "web_view_link": updated_file.get('webViewLink')
                    },
                    "message": f"Successfully updated file '{name}'"
                }
            else:
                # Create new file
                file_metadata = {'name': name}
                if parent_id and parent_id != "root":
                    file_metadata['parents'] = [parent_id]
                
                created_file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,size,createdTime,webViewLink,parents'
                ).execute()
                
                return {
                    "status": "success",
                    "data": {
                        "file_id": created_file.get('id'),
                        "name": created_file.get('name'),
                        "size": int(created_file.get('size', 0)),
                        "operation": "created",
                        "parent_id": parent_id or "root",
                        "created_at": created_file.get('createdTime'),
                        "web_view_link": created_file.get('webViewLink')
                    },
                    "message": f"Successfully created file '{name}'"
                }
                
        except Exception as e:
            logger.error(f"Error writing file: {e}")
            return {
                "status": "error",
                "message": f"Failed to write file: {str(e)}"
            } 