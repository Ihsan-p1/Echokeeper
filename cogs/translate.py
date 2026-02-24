import discord
import logging
from discord.ext import commands
from services.translator import translate_text, TranslationError
from services.language_detect import detect_language
from services.queue import translate_queue
from database.models import (
    get_user_settings,
    get_channel_target_lang,
)
from database.db import init_db
from utils.embeds import translation_embed, error_embed
from utils.constants import (
    SUPPORTED_LANGUAGES,
    TRANSLATE_REACTION,
    MAX_TEXT_LENGTH,
)
from config import DEFAULT_TARGET_LANG, COOLDOWN_SECONDS

log = logging.getLogger("cog.translate")


class TranslateCog(commands.Cog, name="Translate"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        # DB initialization moved to bot.startup()
        translate_queue.start()
        log.info("TranslateCog loaded.")

    async def cog_unload(self) -> None:
        translate_queue.stop()

    # ─── Helper ──────────────────────────────────────────────────────────────

    async def _send_response(
        self,
        target: discord.Message | discord.Interaction,
        content: str | None = None,
        embed: discord.Embed | None = None,
        ephemeral: bool = False,
    ) -> None:
        """Unified helper to send response to Message or Interaction."""
        if isinstance(target, discord.Message):
            await target.reply(content=content, embed=embed, mention_author=False)
        else:
            if target.response.is_done():
                await target.followup.send(content=content, embed=embed, ephemeral=ephemeral)
            else:
                await target.response.send_message(content=content, embed=embed, ephemeral=ephemeral)

    async def _get_target_lang(self, user_id: int) -> str:
        """Helper to get user's target language with fallback to default."""
        settings = await get_user_settings(user_id)
        return settings.target_lang or DEFAULT_TARGET_LANG

    async def _do_translate(
        self,
        text: str,
        source: str,
        target: str,
        reply_target: discord.Message | discord.Interaction,
        author: discord.User | discord.Member,
    ) -> None:
        if len(text) > MAX_TEXT_LENGTH:
            msg = f"Teks terlalu panjang (maks {MAX_TEXT_LENGTH} karakter)."
            await self._send_response(reply_target, embed=error_embed(msg), ephemeral=True)
            return

        try:
            translated = await translate_queue.submit(
                translate_text(text, target=target, source=source)
            )
        except TranslationError as e:
            await self._send_response(reply_target, embed=error_embed(str(e)), ephemeral=True)
            return

        embed = translation_embed(text, translated, source, target, author)
        await self._send_response(reply_target, embed=embed)

    # ─── Command: !tl ────────────────────────────────────────────────────────

    @commands.command(name="tl", help="Terjemahkan teks. Usage: !tl [lang] <teks>")
    @commands.cooldown(1, COOLDOWN_SECONDS, commands.BucketType.user)
    async def tl(self, ctx: commands.Context, *, args: str) -> None:
        """
        !tl <teks>          → translate ke bahasa default user / en
        !tl vi <teks>       → translate ke Vietnamese
        """
        parts = args.split(maxsplit=1)
        if len(parts) >= 2 and parts[0].lower() in SUPPORTED_LANGUAGES:
            target = parts[0].lower()
            text = parts[1]
        else:
            text = args
            target = await self._get_target_lang(ctx.author.id)

        source = detect_language(text)
        async with ctx.typing():
            await self._do_translate(text, source, target, ctx.message, ctx.author)

    # ─── Slash Command: /tl ──────────────────────────────────────────────────

    @discord.app_commands.command(name="tl", description="Translate text to your chosen language")
    @discord.app_commands.describe(
        text="Text to translate",
        target="Target language code: en, id, vi, etc.",
    )
    async def slash_tl(
        self,
        interaction: discord.Interaction,
        text: str,
        target: str = "",
    ) -> None:
        await interaction.response.defer()
        if not target:
            target = await self._get_target_lang(interaction.user.id)

        target = target.lower()
        if target not in SUPPORTED_LANGUAGES:
            await interaction.followup.send(
                embed=error_embed(f"Bahasa `{target}` tidak didukung."), ephemeral=True
            )
            return

        source = detect_language(text)
        await self._do_translate(text, source, target, interaction, interaction.user)

    # ─── Auto-translate channel ───────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        if not message.content.strip():
            return

        channel_target = await get_channel_target_lang(str(message.channel.id))
        if channel_target is None:
            return

        source = detect_language(message.content)
        if source == channel_target:
            return  # Sudah dalam bahasa tujuan

        await self._do_translate(
            message.content, source, channel_target, message, message.author
        )

    # ─── Reaction trigger (🌐) ────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if str(payload.emoji) != TRANSLATE_REACTION:
            return
        if payload.user_id == self.bot.user.id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        if not message.content.strip():
            return

        user = self.bot.get_user(payload.user_id) or await self.bot.fetch_user(payload.user_id)
        target = await self._get_target_lang(payload.user_id)
        source = detect_language(message.content)

        await self._do_translate(message.content, source, target, message, user)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TranslateCog(bot))
