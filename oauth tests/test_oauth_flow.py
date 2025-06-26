
import requests
import base64
import hashlib
import secrets
import urllib.parse
from typing import Dict, Optional

class MCPOAuthClient:
    """Simple OAuth 2.1 client for testing MCP server"""
    
    def __init__(self, server_base_url: str = "http://localhost:3007"):
        self.server_base_url = server_base_url
        self.client_id: Optional[str] = None
        self.access_token: Optional[str] = None
        
    def generate_pkce_pair(self) -> tuple[str, str]:
        """Generate PKCE code verifier and challenge"""
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')
        return code_verifier, code_challenge
    
    def register_client(self) -> Dict:
        """Register a new OAuth client"""
        registration_data = {
            "client_name": "Test MCP Client",
            "redirect_uris": ["http://localhost:3000/callback"],
            "scope": "gdrive:read gdrive:write"
        }
        
        response = requests.post(
            f"{self.server_base_url}/register",
            json=registration_data
        )
        
        if response.status_code == 200:
            client_info = response.json()
            self.client_id = client_info["client_id"]
            print(f"✅ Client registered successfully: {self.client_id}")
            return client_info
        else:
            print(f"❌ Client registration failed: {response.text}")
            return {}
    
    def get_authorization_url(self) -> tuple[str, str]:
        """Get authorization URL for user consent"""
        if not self.client_id:
            raise ValueError("Client must be registered first")
        
        code_verifier, code_challenge = self.generate_pkce_pair()
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": "http://localhost:3000/callback",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "scope": "gdrive:read gdrive:write",
            "state": secrets.token_urlsafe(16)
        }
        
        auth_url = f"{self.server_base_url}/authorize?{urllib.parse.urlencode(params)}"
        return auth_url, code_verifier
    
    def exchange_code_for_token(self, auth_code: str, code_verifier: str) -> Dict:
        """Exchange authorization code for access token"""
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": "http://localhost:3000/callback",
            "client_id": self.client_id,
            "code_verifier": code_verifier
        }
        
        response = requests.post(
            f"{self.server_base_url}/token",
            json=token_data
        )
        
        if response.status_code == 200:
            token_info = response.json()
            self.access_token = token_info["access_token"]
            print(f"✅ Access token obtained: {self.access_token[:20]}...")
            return token_info
        else:
            print(f"❌ Token exchange failed: {response.text}")
            return {}
    
    def test_tool_endpoints(self):
        """Test all tool endpoints with the access token"""
        if not self.access_token:
            print("❌ No access token available")
            return
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Test create folder
        print("\n🔧 Testing create_folder...")
        response = requests.post(
            f"{self.server_base_url}/tool/create_folder",
            headers=headers,
            json={"name": "Test Folder", "parent_id": "root"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        
        # Test list directory
        print("\n🔧 Testing list_directory...")
        response = requests.post(
            f"{self.server_base_url}/tool/list_directory",
            headers=headers,
            json={"folder_id": "root", "max_results": 10}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        
        # Test read file
        print("\n🔧 Testing read_file...")
        response = requests.post(
            f"{self.server_base_url}/tool/read_file",
            headers=headers,
            json={"file_id": "file1"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
    
    def test_unauthorized_access(self):
        """Test that endpoints reject unauthorized requests"""
        print("\n🔒 Testing unauthorized access...")
        
        response = requests.post(
            f"{self.server_base_url}/tool/create_folder",
            json={"name": "Unauthorized Test"}
        )
        
        if response.status_code == 401:
            print("✅ Unauthorized request properly rejected with 401")
        else:
            print(f"❌ Expected 401, got {response.status_code}")


def main():
    """Main test function"""
    print("🚀 Starting MCP OAuth 2.1 Test")
    
    client = MCPOAuthClient()
    
    # Test server metadata discovery
    print("\n📋 Testing server metadata discovery...")
    try:
        response = requests.get("http://localhost:3007/.well-known/oauth-authorization-server")
        if response.status_code == 200:
            metadata = response.json()
            print("✅ Server metadata retrieved successfully")
            print(f"Supported grant types: {metadata.get('grant_types_supported', [])}")
        else:
            print(f"❌ Metadata discovery failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Please start the server first with: python gdrive_mcp_tool_server.py")
        return
    
    # Test unauthorized access first
    client.test_unauthorized_access()
    
    # Register client
    print("\n📝 Registering OAuth client...")
    client_info = client.register_client()
    if not client_info:
        return
    
    # Get authorization URL
    print("\n🔗 Generating authorization URL...")
    try:
        auth_url, code_verifier = client.get_authorization_url()
        print(f"Authorization URL: {auth_url}")
        
        # In a real scenario, user would visit this URL and authorize
        # For testing, we'll simulate the authorization by directly calling the endpoint
        print("\n🤖 Simulating user authorization (auto-approval for testing)...")
        
        # Extract parameters from auth URL for direct call
        parsed_url = urllib.parse.urlparse(auth_url)
        params = urllib.parse.parse_qs(parsed_url.query)
        
        # Make direct authorization request
        auth_response = requests.get(auth_url, allow_redirects=False)
        
        if auth_response.status_code == 302:
            # Extract authorization code from redirect
            redirect_url = auth_response.headers.get('location', '')
            redirect_params = urllib.parse.parse_qs(urllib.parse.urlparse(redirect_url).query)
            auth_code = redirect_params.get('code', [None])[0]
            
            if auth_code:
                print(f"✅ Authorization code obtained: {auth_code[:20]}...")
                
                # Exchange code for token
                print("\n🔄 Exchanging code for access token...")
                token_info = client.exchange_code_for_token(auth_code, code_verifier)
                
                if token_info:
                    # Test tool endpoints
                    client.test_tool_endpoints()
                    
                    print("\n✅ OAuth 2.1 flow completed successfully!")
                    print(f"🔑 Access token expires in: {token_info.get('expires_in')} seconds")
                else:
                    print("❌ Token exchange failed")
            else:
                print("❌ No authorization code in redirect")
        else:
            print(f"❌ Authorization failed: {auth_response.status_code}")
            
    except Exception as e:
        print(f"❌ Authorization flow failed: {e}")


if __name__ == "__main__":
    main() 