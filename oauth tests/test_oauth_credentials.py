#!/usr/bin/env python3
"""
Test script for OAuth credentials file
Tests the uploaded client_secret file for Google Drive MCP Server
"""

import os
import json
import sys
from pathlib import Path

def test_oauth_credentials():
    """Test the OAuth credentials file"""
    
    print("🧪 Testing OAuth Credentials File")
    print("=" * 50)
    
    # Check for the specific file you uploaded
    original_file = "client_secret_43974738586-ao05v8tlij637q9kdkqcr2cg88let0fh.apps.googleusercontent.com.json"
    standard_file = "credentials.json"
    
    creds_file = None
    if os.path.exists(original_file):
        creds_file = original_file
        print(f"✅ Found original file: {original_file}")
    elif os.path.exists(standard_file):
        creds_file = standard_file
        print(f"✅ Found standard file: {standard_file}")
    else:
        print(f"❌ No credentials file found")
        print(f"Expected: {original_file} or {standard_file}")
        return False
    
    try:
        # Load and parse the credentials
        with open(creds_file, 'r') as f:
            creds = json.load(f)
        
        print("✅ JSON format is valid")
        
        # Check structure
        if 'installed' not in creds:
            print("❌ Missing 'installed' section - this should be a desktop app OAuth file")
            return False
        
        installed = creds['installed']
        
        # Check required fields
        required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri', 'project_id']
        missing_fields = []
        
        for field in required_fields:
            if field not in installed:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        print("✅ All required OAuth fields present")
        
        # Validate specific values
        if not installed['client_id'].endswith('.apps.googleusercontent.com'):
            print(f"❌ Invalid client_id format: {installed['client_id']}")
            return False
        
        print(f"✅ Valid client_id: {installed['client_id']}")
        
        if not installed['client_secret'].startswith('GOCSPX-'):
            print(f"❌ Invalid client_secret format")
            return False
        
        print("✅ Valid client_secret format")
        
        # Check project
        project_id = installed['project_id']
        print(f"✅ Project ID: {project_id}")
        
        # Summary
        print(f"\n📋 OAuth Credentials Summary:")
        print(f"   File: {creds_file}")
        print(f"   Type: Desktop Application OAuth")
        print(f"   Project: {project_id}")
        print(f"   Client ID: {installed['client_id']}")
        print(f"   Redirect URIs: {installed.get('redirect_uris', [])}")
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Rename file to 'credentials.json' if not already done")
        print(f"   2. Enable Google Drive API in project '{project_id}'")
        print(f"   3. Run the MCP server - it will open a browser for authorization")
        print(f"   4. Complete the OAuth consent flow")
        print(f"   5. Server will save tokens for future use")
        
        print(f"\n⚠️  Note: This is OAuth (not service account)")
        print(f"   - Requires one-time user authorization in browser")
        print(f"   - Uses your personal Google Drive access")
        print(f"   - Good for development, consider service account for production")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def rename_if_needed():
    """Rename the file to standard name if needed"""
    original_file = "client_secret_43974738586-ao05v8tlij637q9kdkqcr2cg88let0fh.apps.googleusercontent.com.json"
    standard_file = "credentials.json"
    
    if os.path.exists(original_file) and not os.path.exists(standard_file):
        print(f"\n🔄 Renaming {original_file} to {standard_file}")
        try:
            os.rename(original_file, standard_file)
            print("✅ File renamed successfully")
            return True
        except Exception as e:
            print(f"❌ Error renaming file: {e}")
            return False
    return True

if __name__ == "__main__":
    success = test_oauth_credentials()
    
    if success:
        rename_if_needed()
        print("\n🎉 OAuth credentials look good!")
        print("You can now run: python gdrive_mcp_tool_server.py")
    else:
        print("\n❌ Please check your credentials file.")
        sys.exit(1) 