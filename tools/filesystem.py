import os
import shutil
import hashlib
import json
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from server_instance import mcp
from utils import format_bytes, handle_error, ResponseFormat

# --- MODELS ---
class FileSearchInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    path: str = Field(..., description="Directory path to search (e.g., 'C:\\Users\\Stan\\Downloads')")
    pattern: str = Field(default="*", description="File pattern to match (e.g., '*.jpg' or 'report_*.pdf')")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class FileOperationInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    source: str = Field(..., description="Source file or directory path")
    destination: str = Field(..., description="Destination path")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class DuplicateFilesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    path: str = Field(..., description="Directory path to scan for duplicates")
    min_size_mb: int = Field(default=1, description="Minimum file size in MB to consider (default: 1MB)")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

# --- TOOLS ---
@mcp.tool(name="windows_find_files", description="Search for files in a directory matching a specific pattern. Supports wildcards like *.jpg or report_*.pdf.")
async def find_files(params: FileSearchInput) -> str:
    """Search for files in a directory using glob patterns."""
    try:
        path_obj = Path(params.path)
        if not path_obj.is_dir():
            return f"Error: {params.path} is not a valid directory"
        
        found_files = []
        for file in path_obj.glob(params.pattern):
            if file.is_file():
                found_files.append({
                    "name": file.name,
                    "path": str(file),
                    "size": format_bytes(file.stat().st_size)
                })
        
        if not found_files:
            return f"No files matching '{params.pattern}' found in {params.path}"
        
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Found {len(found_files)} file(s) matching '{params.pattern}' in {params.path}"]
            for f in found_files:
                lines.append(f"- **{f['name']}**: {f['size']} ({f['path']})")
            return "\n".join(lines)
        return json.dumps(found_files, indent=2)
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_copy_file", description="Copy a file or directory from source to destination. Supports both files and folders.")
async def copy_file(params: FileOperationInput) -> str:
    """Copy files or directories with progress feedback."""
    try:
        source = Path(params.source)
        dest = Path(params.destination)
        
        if not source.exists():
            return f"Error: Source path '{params.source}' does not exist"
        
        if source.is_dir():
            shutil.copytree(source, dest)
            action = "copied"
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
            action = "copied"
        
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"✅ Successfully {action} **{source.name}** to **{dest}**"
        return json.dumps({"status": "success", "action": action, "source": str(source), "destination": str(dest)})
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_find_duplicates", description="Find duplicate files in a directory based on size and content hash. Only considers files larger than min_size_mb.")
async def find_duplicates(params: DuplicateFilesInput) -> str:
    """Find duplicate files by comparing file sizes and hashes."""
    try:
        path_obj = Path(params.path)
        if not path_obj.is_dir():
            return f"Error: {params.path} is not a valid directory"
        
        # Group files by size first
        files_by_size = {}
        min_size = params.min_size_mb * 1024 * 1024
        
        for file in path_obj.rglob("*"):
            if file.is_file() and file.stat().st_size >= min_size:
                size = file.stat().st_size
                if size not in files_by_size:
                    files_by_size[size] = []
                files_by_size[size].append(file)
        
        # Find duplicates by comparing hashes
        duplicates = []
        for size, files in files_by_size.items():
            if len(files) > 1:
                # Group files by hash
                hash_groups = {}
                for file in files:
                    with open(file, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    if file_hash not in hash_groups:
                        hash_groups[file_hash] = []
                    hash_groups[file_hash].append(file)
                
                # Add groups with >1 file to duplicates
                for hash_val, files in hash_groups.items():
                    if len(files) > 1:
                        duplicates.append({
                            "hash": hash_val,
                            "files": [{"name": f.name, "path": str(f), "size": format_bytes(f.stat().st_size)} for f in files]
                        })
        
        if not duplicates:
            return f"No duplicate files found in {params.path} (min size: {params.min_size_mb}MB)"
        
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Found {len(duplicates)} duplicate group(s) in {params.path}"]
            for i, dup_group in enumerate(duplicates, 1):
                lines.append(f"\n## Group {i} (Hash: {dup_group['hash'][:8]}...)")
                for f in dup_group['files']:
                    lines.append(f"- {f['name']}: {f['size']} at `{f['path']}`")
            return "\n".join(lines)
        return json.dumps(duplicates, indent=2)
    except Exception as e:
        return handle_error(e)