from redis.asyncio import Redis

from src.env import settings


async def get_redis_db_main() -> Redis:
    return Redis(
        host=settings.REDIS_HOST.get_secret_value(),
        port=int(settings.REDIS_PORT.get_secret_value()),
    )
