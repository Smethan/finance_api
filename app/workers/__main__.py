import asyncio

from loguru import logger

from app.core.logging import configure_logging
from app.workers.sync_worker import run_full_sync


def main() -> None:
    configure_logging()
    logger.info("Starting scheduled sync run")
    asyncio.run(run_full_sync())
    logger.info("Scheduled sync run complete")


if __name__ == "__main__":
    main()
