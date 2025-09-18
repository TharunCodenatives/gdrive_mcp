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
USE_REAL_GOOGLE_DRIVE_API=true

# MCP Server Configuration  
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=3007
```

## Step 5: First-Time Authentication

For the first run, you'll need to authenticate:

```bash
cd gdrive-mcp
python auth_setup.py
```

This will:
1. Open a browser for OAuth consent
2. Save refresh token for future use
3. Test the connection

## Step 6: Test the Integration

```bash
# Start server
python gdrive_mcp_tool_server.py

# Test with Postman or curl
curl -X POST "http://localhost:3007/tool/list_directory" \
     -H "Authorization: Bearer YOUR_MCP_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"folder_id": "root"}'
```

## Production Deployment Considerations

### Service Account (Recommended for Production)
1. Create a service account in Google Cloud Console
2. Download the service account key JSON
3. Set environment variable: `GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json`
4. Share Google Drive folders/files with the service account email

### Security
- Store credentials securely (use cloud secret managers)
- Use HTTPS in production
- Implement proper logging and monitoring
- Regular token rotation

### Scaling
- Consider using connection pooling
- Implement rate limiting for Google API calls
- Use caching for frequently accessed data

## Troubleshooting

### Common Issues:

1. **"credentials.json not found"**
   - Ensure file exists in correct location
   - Check file permissions

2. **"Authentication failed"**
   - Verify OAuth scopes are correct
   - Check if API is enabled
   - Clear token.pickle and re-authenticate

3. **"Quota exceeded"**
   - Check Google Cloud Console quotas
   - Implement rate limiting
   - Consider upgrading quota limits

### Environment Variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_DRIVE_CREDENTIALS` | Path to credentials JSON | `credentials.json` |
| `GOOGLE_DRIVE_TOKEN` | Path to token pickle file | `token.pickle` |
| `USE_REAL_GOOGLE_DRIVE_API` | Enable real API vs mock | `true` |

## Next Steps

Once setup is complete:
1. Test all endpoints with real Google Drive
2. Deploy to your lab environment
3. Configure monitoring and logging
4. Set up automated testing

## Support

For Google Drive API documentation:
- [Google Drive API v3 Reference](https://developers.google.com/drive/api/v3/reference)
- [Python Client Library](https://github.com/googleapis/google-api-python-client) 
