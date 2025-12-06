import subprocess
import json
import time
import psutil
from pydantic import BaseModel, Field, ConfigDict
from server_instance import mcp
from utils import handle_error, ResponseFormat

# --- MODELS ---
class TemperatureInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class PerformanceHistoryInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    duration_seconds: int = Field(default=60, description="Duration in seconds to monitor performance")
    interval_seconds: int = Field(default=5, description="Interval between measurements in seconds")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class ResourceAlertsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    cpu_threshold: int = Field(default=80, description="CPU usage threshold percentage (0-100)")
    memory_threshold: int = Field(default=80, description="Memory usage threshold percentage (0-100)")
    disk_threshold: int = Field(default=90, description="Disk usage threshold percentage (0-100)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

# --- TOOLS ---
@mcp.tool(name="windows_get_temperatures", description="Get current CPU and GPU temperatures (if available). Requires Open Hardware Monitor or equivalent.")
async def get_temperatures(params: TemperatureInput) -> str:
    """Get system temperatures using PowerShell and WMI."""
    try:
        # Try to get CPU temperature using WMI (requires Open Hardware Monitor or similar)
        ps_script = """
        try {
            $cpuTemp = Get-WmiObject -Namespace "root\\OpenHardwareMonitor" -Class Sensor | Where-Object {$_.SensorType -eq 'Temperature' -and $_.Name -like '*CPU*'} | Select-Object -First 1 -ExpandProperty Value
            $gpuTemp = Get-WmiObject -Namespace "root\\OpenHardwareMonitor" -Class Sensor | Where-Object {$_.SensorType -eq 'Temperature' -and $_.Name -like '*GPU*'} | Select-Object -First 1 -ExpandProperty Value
            [PSCustomObject]@{CPU=$cpuTemp; GPU=$gpuTemp} | ConvertTo-Json
        } catch {
            Write-Output '{"error": "Open Hardware Monitor not installed or WMI access denied"}'
        }
        """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_script], 
            capture_output=True, text=True, timeout=10, 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode != 0:
            return "Error: Could not retrieve temperature data (Open Hardware Monitor required)"
        
        try:
            data = json.loads(result.stdout.strip())
            if "error" in data:
                return data["error"]
            
            if params.response_format == ResponseFormat.MARKDOWN:
                lines = ["# System Temperatures"]
                if "CPU" in data and data["CPU"]:
                    lines.append(f"- **CPU**: {data['CPU']}°C")
                if "GPU" in data and data["GPU"]:
                    lines.append(f"- **GPU**: {data['GPU']}°C")
                if not any(k in data for k in ["CPU", "GPU"]):
                    lines.append("- No temperature data available (install Open Hardware Monitor)")
                return "\n".join(lines)
            return result.stdout
        except json.JSONDecodeError:
            return "Error: Invalid temperature data format"
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_performance_history", description="Monitor CPU, memory, and disk usage over time. Returns a time series of system performance.")
async def performance_history(params: PerformanceHistoryInput) -> str:
    """Record system performance metrics at regular intervals."""
    try:
        measurements = []
        end_time = time.time() + params.duration_seconds
        
        while time.time() < end_time:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            measurements.append({
                "timestamp": time.strftime("%H:%M:%S"),
                "cpu": cpu,
                "memory": mem,
                "disk": disk
            })
            time.sleep(params.interval_seconds)
        
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = ["# Performance History", 
                     f"Duration: {params.duration_seconds}s | Interval: {params.interval_seconds}s", ""]
            lines.append("| Time     | CPU % | Memory % | Disk % |")
            lines.append("|----------|-------|----------|--------|")
            for m in measurements:
                lines.append(f"| {m['timestamp']} | {m['cpu']}   | {m['memory']}     | {m['disk']}   |")
            return "\n".join(lines)
        return json.dumps({"duration": params.duration_seconds, "interval": params.interval_seconds, "measurements": measurements})
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_resource_alerts", description="Check if system resources exceed specified thresholds. Returns alerts for CPU, memory, or disk usage.")
async def resource_alerts(params: ResourceAlertsInput) -> str:
    """Check system resource usage against specified thresholds."""
    try:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        
        alerts = []
        if cpu > params.cpu_threshold:
            alerts.append(f"⚠️ High CPU usage: {cpu}% (threshold: {params.cpu_threshold}%)")
        if mem > params.memory_threshold:
            alerts.append(f"⚠️ High memory usage: {mem}% (threshold: {params.memory_threshold}%)")
        if disk > params.disk_threshold:
            alerts.append(f"⚠️ High disk usage: {disk}% (threshold: {params.disk_threshold}%)")
        
        if not alerts:
            return "✅ All resources within normal limits"
        
        if params.response_format == ResponseFormat.MARKDOWN:
            return "# Resource Alerts\n\n" + "\n".join(alerts)
        return json.dumps({"alerts": alerts, "cpu": cpu, "memory": mem, "disk": disk})
    except Exception as e:
        return handle_error(e)