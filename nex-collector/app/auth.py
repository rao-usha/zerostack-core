"""Authentication middleware."""
from fastapi import Request, HTTPException
from .config import settings


async def verify_token(request: Request):
    """Verify Bearer token."""
    if request.url.path.startswith("/v1/"):
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        
        token = auth_header.replace("Bearer ", "")
        if token != settings.NEX_WRITE_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    return True

