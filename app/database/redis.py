from redis.asyncio import Redis
from app.config import settings


class RedisClient:
    def __init__(self):
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )

    async def add_token_to_blacklist(self, jti: str) -> None:
        await self.redis.set(jti, "")

    async def is_token_blacklisted(self, jti: str) -> bool:
        return await self.redis.exists(jti)

    async def check_rate_limit(
        self, key: str, max_requests: int, window_seconds: int
    ) -> bool:
        """
        Returns True if request is ALLOWED under the rate limit, False if EXCEEDED.
        Uses Redis INCR and EXPIRE for atomic rate-limiting.
        """
        try:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, window_seconds)
            return current <= max_requests
        except Exception:
            return True


redis_db = RedisClient()
