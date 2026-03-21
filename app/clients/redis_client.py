import aioredis


class RedisClient:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)

    async def set(self, key: str, value: str, ttl: int = 300):
        await self.redis.set(key, value, ex=ttl)

    async def get(self, key: str) -> str | None:
        return await self.redis.get(key)

    async def delete(self, key: str):
        await self.redis.delete(key)
