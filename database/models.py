from dataclasses import dataclass
import aiosqlite
from database.db import get_connection


@dataclass
class UserSettings:
    user_id: int
    target_lang: str = "en"
    opt_in: bool = False


async def get_user_settings(user_id: int) -> UserSettings:
    async with get_connection() as db:
        async with db.execute(
            "SELECT target_lang, opt_in FROM user_settings WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return UserSettings(user_id=user_id, target_lang=row[0], opt_in=bool(row[1]))
            return UserSettings(user_id=user_id)


async def set_user_lang(user_id: int, lang: str) -> None:
    async with get_connection() as db:
        await db.execute("""
            INSERT INTO user_settings (user_id, target_lang, opt_in)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET target_lang = excluded.target_lang
        """, (user_id, lang))
        await db.commit()


async def set_user_optin(user_id: int, opt_in: bool) -> None:
    async with get_connection() as db:
        await db.execute("""
            INSERT INTO user_settings (user_id, opt_in)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET opt_in = excluded.opt_in
        """, (user_id, int(opt_in)))
        await db.commit()


async def get_channel_target_lang(channel_id: str) -> str | None:
    async with get_connection() as db:
        async with db.execute(
            "SELECT target_lang FROM auto_translate_channels WHERE channel_id = ?",
            (channel_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def set_channel_lang(channel_id: str, lang: str) -> None:
    async with get_connection() as db:
        await db.execute("""
            INSERT INTO auto_translate_channels (channel_id, target_lang)
            VALUES (?, ?)
            ON CONFLICT(channel_id) DO UPDATE SET target_lang = excluded.target_lang
        """, (channel_id, lang))
        await db.commit()


async def remove_channel(channel_id: str) -> None:
    async with get_connection() as db:
        await db.execute(
            "DELETE FROM auto_translate_channels WHERE channel_id = ?",
            (channel_id,),
        )
        await db.commit()
