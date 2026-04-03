from typing import Any, Optional


def api_response(success: bool, message: str, data: Optional[Any] = None) -> dict:
    """
    Small helper to keep route handlers consistent and readable.
    """
    return {"success": success, "message": message, "data": data}

