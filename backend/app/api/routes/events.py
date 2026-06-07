from typing import Any

from fastapi import APIRouter, Request

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    RateLimitDep
)
from app.models import (
    SecurityEventCreate,
    SecurityEventPublic
)
from app.core.redis import redis_client

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=SecurityEventPublic)
def create_security_event(rate_limit: RateLimitDep, session: SessionDep, request: Request, current_user: CurrentUser, event_in: SecurityEventCreate,
) -> Any:
    ip = event_in.ip or request.client.host

    event_in.ip = ip

    return crud.create_event(
        session=session,
        event_type=event_in.event_type,
        severity=event_in.severity,
        source=event_in.source,
        event_data=event_in.event_data,
        ip=event_in.ip,
        user_id=current_user.id,
    )

@router.get("/redis-test")
async def redis_test(rate_limit: RateLimitDep):
    await redis_client.set("test", "hello")
    value = await redis_client.get("test")
    return {"value": value}