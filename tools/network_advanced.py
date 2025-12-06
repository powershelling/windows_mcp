import subprocess
import json
from pydantic import BaseModel, Field, ConfigDict
from server_instance import mcp
from utils import handle_error, ResponseFormat

# --- MODELS ---
class PortScanInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    host: str = Field(..., description="Host or IP address to scan (e.g., '192.168.1.1' or 'google.com')")
    ports: str = Field(default="21-23,80,443,3389", description="Ports to scan (e.g., '21-23,80,443' or '1-1000')")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class FirewallRuleInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    action: str = Field(..., description="Action: 'list', 'enable', or 'disable'")
    name: str = Field(default=None, description="Rule name (required for enable/disable)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

# --- TOOLS ---
@mcp.tool(name="windows_port_scan", description="Scan network ports on a remote host. Useful for security audits and troubleshooting.")
async def port_scan(params: PortScanInput) -> str:
    """Scan ports on a remote host using PowerShell Test-NetConnection."""
    try:
        # Validate ports format
        try:
            port_ranges = []
            for part in params.ports.split(','):
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    port_ranges.extend(range(start, end + 1))
                else:
                    port_ranges.append(int(part))
            ports = sorted(set(port_ranges))  # Remove duplicates and sort
            if not ports:
                return "Error: No valid ports specified"
        except ValueError:
            return "Error: Invalid port format. Use '80' or '1-1000'"
        
        # Scan ports
        open_ports = []
        for port in ports:
            try:
                result = subprocess.run(
                    ["powershell", "-Command", f"Test-NetConnection -ComputerName {params.host} -Port {port} -InformationLevel Quiet"],
                    capture_output=True, text=True, timeout=5, 
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0 and "True" in result.stdout:
                    open_ports.append(port)
            except:
                continue
        
        if not open_ports:
            return f"No open ports found on {params.host} (scanned: {len(ports)} ports)"
        
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"# Port Scan Results for {params.host}\n\n" + \
                   f"Open ports: **{', '.join(map(str, open_ports))}**\n" + \
                   f"Scanned: {len(ports)} ports"
        return json.dumps({"host": params.host, "open_ports": open_ports, "scanned_ports": ports})
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_firewall_rule", description="Manage Windows firewall rules: list, enable, or disable specific rules.")
async def firewall_rule(params: FirewallRuleInput) -> str:
    """Manage Windows firewall rules using PowerShell."""
    try:
        if params.action == "list":
            ps_script = "Get-NetFirewallRule | Select-Object DisplayName, Enabled, Direction, Action | ConvertTo-Json"
        elif params.action in ["enable", "disable"]:
            if not params.name:
                return "Error: Rule name required for enable/disable"
            ps_script = f"Get-NetFirewallRule -DisplayName '*{params.name}*' | {{ $_.DisplayName; {params.action}-NetFirewallRule -DisplayName $_.DisplayName }}"
        else:
            return "Error: Invalid action. Use 'list', 'enable', or 'disable'"
        
        result = subprocess.run(
            ["powershell", "-Command", ps_script], 
            capture_output=True, text=True, timeout=15, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        if params.action == "list":
            try:
                rules = json.loads(result.stdout.strip())
                if not rules:
                    return "No firewall rules found"
                
                if params.response_format == ResponseFormat.MARKDOWN:
                    lines = ["# Firewall Rules", ""]
                    for rule in rules[:20]:  # Limit to 20 for readability
                        status = "✅" if rule['Enabled'] else "❌"
                        lines.append(f"- {status} **{rule['DisplayName']}**: {rule['Direction']} → {rule['Action']}")
                    if len(rules) > 20:
                        lines.append(f"\n... and {len(rules)-20} more rules")
                    return "\n".join(lines)
                return result.stdout
            except json.JSONDecodeError:
                return "Error: Could not parse firewall rules"
        else:
            if params.response_format == ResponseFormat.MARKDOWN:
                return f"✅ Firewall rule '{params.name}' {params.action}d"
            return json.dumps({"status": "success", "action": params.action, "rule": params.name})
    except subprocess.TimeoutExpired:
        return "Error: Firewall operation timed out"
    except Exception as e:
        return handle_error(e)