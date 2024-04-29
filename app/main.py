from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from app.database import engine
from app.models import Base
from app.utils.logging import AppLogger
from app.api.user import router as user_router
from app.api.health import router as health_router
from app.redis import get_redis, get_cache
from app.services.auth import AuthBearer

logger = AppLogger().get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the redis connection
    app.state.redis = await get_redis()
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    try:
        # Initialize the cache with the redis connection
        redis_cache = await get_cache()
        FastAPICache.init(RedisBackend(redis_cache), prefix="fastapi-cache")
        logger.info(FastAPICache.get_cache_status_header())
        yield
    finally:
        # close redis connection and release the resources
        await app.state.redis.close()


app = FastAPI(title="Stuff And Nonsense API", version="0.6", lifespan=lifespan)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.include_router(user_router)


app.include_router(health_router, prefix="/v1/public/health", tags=["Health, Public"])
app.include_router(
    health_router,
    prefix="/v1/health",
    tags=["Health, Bearer"],
    dependencies=[Depends(AuthBearer())],
)
