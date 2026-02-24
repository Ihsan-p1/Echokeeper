import discord
import asyncio
import logging
from discord.ext import commands
from config import DISCORD_TOKEN
from database.db import init_db
from services.nllb_backend import preload as preload_nllb

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("bot")


def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True

    bot = commands.Bot(
        command_prefix="!",
        intents=intents,
        help_command=None,
    )
    return bot


bot = create_bot()


async def startup() -> None:
    """Run startup tasks: DB init, model preloading."""
    log.info("Starting up EchoKeeper...")
    await init_db()
    # Preload NLLB model in a separate thread to avoid blocking the event loop
    try:
        log.info("Preloading NLLB-200 model...")
        await asyncio.to_thread(preload_nllb)
    except Exception as e:
        log.warning(f"Failed to preload NLLB model: {e}")


async def load_cogs() -> None:
    extensions = [
        "cogs.translate",
        "cogs.settings",
    ]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            log.info(f"Loaded extension: {ext}")
        except Exception as e:
            log.error(f"Failed to load extension {ext}: {e}")


@bot.event
async def on_ready() -> None:
    log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    # Guild sync = instan (tidak butuh propagasi)
    for guild in bot.guilds:
        await bot.tree.sync(guild=guild)
        log.info(f"Slash commands synced to guild: {guild.name} (ID: {guild.id})")
    # Global sync sebagai fallback (butuh waktu ~1 jam)
    await bot.tree.sync()
    log.info("Global slash command sync done.")


@bot.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx: commands.Context) -> None:
    """Force sync slash commands ke server ini (owner only)."""
    synced = await bot.tree.sync(guild=ctx.guild)
    await ctx.send(f"✅ Synced **{len(synced)}** slash command(s) ke server ini.", delete_after=10)
    log.info(f"Manual sync: {len(synced)} commands synced to {ctx.guild.name}")


@bot.event
async def on_command_error(ctx: commands.Context, error: Exception) -> None:
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"⏳ Cooldown aktif, coba lagi dalam `{error.retry_after:.1f}s`.",
            delete_after=5,
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Argumen kurang. Cek `!help`.", delete_after=5)
    elif isinstance(error, commands.NotOwner):
        pass  # ignore silently
    else:
        log.error(f"Unhandled error: {error}")


async def main() -> None:
    async with bot:
        await startup()
        await load_cogs()
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
