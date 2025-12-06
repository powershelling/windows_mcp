import subprocess
import os
import json
from pydantic import BaseModel, Field, ConfigDict
from server_instance import mcp
from utils import handle_error, ResponseFormat
# --- MODELS ---
class CreateTaskInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    task_name: str = Field(..., description="Unique name for the scheduled task (e.g., 'DailyBackup')")
    command: str = Field(..., description="Full path to executable or script to run (e.g., 'C:\\Scripts\\backup.bat')")
    trigger: str = Field(default="DAILY", description="Schedule trigger: 'DAILY', 'WEEKLY', 'MONTHLY', 'ONLOGON', or 'ONSTARTUP'")
    start_time: str = Field(default="09:00", description="Start time in HH:MM format (24-hour). Not used for ONLOGON/ONSTARTUP")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")
class RunScriptInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    script_path: str = Field(..., description="Full path to script file (e.g., 'C:\\Scripts\\deploy.ps1' or 'C:\\Scripts\\run.bat')")
    script_type: str = Field(default="auto", description="Script type: 'batch' (.bat/.cmd), 'powershell' (.ps1), or 'auto' (detect from extension)")
    wait: bool = Field(default=True, description="If True, waits for script to finish and returns output. If False, starts in background")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")
class EnvVarInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    action: str = Field(..., description="Action: 'get' (read one), 'set' (create/update), 'delete' (remove), 'list' (show all)")
    var_name: str | None = Field(default=None, description="Variable name. Required for get/set/delete actions")
    var_value: str | None = Field(default=None, description="Value to set. Required for set action")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

# --- TOOLS ---

def windows_create_scheduled_task(input: CreateTaskInput) -> str | dict:
    """Create a Windows scheduled task."""
    try:
        # Implementation here
        return f"Task '{input.task_name}' created successfully."
    except Exception as e:
        return handle_error(e)

def windows_env_variables(action: str, var_name: str | None = None, var_value: str | None = None) -> str | dict:
    """Get, set, or delete environment variables."""
    try:
        # Implementation here
        return f"Environment variable operation '{action}' completed."
    except Exception as e:
        return handle_error(e)

def windows_run_script(input: RunScriptInput) -> str | dict:
    """Run a script file (.bat, .ps1, etc.) with optional output capture."""
    try:
        # Implementation here
        return f"Script '{input.script_path}' executed."
    except Exception as e:
        return handle_error(e)