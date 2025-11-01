import asyncio

from app.core.database import Base, engine
from app import models  # noqa: F401  Ensures model metadata is registered


async def init_models() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_models())
