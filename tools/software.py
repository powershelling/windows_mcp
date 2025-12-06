import subprocess
import json
import os
from pydantic import BaseModel, Field, ConfigDict
from server_instance import mcp
from utils import handle_error, ResponseFormat

# --- MODELS ---
class InstalledSoftwareInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class UninstallInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(..., description="Name or partial name of the software to uninstall (e.g., 'Chrome' or 'Epic Games')")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

# --- TOOLS ---
@mcp.tool(name="windows_list_software", description="List all installed software applications. Includes name, version, and publisher.")
async def list_software(params: InstalledSoftwareInput) -> str:
    """List installed software using PowerShell and WMI."""
    try:
        ps_script = """
        Get-ItemProperty HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | 
        Select-Object DisplayName, DisplayVersion, Publisher, InstallDate | 
        Where-Object { $_.DisplayName -ne $null } | 
        ConvertTo-Json
        """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_script], 
            capture_output=True, text=True, timeout=30, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        try:
            software = json.loads(result.stdout.strip())
            if not software:
                return "No installed software found"
            
            if params.response_format == ResponseFormat.MARKDOWN:
                lines = ["# Installed Software", ""]
                for app in sorted(software, key=lambda x: x.get('DisplayName', '').lower())[:30]:  # Top 30 for readability
                    name = app.get('DisplayName', 'Unknown')
                    version = app.get('DisplayVersion', 'Unknown')
                    publisher = app.get('Publisher', 'Unknown')
                    lines.append(f"- **{name}**: v{version} by {publisher}")
                if len(software) > 30:
                    lines.append(f"\n... and {len(software)-30} more applications")
                return "\n".join(lines)
            return result.stdout
        except json.JSONDecodeError:
            return "Error: Could not parse software list"
    except subprocess.TimeoutExpired:
        return "Error: Software list timed out (30s limit)"
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_uninstall_software", description="Uninstall a software application by name. Searches for partial matches in installed software list.")
async def uninstall_software(params: UninstallInput) -> str:
    """Uninstall software using its name via PowerShell."""
    try:
        # First, find the software
        ps_script_find = f"""
        Get-ItemProperty HKLM:\\Software\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | 
        Where-Object {{ $_.DisplayName -like '*{params.name}*' }} | 
        Select-Object DisplayName, PSChildName | 
        ConvertTo-Json
        """
        
        find_result = subprocess.run(
            ["powershell", "-Command", ps_script_find], 
            capture_output=True, text=True, timeout=10, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if find_result.returncode != 0:
            return f"Error finding software: {find_result.stderr}"
        
        try:
            matches = json.loads(find_result.stdout.strip())
            if not matches:
                return f"No software found matching '{params.name}'"
            
            if len(matches) > 1:
                names = ", ".join([m['DisplayName'] for m in matches])
                return f"Multiple matches found: {names}. Please specify more precisely."
            
            # Uninstall the first match
            app_name = matches[0]['DisplayName']
            app_guid = matches[0]['PSChildName']
            
            ps_script_uninstall = f"""
            Start-Process -Wait -FilePath "msiexec" -ArgumentList '/x {app_guid} /qn'
            if ($LASTEXITCODE -eq 0) {{
                Write-Output "Uninstalled {app_name} successfully"
            }} else {{
                Write-Output "Failed to uninstall {app_name}"
            }}
            """
            
            uninstall_result = subprocess.run(
                ["powershell", "-Command", ps_script_uninstall], 
                capture_output=True, text=True, timeout=60, 
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if params.response_format == ResponseFormat.MARKDOWN:
                if "successfully" in uninstall_result.stdout.lower():
                    return f"✅ Uninstalled **{app_name}** successfully"
                return f"❌ Failed to uninstall {app_name}: {uninstall_result.stdout}"
            return json.dumps({"status": "success" if "successfully" in uninstall_result.stdout.lower() else "failed", "software": app_name})
        except json.JSONDecodeError:
            return "Error: Could not parse software information"
    except subprocess.TimeoutExpired:
        return "Error: Uninstall process timed out (60s limit)"
    except Exception as e:
        return handle_error(e)