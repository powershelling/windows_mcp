import subprocess
import json
from pydantic import BaseModel, Field, ConfigDict
from server_instance import mcp
from utils import handle_error, ResponseFormat

# --- MODELS ---
class RunCommandInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    command: str = Field(..., description="Command to execute (e.g., 'dir C:\\' or 'ipconfig /all')")
    shell: str = Field(default="cmd", description="Shell to use: 'cmd' (default) or 'powershell'")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class ShortcutInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(..., description="Name for the shortcut (e.g., 'MyApp')")
    target: str = Field(..., description="Target path (e.g., 'C:\\Program Files\\App\\app.exe')")
    desktop: bool = Field(default=True, description="Create on desktop (True) or in user's start menu (False)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

# --- TOOLS ---
@mcp.tool(name="windows_run_command", description="Execute a Windows command or PowerShell script and return the output. Useful for advanced system operations.")
async def run_command(params: RunCommandInput) -> str:
    """Execute a command in cmd or PowerShell and return the output."""
    try:
        shell = params.shell.lower()
        if shell == "powershell":
            cmd = ["powershell", "-Command", params.command]
        else:  # Default to cmd
            cmd = ["cmd", "/c", params.command]
        
        result = subprocess.run(
            cmd, 
            capture_output=True, text=True, timeout=30, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            return f"Error (code {result.returncode}): {result.stderr}"
        
        output = result.stdout.strip()
        if not output:
            return "Command executed successfully (no output)"
        
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"```\n{output}\n```"
        return json.dumps({"output": output})
    except subprocess.TimeoutExpired:
        return "Error: Command timed out (30s limit)"
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_create_shortcut", description="Create a desktop or start menu shortcut for an application or file.")
async def create_shortcut(params: ShortcutInput) -> str:
    """Create a Windows shortcut (.lnk file) using PowerShell."""
    try:
        # PowerShell script to create shortcut
        ps_script = f"""
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("
        if {params.desktop}:
            ps_script += "$env:USERPROFILE\\Desktop\\{params.name}.lnk"
        else:
            ps_script += "$env:APPDATA\\Microsoft\\Windows\\Start Menu\\Programs\\{params.name}.lnk"
        ps_script += f""
        )
        $Shortcut.TargetPath = '{params.target}'
        $Shortcut.Save()
        """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_script], 
            capture_output=True, text=True, timeout=10, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            return f"Error creating shortcut: {result.stderr}"
        
        location = "desktop" if params.desktop else "start menu"
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"✅ Shortcut **{params.name}** created on {location} pointing to **{params.target}**"
        return json.dumps({"status": "success", "name": params.name, "target": params.target, "location": location})
    except Exception as e:
        return handle_error(e)