import json
import asyncio

from redis.asyncio import Redis
from sqlmodel import Session, select
from app.models import OutboxEvent

from app.core.db import engine
from app.core.redis import redis_client


async def process_outbox(session: Session, redis: Redis) -> int:
    statement = (
        select(OutboxEvent)
        .where(OutboxEvent.processed == False)
        .order_by(OutboxEvent.id)
        .limit(100)
    )

    events = session.exec(statement).all()

    processed_count = 0

    for event in events:
        try:
            await redis.xadd(
                "events",
                {
                    "event_type": event.event_type,
                    "payload": event.payload,
                }
            )

            event.processed = True
            processed_count += 1

        except Exception:
            # Redis unavailable, network issue, etc.
            print("Error processing outbox event:", event.id)
            break

    session.commit()

    return processed_count



async def outbox_worker():
    while True:
        try:
            with Session(engine) as session:
                await process_outbox(
                    session=session,
                    redis=redis_client,
                )

        except Exception as exc:
            print(f"Outbox worker error: {exc}")

        await asyncio.sleep(1)