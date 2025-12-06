from enum import Enum
class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"
def format_bytes(bytes_value: int) -> str:
    """Format bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"
def handle_error(e: Exception) -> str:
    """Consistent error formatting across all tools."""
    return f"Error: {type(e).__name__}: {str(e)}"