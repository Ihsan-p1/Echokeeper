import aiosqlite
import logging
from pathlib import Path

log = logging.getLogger("database")

DB_PATH = Path(__file__).parent / "bot.db"


async def init_db() -> None:
    """Create tables if they don't exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id     INTEGER PRIMARY KEY,
                target_lang TEXT    NOT NULL DEFAULT 'en',
                opt_in      INTEGER NOT NULL DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS auto_translate_channels (
                channel_id  TEXT PRIMARY KEY,
                target_lang TEXT NOT NULL DEFAULT 'en'
            )
        """)
        await db.commit()
    log.info(f"Database initialized at {DB_PATH}")


def get_connection() -> aiosqlite.Connection:
    return aiosqlite.connect(DB_PATH)
