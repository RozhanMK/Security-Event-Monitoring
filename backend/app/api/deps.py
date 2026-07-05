from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import TokenPayload, User
from app.rate_limiter import FixedWindowRateLimiter

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

def decode_access_token(token: str) -> TokenPayload:
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[security.ALGORITHM],
    )
    return TokenPayload(**payload)

async def get_current_user_ws(session, token: str) -> User:
    try:
        token_data = decode_access_token(token)
    except (InvalidTokenError, ValidationError):
        return None

    return session.get(User, token_data.sub)

def rate_limit(scope: str = "ip", limit: int = 5, window: int = 60):
    limiter = FixedWindowRateLimiter(limit, window, scope)

    async def dependency(request: Request):
        key = request.client.host
        await limiter.check(key)

    return dependency

RateLimitDep = Annotated[None, Depends(rate_limit("ip", 5, 60))]