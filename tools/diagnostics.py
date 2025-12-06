import subprocess
import json
import os
from pydantic import BaseModel, Field, ConfigDict
from server_instance import mcp
from utils import handle_error, ResponseFormat

# --- MODELS ---
class SystemInfoInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class DiskInfoInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    path: str = Field(default="C:", description="Drive or directory path to analyze (e.g., 'C:\\' or 'D:\\Projects')")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

# --- TOOLS ---
@mcp.tool(name="windows_system_info", description="Get detailed Windows system information: OS version, architecture, boot time, and hardware specs.")
async def system_info(params: SystemInfoInput) -> str:
    """Get comprehensive Windows system information using systeminfo command."""
    try:
        result = subprocess.run(
            ["systeminfo"], 
            capture_output=True, text=True, timeout=10, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"```\n{result.stdout}\n```"
        return json.dumps({"system_info": result.stdout.split("\n")})
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_disk_info", description="Get detailed information about a specific disk or directory: size, free space, file system, and usage statistics.")
async def disk_info(params: DiskInfoInput) -> str:
    """Get disk or directory information using PowerShell commands."""
    try:
        ps_script = f"""
        $path = '{params.path}'
        if ($path -match '^[A-Za-z]:\\$') {{
            Get-Volume -DriveLetter $path[0] | Select-Object DriveLetter, FileSystemLabel, FileSystem, SizeRemaining, Size | ConvertTo-Json
        }} else {{
            Get-Item $path | Select-Object FullName, @{{Name='Size';Expression={{(Get-ChildItem $path -Recurse | Measure-Object -Property Length -Sum).Sum}}}}, LastWriteTime | ConvertTo-Json
        }}
        """
        result = subprocess.run(
            ["powershell", "-Command", ps_script], 
            capture_output=True, text=True, timeout=10, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        data = json.loads(result.stdout.strip())
        if params.response_format == ResponseFormat.MARKDOWN:
            if "DriveLetter" in data:
                return f"# Disk Info: {data['FileSystemLabel'] or data['DriveLetter']}\
" + 
                       f"- **File System**: {data['FileSystem']}\
" + 
                       f"- **Total Size**: {int(data['Size'])//1024//1024//1024} GB\\n" + 
                       f"- **Free Space**: {int(data['SizeRemaining'])//1024//1024//1024} GB"
            else:
                return f"# Directory Info: {data['FullName']}\
" + 
                       f"- **Size**: {int(data['Size'])//1024//1024} MB\\n" + 
                       f"- **Last Modified**: {data['LastWriteTime']}"
        return result.stdout
    except Exception as e:
        return handle_error(e)