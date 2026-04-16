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
        await self.redis(jti, "")

    async def is_token_blacklisted(self, jti: str) -> bool:
        return await self.redis.exists(jti)


redis_db = RedisClient()
