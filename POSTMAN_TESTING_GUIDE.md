# Postman Testing Guide - MCP Google Drive Server

Complete testing flow for the Google Drive MCP Tool Server with OAuth 2.1 authorization.

## 🚀 **Quick Start**

### **Step 1: Start Your Server**
```bash
cd gdrive-mcp
python gdrive_mcp_tool_server.py
```
Server runs on `http://192.168.86.22:8000`

---

## 📋 **Postman Collection Setup**

### **Request 1: Server Health Check**
- **Method:** `GET`
- **URL:** `http://192.168.86.22:8000/health`
- **Expected Response:**
```json
{
  "status": "ok"
}
```

---

### **Request 2: MCP Authorization Server Metadata Discovery**
- **Method:** `GET` 
- **URL:** `http://192.168.86.22:8000/.well-known/oauth-authorization-server`
- **Expected Response:**
```json
{
  "issuer": "http://192.168.86.22:8000",
  "authorization_endpoint": "http://192.168.86.22:8000/authorize",
  "token_endpoint": "http://192.168.86.22:8000/token",
  "registration_endpoint": "http://192.168.86.22:8000/register",
  "scopes_supported": ["gdrive:read", "gdrive:write"],
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "client_credentials"]
}
```

---

### **Request 3: Test Unauthorized Access (Should Fail)**
- **Method:** `POST`
- **URL:** `http://192.168.86.22:8000/tool/create_folder`
- **Headers:**
```
Content-Type: application/json
```
- **Body (raw JSON):**
```json
{
  "name": "Unauthorized Test",
  "parent_id": "root"
}
```
- **Expected Response (401):**
```json
{
  "detail": "Authorization required"
}
```

---

### **Request 4: Register MCP OAuth Client**
- **Method:** `POST`
- **URL:** `http://192.168.86.22:8000/register`
- **Headers:**
```
Content-Type: application/json
```
- **Body (raw JSON):**
```json
{
  "client_name": "Postman MCP Client",
  "redirect_uris": ["http://localhost:3000/callback"],
  "scope": "gdrive:read gdrive:write"
}
```
- **Expected Response:**
```json
{
  "client_id": "client_abc123xyz",
  "client_secret": null,
  "client_name": "Postman MCP Client",
  "redirect_uris": ["http://localhost:3000/callback"]
}
```
**📝 Copy the `client_id` for next step!**

---

### **Request 5: Get MCP Access Token**
- **Method:** `POST`
- **URL:** `http://192.168.86.22:8000/token`
- **Headers:**
```
Content-Type: application/json
```
- **Body (raw JSON):**
```json
{
  "grant_type": "client_credentials",
  "client_id": "client_8bHaJvgtxi4PTxFD0kDvZQ"
}
```
- **Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```
**📝 Copy the `access_token` for tool requests!**

---

## 🔧 **Test All Google Drive Tools (Protected Endpoints)**

### **Tool 1: Create Folder**
- **Method:** `POST`
- **URL:** `http://192.168.86.22:8000/tool/create_folder`
- **Headers:**
```
Content-Type: application/json
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```
- **Body (raw JSON):**
```json
{
  "name": "My Postman Test Folder",
  "parent_id": "root"
}
```
- **Expected Response:**
```json
{
  "status": "success",
  "data": {
    "folder_id": "folder_abc123",
    "name": "My Postman Test Folder",
    "parent_id": "root",
    "created_at": "2025-06-16T...",
    "web_view_link": "https://drive.google.com/drive/folders/folder_abc123"
  },
  "message": "Folder 'My Postman Test Folder' created successfully",
  "authorized_client": "client_abc123xyz"
}
```

---

### **Tool 2: List Directory**
- **Method:** `POST`
- **URL:** `http://192.168.86.22:8000/tool/list_directory`
- **Headers:**
```
Content-Type: application/json
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```
- **Body (raw JSON):**
```json
{
  "folder_id": "root",
  "max_results": 10
}
```
- **Expected Response:**
```json
{
  "status": "success",
  "data": {
    "folder_id": "root",
    "folder_name": "My Drive",
    "contents": [
      {
        "id": "folder1",
        "name": "Documents",
        "type": "folder",
        "size": null
      },
      {
        "id": "file1", 
        "name": "example.txt",
        "type": "file",
        "size": 1024
      }
    ],
    "total_items": 6
  },
  "authorized_client": "client_abc123xyz"
}
```

---

### **Tool 3: Navigate Path**
- **Method:** `POST`
- **URL:** `http://192.168.86.22:8000/tool/navigate_path`
- **Headers:**
```
Content-Type: application/json
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```
- **Body (raw JSON):**
```json
{
  "path": "/Documents"
}
```
- **Expected Response:**
```json
{
  "status": "success",
  "data": {
    "path": "/Documents",
    "folder_id": "folder1",
    "folder_name": "Documents",
    "breadcrumb": ["Documents"],
    "contents": [
      {
        "id": "file3",
        "name": "document.docx",
        "type": "file",
        "size": 2048
      }
    ]
  },
  "message": "Successfully navigated to '/Documents'",
  "authorized_client": "client_abc123xyz"
}
```

---

### **Tool 4: Read File**
- **Method:** `POST`
- **URL:** `http://192.168.86.22:8000/tool/read_file`
- **Headers:**
```
Content-Type: application/json
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```
- **Body (raw JSON):**
```json
{
  "file_id": "file1",
  "encoding": "utf-8"
}
```
- **Expected Response:**
```json
{
  "status": "success",
  "data": {
    "file_id": "file1",
    "name": "example.txt",
    "content": "This is example file content.",
    "size": 1024,
    "encoding": "utf-8",
    "mime_type": "text/plain",
    "last_modified": "2025-06-16T..."
  },
  "message": "Successfully read file 'example.txt'",
  "authorized_client": "client_abc123xyz"
}
```

---

### **Tool 5: Write File**
- **Method:** `POST`
- **URL:** `http://192.168.86.22:8000/tool/write_file`
- **Headers:**
```
Content-Type: application/json
Authorization: Bearer YOUR_ACCESS_TOKEN_HERE
```
- **Body (raw JSON):**
```json
{
  "name": "postman-test-file.txt",
  "content": "Hello from Postman MCP test!\n\nThis file was created via the MCP Google Drive server.",
  "parent_id": "root"
}
```
- **Expected Response:**
```json
{
  "status": "success",
  "data": {
    "file_id": "file_abc123",
    "name": "postman-test-file.txt",
    "size": 98,
    "operation": "created",
    "parent_id": "root",
    "created_at": "2025-06-16T...",
    "web_view_link": "https://drive.google.com/file/d/file_abc123/view"
  },
  "message": "Successfully created file 'postman-test-file.txt'",
  "authorized_client": "client_abc123xyz"
}
```

---

## 🚀 **Postman Automation Tips**

### **Environment Variables Setup:**
Create a Postman environment called "MCP Google Drive" with:
- `baseUrl` = `http://192.168.86.22:8000`
- `clientId` = (will be set automatically)
- `accessToken` = (will be set automatically)

### **Auto-Save Client ID:**
Add to "Register Client" request **Tests** tab:
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("clientId", response.client_id);
    console.log("Client ID saved:", response.client_id);
}
```

### **Auto-Save Access Token:**
Add to "Get Token" request **Tests** tab:
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

if (pm.response.code === 200) {
    const response = pm.response.json();
    pm.environment.set("accessToken", response.access_token);
    console.log("Access token saved and expires in:", response.expires_in, "seconds");
}
```

### **Use Variables in Requests:**
Replace hardcoded values with variables:
- **URLs:** `{{baseUrl}}/tool/create_folder`
- **Request Bodies:** `"client_id": "{{clientId}}"`
- **Headers:** `Authorization: Bearer {{accessToken}}`

### **Validation Tests:**
Add to tool endpoint requests **Tests** tab:
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has success status", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.status).to.eql("success");
});

pm.test("Response includes authorized client", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property("authorized_client");
});
```

---

## ✅ **Testing Checklist**

### **OAuth 2.1 Flow:**
- [ ] Health check returns 200
- [ ] Metadata discovery returns proper endpoints
- [ ] Unauthorized requests return 401
- [ ] Client registration returns client_id
- [ ] Token request returns access_token

### **Google Drive Tools:**
- [ ] Create folder with valid token succeeds
- [ ] List directory shows created folders
- [ ] Navigate path works for existing paths
- [ ] Read file returns file content
- [ ] Write file creates new files

### **Security:**
- [ ] All requests without token return 401
- [ ] Invalid tokens return 401
- [ ] Expired tokens return 401
- [ ] All successful responses include `authorized_client`

### **Response Format:**
- [ ] All responses follow `{status, data, message}` format
- [ ] Success responses include proper data structures
- [ ] Error responses include meaningful messages

---

## 🔧 **Troubleshooting**

### **Common Issues:**

1. **"Connection refused"**
   - Server not running
   - Wrong IP/port (check it's 192.168.86.22:8000)

2. **"Authorization required"**
   - Missing `Authorization` header
   - Wrong token format (should be `Bearer <token>`)

3. **"Invalid token"**
   - Token expired (30 min lifetime)
   - Get new token with `/token` endpoint

4. **"Client not found"**
   - Use correct `client_id` from registration response

### **Quick Fixes:**

```bash
# Restart server
python gdrive_mcp_tool_server.py

# Get new token
# Use the "Get MCP Access Token" request again
```

---

## 📝 **Notes**

- **Token Lifetime:** 30 minutes (1800 seconds)
- **Mock Mode:** Server works without Google Drive credentials
- **Real Mode:** Add `credentials.json` for actual Google Drive operations
- **All endpoints** require proper Authorization header except health check and metadata

---

## 🎯 **Success Criteria**

Your MCP Google Drive server is working correctly if:
- ✅ OAuth 2.1 flow completes successfully
- ✅ All 5 tool endpoints respond with success
- ✅ Unauthorized requests are properly rejected
- ✅ Responses include `authorized_client` field
- ✅ Token validation works correctly

**Happy Testing!** 🚀 