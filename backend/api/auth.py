from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from config import settings

_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(key: str = Security(_header)) -> str:
    if not key or key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Pass it as the X-API-Key header."
        )
    return key
