import subprocess
import json
import psutil
from pydantic import BaseModel, Field, ConfigDict
from server_instance import mcp
from utils import handle_error, ResponseFormat

# --- MODELS ---
class ShutdownInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    action: str = Field(default="shutdown", description="Action to perform: 'shutdown', 'restart', or 'hibernate'")
    delay_minutes: int = Field(default=0, description="Delay in minutes before performing the action (default: 0)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class PowerPlanInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    plan: str = Field(default="high-performance", description="Power plan to set: 'high-performance', 'balanced', or 'power-saver'")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

# --- TOOLS ---
@mcp.tool(name="windows_system_shutdown", description="Shutdown, restart, or hibernate the system with optional delay.")
async def system_shutdown(params: ShutdownInput) -> str:
    """Shutdown, restart, or hibernate the system using shutdown command."""
    try:
        valid_actions = ["shutdown", "restart", "hibernate"]
        if params.action not in valid_actions:
            return f"Error: Invalid action '{params.action}'. Use one of: {', '.join(valid_actions)}"
        
        # Map action to shutdown command
        action_map = {
            "shutdown": "/s",
            "restart": "/r",
            "hibernate": "/h"
        }
        
        # Build command
        cmd = ["shutdown", action_map[params.action]]
        if params.delay_minutes > 0:
            cmd.extend(["/t", str(params.delay_minutes * 60)])
        
        # Execute
        result = subprocess.run(
            cmd, 
            capture_output=True, text=True, timeout=5, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        action_display = params.action.capitalize()
        delay_msg = f" in {params.delay_minutes} minutes" if params.delay_minutes > 0 else ""
        
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"⏳ System will {action_display}{delay_msg}. Use `shutdown /a` to cancel."
        return json.dumps({
            "status": "scheduled",
            "action": params.action,
            "delay_minutes": params.delay_minutes
        })
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_set_power_plan", description="Change the system power plan to optimize for performance, balance, or energy saving.")
async def set_power_plan(params: PowerPlanInput) -> str:
    """Change Windows power plan using PowerShell."""
    try:
        plan_map = {
            "high-performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
            "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
            "power-saver": "a1841308-3541-4fab-bc81-f71556f20b4a"
        }
        
        if params.plan not in plan_map:
            return f"Error: Invalid power plan '{params.plan}'. Use: high-performance, balanced, or power-saver"
        
        ps_script = f"""
        powercfg /setactive {plan_map[params.plan]}
        (Get-WmiObject -Class Win32_PowerPlan -Filter "IsActive=true").ElementName
        """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_script], 
            capture_output=True, text=True, timeout=10, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        active_plan = result.stdout.strip().split("\n")[-1]
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"⚡ Power plan set to: **{active_plan}**"
        return json.dumps({"status": "success", "power_plan": active_plan})
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_system_info", description="Get comprehensive system information including hardware, OS, and performance details.")
async def system_info(params: object = None) -> str:
    """Get detailed system information using systeminfo command."""
    try:
        result = subprocess.run(
            ["systeminfo"], 
            capture_output=True, text=True, timeout=15, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        
        return f"```\n{result.stdout}\n```"
    except subprocess.TimeoutExpired:
        return "Error: System info command timed out"
    except Exception as e:
        return handle_error(e)