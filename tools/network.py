import subprocess
import json
import socket
from pydantic import BaseModel, Field, ConfigDict
from server_instance import mcp
from utils import handle_error, ResponseFormat

# --- MODELS ---
class PingInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    host: str = Field(..., description="Host to ping (e.g., 'google.com' or '8.8.8.8')")
    count: int = Field(default=4, description="Number of ping attempts (default: 4)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class SpeedTestInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class NetworkInfoInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

# --- TOOLS ---
@mcp.tool(name="windows_ping", description="Ping a host and return latency statistics. Useful for network diagnostics.")
async def ping_host(params: PingInput) -> str:
    """Ping a host using Windows ping command and parse results."""
    try:
        result = subprocess.run(
            ["ping", "-n", str(params.count), params.host], 
            capture_output=True, text=True, timeout=20, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        output = result.stdout
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"```\n{output}\n```"
        return json.dumps({"output": output.split("\n")})
    except subprocess.TimeoutExpired:
        return "Error: Ping timed out (20s limit)"
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_speed_test", description="Run an internet speed test using speedtest-cli. Measures download, upload, and ping.")
async def speed_test(params: SpeedTestInput) -> str:
    """Run a network speed test using speedtest-cli."""
    try:
        # Check if speedtest-cli is installed
        try:
            subprocess.run(
                ["speedtest-cli", "--version"], 
                capture_output=True, text=True, timeout=5, 
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except FileNotFoundError:
            return "Error: speedtest-cli not installed. Install with: pip install speedtest-cli"
        
        result = subprocess.run(
            ["speedtest-cli", "--simple"], 
            capture_output=True, text=True, timeout=60, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        # Parse output
        lines = result.stdout.strip().split("\n")
        if len(lines) < 3:
            return "Error: Invalid speedtest output"
        
        ping = lines[0].split(":")[1].strip()
        download = lines[1].split(":")[1].strip()
        upload = lines[2].split(":")[1].strip()
        
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"# Internet Speed Test\n" + \
                   f"- **Ping**: {ping}\n" + \
                   f"- **Download**: {download}\n" + \
                   f"- **Upload**: {upload}"
        return json.dumps({
            "ping": ping,
            "download": download,
            "upload": upload
        })
    except subprocess.TimeoutExpired:
        return "Error: Speed test timed out (60s limit)"
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_network_info", description="Get detailed network information: IP addresses, interfaces, and DNS settings.")
async def network_info(params: NetworkInfoInput) -> str:
    """Get comprehensive network information using ipconfig and PowerShell."""
    try:
        # Get basic network info with ipconfig
        ipconfig_result = subprocess.run(
            ["ipconfig", "/all"], 
            capture_output=True, text=True, timeout=10, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # Get DNS info with PowerShell
        ps_script = """
        Get-DnsClientServerAddress | Select-Object InterfaceAlias, ServerAddresses | ConvertTo-Json
        Get-NetIPConfiguration | Select-Object InterfaceAlias, IPv4Address, IPv6Address | ConvertTo-Json
        """
        
        ps_result = subprocess.run(
            ["powershell", "-Command", ps_script], 
            capture_output=True, text=True, timeout=10, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"# Network Information\n\n" + \
                   f"## IP Config\n```\n{ipconfig_result.stdout}\n```\n\n" + \
                   f"## DNS Configuration\n```json\n{ps_result.stdout}\n```"
        return json.dumps({
            "ipconfig": ipconfig_result.stdout.split("\n"),
            "dns_info": json.loads(ps_result.stdout.strip())
        })
    except Exception as e:
        return handle_error(e)