"""
backend/app/graph/checkpoint.py
"""
import sys
import asyncio
import selectors
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.config.settings import settings

if sys.platform == "win32":
    try:
        loop = asyncio.get_event_loop()
        if not isinstance(loop, asyncio.SelectorEventLoop):
            selector_loop = asyncio.SelectorEventLoop(selectors.SelectSelector())
            asyncio.set_event_loop(selector_loop)
    except RuntimeError:
        pass


@asynccontextmanager
async def get_postgres_checkpointer():
    async with AsyncPostgresSaver.from_conn_string(
        settings.DATABASE_URL
    ) as checkpointer:
        await checkpointer.setup()
        yield checkpointer