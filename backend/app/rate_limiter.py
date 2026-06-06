from fastapi import HTTPException

from app.core.redis import redis_client


class FixedWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int, scope: str = "ip"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.scope = scope

        if scope == "ip":
            self.namespace = "ratelimit:ip:"
        elif scope == "user":
            self.namespace = "ratelimit:user:"
        else:
            raise ValueError("scope must be 'ip' or 'user'")

    async def check(self, identifier: str) -> None:
        key = f"{self.namespace}{identifier}"

        current = await redis_client.incr(key)

        if current == 1:
            await redis_client.expire(key, self.window_seconds)

        if current > self.max_requests:
            ttl = await redis_client.ttl(key)

            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {ttl} seconds.",
            )
        
