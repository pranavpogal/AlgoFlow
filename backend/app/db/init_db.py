from app.db.base import Base
from app.db.session import engine
from app.core.config import get_settings


async def init_db() -> None:
    if not get_settings().auto_create_db_schema:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
