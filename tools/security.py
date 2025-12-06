import subprocess
import json
from pydantic import BaseModel, Field, ConfigDict
from server_instance import mcp
from utils import handle_error, ResponseFormat

# --- MODELS ---
class UpdatesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    install: bool = Field(default=False, description="Install updates if available (default: False, check only)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class UACInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class DriversInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

# --- TOOLS ---
@mcp.tool(name="windows_check_updates", description="Check for available Windows updates. Optionally install them if requested.")
async def check_updates(params: UpdatesInput) -> str:
    """Check for Windows updates using PowerShell."""
    try:
        if params.install:
            ps_script = """
            Install-Module -Name PSWindowsUpdate -Force -Confirm:$false
            Import-Module PSWindowsUpdate
            Get-WindowsUpdate -Install -AcceptAll | Out-String
            """
        else:
            ps_script = """
            Install-Module -Name PSWindowsUpdate -Force -Confirm:$false
            Import-Module PSWindowsUpdate
            Get-WindowsUpdate | Select-Object Title, KB, Size, InstallationBehavior | ConvertTo-Json
            """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_script], 
            capture_output=True, text=True, timeout=60, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        if params.install:
            return f"Update installation results:\n```\n{result.stdout}\n```"
        
        try:
            updates = json.loads(result.stdout.strip())
            if not updates:
                return "✅ System is up to date"
            
            if params.response_format == ResponseFormat.MARKDOWN:
                lines = ["# Available Windows Updates", ""]
                for update in updates:
                    lines.append(f"- **{update['Title']}** (KB{update['KB']}, {update['Size']}MB)")
                lines.append(f"\n💡 Use `windows_check_updates(install=True)` to install these updates.")
                return "\n".join(lines)
            return result.stdout
        except json.JSONDecodeError:
            return f"Update check results:\n```\n{result.stdout}\n```"
    except subprocess.TimeoutExpired:
        return "Error: Update check timed out (60s limit)"
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_uac_status", description="Check the current User Account Control (UAC) status and settings.")
async def uac_status(params: UACInput) -> str:
    """Get UAC status using registry query."""
    try:
        ps_script = """
        $uacStatus = (Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "EnableLUA" -ErrorAction SilentlyContinue).EnableLUA
        $uacLevel = (Get-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" -Name "ConsentPromptBehaviorAdmin" -ErrorAction SilentlyContinue).ConsentPromptBehaviorAdmin
        
        [PSCustomObject]@{
            Status = if ($uacStatus -eq 1) { "Enabled" } else { "Disabled" }
            Level = switch ($uacLevel) {
                0 { "Always notify" }
                1 { "Notify when apps make changes" }
                2 { "Default - Notify when apps make changes (no dim)" }
                5 { "Always notify (highest security)" }
                default { "Unknown level: $uacLevel" }
            }
        } | ConvertTo-Json
        """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_script], 
            capture_output=True, text=True, timeout=10, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        try:
            data = json.loads(result.stdout.strip())
            if params.response_format == ResponseFormat.MARKDOWN:
                return f"# UAC Status\n" + \
                       f"- **Status**: {data['Status']}\n" + \
                       f"- **Notification Level**: {data['Level']}"
            return result.stdout
        except json.JSONDecodeError:
            return "Error: Could not parse UAC status"
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_list_drivers", description="List all installed drivers and check for outdated ones.")
async def list_drivers(params: DriversInput) -> str:
    """List system drivers using PowerShell."""
    try:
        ps_script = """
        Get-WmiObject Win32_PnPSignedDriver | Select-Object DeviceName, DriverVersion, Manufacturer, Description | ConvertTo-Json
        """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_script], 
            capture_output=True, text=True, timeout=30, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        try:
            drivers = json.loads(result.stdout.strip())
            if not drivers:
                return "No drivers found"
            
            if params.response_format == ResponseFormat.MARKDOWN:
                lines = ["# Installed Drivers", ""]
                for driver in drivers[:20]:  # Limit to 20 for readability
                    lines.append(f"- **{driver['DeviceName']}**: v{driver['DriverVersion']} by {driver['Manufacturer']}")
                if len(drivers) > 20:
                    lines.append(f"\n... and {len(drivers)-20} more drivers")
                return "\n".join(lines)
            return result.stdout
        except json.JSONDecodeError:
            return "Error: Could not parse driver information"
    except subprocess.TimeoutExpired:
        return "Error: Driver list timed out (30s limit)"
    except Exception as e:
        return handle_error(e)