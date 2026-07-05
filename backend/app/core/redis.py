import json
import asyncio
import redis.asyncio as redis
from app.core.connection_manager import manager

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)

async def redis_event_consumer():
    last_id = "$"

    while True:
        results = await redis_client.xread(
            {"events": last_id},
            block=5000
        )

        if not results:
            continue

        for _, messages in results:
            for message_id, fields in messages:
                last_id = message_id

                event = json.loads(fields[b"data"])

                user_id = event["user_id"]

                await manager.send_to_user(
                    user_id,
                    event
                )