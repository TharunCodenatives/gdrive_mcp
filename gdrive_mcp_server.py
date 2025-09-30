from mcp.server.fastmcp import FastMCP, Context
from google_drive_integration import GoogleDriveAPIClient

# Init MCP server
mcp = FastMCP("gdrive")

# Google Drive client
gdrive_tool = GoogleDriveAPIClient()
gdrive_tool.authenticate()

# ---------------- TOOLS ---------------- #

@mcp.tool("create_folder", description="Create a folder in Google Drive")
def create_folder(name: str, parent_id: str = "root"):
    return gdrive_tool.create_folder(name, parent_id)

@mcp.tool("list_directory", description="List files inside a folder")
def list_directory(folder_id: str = "root", max_results: int = 100):
    return gdrive_tool.list_directory(folder_id, max_results)

@mcp.tool("navigate_path", description="Navigate to a folder by path")
def navigate_path(path: str):
    return gdrive_tool.navigate_path(path)

@mcp.tool("read_file", description="Read a file by name or ID")
def read_file(file_name_or_id: str, encoding: str = "utf-8", parent_id: str = "root"):
    return gdrive_tool.read_file(file_name_or_id, encoding, parent_id)

@mcp.tool("write_file", description="Write a file (supports txt, pdf, json, csv, docx, etc.)")
def write_file(name: str, content: str, file_id: str, parent_id: str = "root"):
    return gdrive_tool.write_file(name, content, file_id, parent_id)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
