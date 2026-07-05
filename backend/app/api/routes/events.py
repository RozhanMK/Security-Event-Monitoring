from typing import Any
import json

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from sqlmodel import select
from sqlmodel import Session

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    RateLimitDep
)
from app.models import (
    SecurityEventCreate,
    SecurityEventPublic, 
    SecurityEvent
)
from app.core.redis import redis_client
from app.core.connection_manager import manager
from app.api.deps import get_current_user_ws
from app.core.db import engine
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

@router.websocket("/ws")
async def events_ws(websocket: WebSocket):

    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    with Session(engine) as session:
        print("test1")
        user = await get_current_user_ws(session, token)
        print("test2")

    if not user:
        await websocket.close(code=1008)
        return
    
    await websocket.accept()

    await manager.connect(str(user.id), websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(str(user.id), websocket)

@router.get("/")
async def get_events(session: SessionDep, current_user: CurrentUser, limit: int = 100):
    statement = (
        select(SecurityEvent)
        .where(SecurityEvent.user_id == current_user.id)
        .order_by(SecurityEvent.created_at.desc())
        .limit(limit)
    )

    events = session.exec(statement).all()

    return events

@router.get("/redis-test")
async def redis_test(rate_limit: RateLimitDep):
    await redis_client.set("test", "hello")
    value = await redis_client.get("test")
    return {"value": value}