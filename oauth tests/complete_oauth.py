 #!/usr/bin/env python3
"""
OAuth Authorization Helper
Completes the OAuth flow for Google Drive MCP Server
"""

import os
import json
import pickle
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

def complete_oauth_flow():
    """Complete the OAuth authorization flow"""
    
    print("🔐 Google Drive OAuth Authorization Helper")
    print("=" * 50)
    
    # Check for credentials file
    credentials_file = "credentials.json"
    if not os.path.exists(credentials_file):
        print(f"❌ {credentials_file} not found!")
        print("Make sure you have renamed your client_secret file to credentials.json")
        return False
    
    print(f"✅ Found {credentials_file}")
    
    # Set up OAuth flow
    try:
        flow = Flow.from_client_secrets_file(
            credentials_file,
            scopes=[
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file'
            ]
        )
        flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
        
        # Get authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        print("\n🌐 Step 1: Visit this URL in your browser:")
        print("-" * 50)
        print(auth_url)
        print("-" * 50)
        
        print("\n📋 Step 2: Complete authorization and copy the code")
        print("1. Sign in to your Google account")
        print("2. Grant permissions for Google Drive access")  
        print("3. Copy the authorization code shown")
        
        # Get authorization code from user
        print("\n💾 Step 3: Enter the authorization code:")
        auth_code = input("Authorization code: ").strip()
        
        if not auth_code:
            print("❌ No authorization code provided")
            return False
        
        print(f"✅ Received authorization code: {auth_code[:10]}...")
        
        # Exchange code for token
        print("\n🔄 Exchanging code for access token...")
        flow.fetch_token(code=auth_code)
        
        # Save credentials
        creds = flow.credentials
        token_file = "token.pickle"
        
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
        
        print(f"✅ Saved credentials to {token_file}")
        
        # Test the credentials
        print("\n🧪 Testing Google Drive API access...")
        from googleapiclient.discovery import build
        
        service = build('drive', 'v3', credentials=creds)
        
        # Try to list some files
        results = service.files().list(pageSize=5, fields="files(id,name)").execute()
        files = results.get('files', [])
        
        print(f"✅ Successfully connected to Google Drive!")
        print(f"📁 Found {len(files)} files in your Drive:")
        for file in files:
            print(f"   - {file['name']} (ID: {file['id']})")
        
        print("\n🎉 OAuth authorization complete!")
        print("You can now restart your MCP server:")
        print("python gdrive_mcp_tool_server.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during OAuth flow: {e}")
        return False

def check_existing_auth():
    """Check if we already have valid authorization"""
    print("\n🔍 Checking for existing authorization...")
    
    token_file = "token.pickle"
    if not os.path.exists(token_file):
        print("⚪ No existing token found")
        return False
    
    try:
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)
        
        # Check if credentials are valid
        if creds and creds.valid:
            print("✅ Valid credentials found!")
            
            # Test API access
            from googleapiclient.discovery import build
            service = build('drive', 'v3', credentials=creds)
            results = service.files().list(pageSize=1).execute()
            
            print("✅ Google Drive API access confirmed")
            print("Your MCP server should work now!")
            return True
            
        elif creds and creds.expired and creds.refresh_token:
            print("🔄 Credentials expired, refreshing...")
            creds.refresh(Request())
            
            # Save refreshed credentials
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
            
            print("✅ Credentials refreshed successfully!")
            return True
        else:
            print("❌ Invalid credentials found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking credentials: {e}")
        return False

if __name__ == "__main__":
    # First check if we already have valid auth
    if check_existing_auth():
        print("\n🎉 You're already authorized! Your MCP server should work.")
    else:
        print("\n🔐 Need to complete OAuth authorization...")
        if complete_oauth_flow():
            print("\n✅ Authorization complete!")
        else:
            print("\n❌ Authorization failed. Please try again.")
    
    print("\n📖 Next steps:")
    print("1. Restart your MCP server: python gdrive_mcp_tool_server.py")
    print("2. Server should now authenticate successfully")
    print("3. Visit http://localhost:3007/docs to test the API")