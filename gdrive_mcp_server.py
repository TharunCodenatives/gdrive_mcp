from mcp.server.fastmcp import FastMCP
from gdrive_tools_setup import GoogleDriveTool

mcp = FastMCP("gdrive")
gdrive_tool = GoogleDriveTool()

@mcp.tool("create_folder", description="Create a new folder in Google Drive")
def create_folder(name: str, parent_id: str = "root"):
    return gdrive_tool.create_folder(name, parent_id)

@mcp.tool("list_directory", description="List contents of a folder")
def list_directory(folder_id: str = "root", max_results: int = 100):
    return gdrive_tool.list_directory(folder_id, max_results)

@mcp.tool("navigate_path", description="Navigate to a specific path in Google Drive")
def navigate_path(path: str):
    return gdrive_tool.navigate_path(path)

@mcp.tool("write_file", description="Write content to a file")
def write_file(name: str, content: str, file_id: str, parent_id: str = "root"):
    return gdrive_tool.write_file(name, content, file_id, parent_id)

@mcp.tool("read_file", description="Read content from a file")
def read_file(file_id: str, encoding: str = "utf-8"):
    return gdrive_tool.read_file(file_id, encoding)

if __name__ == "__main__":
    mcp.run(transport="streamable-http")

