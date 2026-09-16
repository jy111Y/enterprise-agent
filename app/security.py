import os
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)

def require_api_key(
        provided_key: str | None = Security(api_key_header),
) -> None:
    expected_key = os.getenv("APP_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="APP_API_KEY未配置",
        )

    if(
        provided_key is None
        or not secrets.compare_digest(provided_key, expected_key)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或缺少 X-API-Key",
        )
    