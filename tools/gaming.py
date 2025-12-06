import subprocess
import psutil
import json
import os
from pydantic import BaseModel, Field, ConfigDict
from server_instance import mcp
from utils import format_bytes, handle_error, ResponseFormat

# --- MODELS ---
class GPUStatsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class GamingProcessesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    action: str = Field(default="list", description="Action: 'list' (show running heavy apps) or 'kill' (terminate a process)")
    process_name: str | None = Field(default=None, description="Process name to terminate. Required for 'kill' action (e.g., 'chrome' or 'discord.exe')")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class SteamGamesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

# --- TOOLS ---
@mcp.tool(name="windows_gpu_stats", description="Get NVIDIA GPU statistics: temperature, usage, memory, and power draw. Requires NVIDIA GPU with drivers.")
async def gpu_stats(params: GPUStatsInput) -> str:
    """Get detailed NVIDIA GPU statistics using nvidia-smi."""
    try:
        cmd = ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total,power.draw", "--format=csv,noheader,nounits"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
        except FileNotFoundError:
            return "Error: NVIDIA GPU not found or nvidia-smi not in PATH"
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        data = result.stdout.strip().split(', ')
        if len(data) >= 7:
            gpu_info = {
                "name": data[0],
                "temperature": f"{data[1]}C",
                "gpu_usage": f"{data[2]}%",
                "memory_usage": f"{data[3]}%",
                "memory_used": f"{data[4]} MB",
                "memory_total": f"{data[5]} MB",
                "power_draw": f"{data[6]} W"
            }
            if params.response_format == ResponseFormat.MARKDOWN:
                return f"""# GPU Stats - {gpu_info['name']}
- **Temperature**: {gpu_info['temperature']}
- **GPU Usage**: {gpu_info['gpu_usage']}
- **Memory Usage**: {gpu_info['memory_usage']} ({gpu_info['memory_used']} / {gpu_info['memory_total']})
- **Power Draw**: {gpu_info['power_draw']}
"""
            return json.dumps(gpu_info, indent=2)
        return result.stdout
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_gaming_processes", description="List or kill resource-heavy processes (Chrome, Discord, Steam, etc.). Useful for freeing resources before gaming.")
async def gaming_processes(params: GamingProcessesInput) -> str:
    """List or kill commonly resource-heavy applications like browsers, Discord, Steam."""
    try:
        # Common gaming/heavy processes
        heavy_apps = [
            "chrome.exe", "firefox.exe", "msedge.exe", "teams.exe",
            "discord.exe", "spotify.exe", "steam.exe", "epicgameslauncher.exe"
        ]
        if params.action == "list":
            found_procs = []
            for proc in psutil.process_iter(['name', 'pid', 'memory_info', 'cpu_percent']):
                try:
                    if proc.info['name'].lower() in [h.lower() for h in heavy_apps]:
                        found_procs.append({
                            "name": proc.info['name'],
                            "pid": proc.info['pid'],
                            "memory": format_bytes(proc.info['memory_info'].rss),
                            "cpu": proc.info['cpu_percent']
                        })
                except:
                    continue
            if not found_procs:
                return "No heavy gaming/browser processes found running."
            if params.response_format == ResponseFormat.MARKDOWN:
                lines = ["# Heavy Processes Running\n"]
                for p in found_procs:
                    lines.append(f"- **{p['name']}** (PID: {p['pid']}) - Memory: {p['memory']}, CPU: {p['cpu']}%")
                return "\n".join(lines)
            return json.dumps(found_procs, indent=2)
        elif params.action == "kill":
            if not params.process_name:
                return "Error: process_name required for 'kill' action"
            killed = []
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    if params.process_name.lower() in proc.info['name'].lower():
                        proc.kill()
                        killed.append(proc.info['name'])
                except:
                    continue
            if killed:
                return f"Killed {len(killed)} instance(s) of '{params.process_name}'"
            return f"No process matching '{params.process_name}' found."
        return f"Unknown action: {params.action}. Use 'list' or 'kill'."
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_steam_games", description="List all installed Steam games by parsing Steam app manifests. Searches default Steam installation paths.")
async def steam_games(params: SteamGamesInput) -> str:
    """List installed Steam games by reading appmanifest files."""
    try:
        steam_paths = [
            "C:\\Program Files (x86)\\Steam\\steamapps",
            "C:\\Program Files\\Steam\\steamapps"
        ]
        games = []
        for steam_path in steam_paths:
            if not os.path.exists(steam_path):
                continue
            for file in os.listdir(steam_path):
                if file.startswith("appmanifest_") and file.endswith(".acf"):
                    try:
                        with open(os.path.join(steam_path, file), 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            # Simple parsing (Steam ACF format)
                            if '"name"' in content:
                                name_start = content.find('"name"') + 7
                                name_end = content.find('"', name_start + 1)
                                game_name = content[name_start:name_end]
                                games.append(game_name)
                    except:
                        continue
        if not games:
            return "No Steam games found or Steam not installed."
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Steam Games ({len(games)} found)\n"]
            for game in sorted(games):
                lines.append(f"- {game}")
            return "\n".join(lines)
        return json.dumps({"games": sorted(games)}, indent=2)
    except Exception as e:
        return handle_error(e)