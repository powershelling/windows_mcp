import os
import shutil
import zipfile
import json
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from server_instance import mcp
from utils import format_bytes, handle_error, ResponseFormat

# --- MODELS ---
class FileCompressInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    source: str = Field(..., description="File or directory to compress (e.g., 'C:\\Users\\Stan\\Documents\\Project')")
    destination: str = Field(..., description="Destination ZIP file path (e.g., 'C:\\Users\\Stan\\backup.zip')")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

class FileEncryptInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    source: str = Field(..., description="File to encrypt (e.g., 'C:\\Users\\Stan\\secret.txt')")
    destination: str = Field(..., description="Destination encrypted file path (e.g., 'C:\\Users\\Stan\\secret.enc')")
    password: str = Field(..., description="Password for encryption")
    response_format: ResponseFormat = Field(default=ResponseFormat.MARKDOWN, description="Output format: 'markdown' for readable text, 'json' for structured data")

# --- TOOLS ---
@mcp.tool(name="windows_compress_files", description="Compress files or directories into a ZIP archive.")
async def compress_files(params: FileCompressInput) -> str:
    """Compress files or directories into a ZIP archive."""
    try:
        source_path = Path(params.source)
        dest_path = Path(params.destination)
        
        if not source_path.exists():
            return f"Error: Source path '{params.source}' does not exist"
        
        if dest_path.exists():
            return f"Error: Destination file '{params.destination}' already exists"
        
        if source_path.is_dir():
            # Compress directory
            with zipfile.ZipFile(dest_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in source_path.rglob('*'):
                    if file.is_file():
                        zipf.write(file, file.relative_to(source_path))
        else:
            # Compress single file
            with zipfile.ZipFile(dest_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(source_path, source_path.name)
        
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"✅ Compressed **{source_path.name}** to **{dest_path}** (Size: {format_bytes(dest_path.stat().st_size)})"
        return json.dumps({
            "status": "success",
            "source": str(source_path),
            "destination": str(dest_path),
            "size": dest_path.stat().st_size
        })
    except Exception as e:
        return handle_error(e)

@mcp.tool(name="windows_encrypt_file", description="Encrypt a file using AES encryption (requires pycryptodome).")
async def encrypt_file(params: FileEncryptInput) -> str:
    """Encrypt a file using AES encryption with a password."""
    try:
        from Crypto.Cipher import AES
        from Crypto.Protocol.KDF import PBKDF2
        from Crypto.Util.Padding import pad
        import base64
        
        source_path = Path(params.source)
        dest_path = Path(params.destination)
        
        if not source_path.exists():
            return f"Error: Source file '{params.source}' does not exist"
        
        if dest_path.exists():
            return f"Error: Destination file '{params.destination}' already exists"
        
        # Generate key from password
        salt = os.urandom(16)
        key = PBKDF2(params.password, salt, dkLen=32, count=1000000)
        
        # Encrypt file
        cipher = AES.new(key, AES.MODE_CBC)
        with open(source_path, 'rb') as f:
            data = f.read()
        
        padded_data = pad(data, AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        
        # Save encrypted file with salt and IV prepended
        with open(dest_path, 'wb') as f:
            f.write(salt + cipher.iv + encrypted_data)
        
        if params.response_format == ResponseFormat.MARKDOWN:
            return f"🔒 Encrypted **{source_path.name}** to **{dest_path}** (Size: {format_bytes(dest_path.stat().st_size)})"
        return json.dumps({
            "status": "success",
            "source": str(source_path),
            "destination": str(dest_path),
            "size": dest_path.stat().st_size
        })
    except ImportError:
        return "Error: pycryptodome required for encryption. Install with: pip install pycryptodome"
    except Exception as e:
        return handle_error(e)