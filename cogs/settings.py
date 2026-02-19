import discord
import logging
from discord.ext import commands
from database.models import (
    get_user_settings,
    set_user_lang,
    set_user_optin,
    set_channel_lang,
    remove_channel,
)
from database.db import init_db
from utils.embeds import success_embed, error_embed, info_embed
from utils.constants import SUPPORTED_LANGUAGES, LANG_DISPLAY_NAME

log = logging.getLogger("cog.settings")


class SettingsCog(commands.Cog, name="Settings"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        await init_db()
        log.info("SettingsCog loaded.")

    # ─── /lang ───────────────────────────────────────────────────────────────

    @discord.app_commands.command(
        name="lang",
        description="Set your default translation language",
    )
    @discord.app_commands.describe(code="Language code: en, id, vi, etc.")
    async def slash_lang(self, interaction: discord.Interaction, code: str) -> None:
        code = code.lower().strip()
        if code not in SUPPORTED_LANGUAGES:
            supported = ", ".join(f"`{k}` ({v})" for k, v in LANG_DISPLAY_NAME.items())
            await interaction.response.send_message(
                embed=error_embed(
                    f"Bahasa `{code}` tidak didukung.\n\n**Tersedia:**\n{supported}"
                ),
                ephemeral=True,
            )
            return

        await set_user_lang(interaction.user.id, code)
        lang_name = LANG_DISPLAY_NAME.get(code, code.upper())
        await interaction.response.send_message(
            embed=success_embed(
                f"Bahasa default kamu diatur ke **{lang_name}** (`{code}`)."
            ),
            ephemeral=True,
        )

    # ─── /optin ──────────────────────────────────────────────────────────────

    @discord.app_commands.command(
        name="optin",
        description="Enable / disable auto-translate for your messages",
    )
    async def slash_optin(self, interaction: discord.Interaction) -> None:
        settings = await get_user_settings(interaction.user.id)
        new_state = not settings.opt_in
        await set_user_optin(interaction.user.id, new_state)
        status = "✅ Aktif" if new_state else "❌ Nonaktif"
        await interaction.response.send_message(
            embed=success_embed(f"Auto-translate: **{status}**"),
            ephemeral=True,
        )

    # ─── /myinfo ─────────────────────────────────────────────────────────────

    @discord.app_commands.command(
        name="myinfo",
        description="View your current translation settings",
    )
    async def slash_myinfo(self, interaction: discord.Interaction) -> None:
        settings = await get_user_settings(interaction.user.id)
        lang_name = LANG_DISPLAY_NAME.get(settings.target_lang, settings.target_lang.upper())
        optin_text = "✅ Aktif" if settings.opt_in else "❌ Nonaktif"
        await interaction.response.send_message(
            embed=info_embed(
                "⚙️ Pengaturan Kamu",
                f"**Bahasa default:** {lang_name} (`{settings.target_lang}`)\n"
                f"**Auto-translate:** {optin_text}",
            ),
            ephemeral=True,
        )

    # ─── /setchannel (Admin only) ─────────────────────────────────────────────

    @discord.app_commands.command(
        name="setchannel",
        description="[Admin] Set this channel as an auto-translate channel",
    )
    @discord.app_commands.describe(lang="Target language code for this channel")
    @discord.app_commands.default_permissions(manage_channels=True)
    async def slash_setchannel(
        self, interaction: discord.Interaction, lang: str = "en"
    ) -> None:
        lang = lang.lower().strip()
        if lang not in SUPPORTED_LANGUAGES:
            await interaction.response.send_message(
                embed=error_embed(f"Bahasa `{lang}` tidak didukung."),
                ephemeral=True,
            )
            return

        await set_channel_lang(str(interaction.channel_id), lang)
        lang_name = LANG_DISPLAY_NAME.get(lang, lang.upper())
        await interaction.response.send_message(
            embed=success_embed(
                f"Channel ini diset sebagai auto-translate → **{lang_name}** (`{lang}`)."
            )
        )

    # ─── /removechannel (Admin only) ──────────────────────────────────────────

    @discord.app_commands.command(
        name="removechannel",
        description="[Admin] Remove this channel from auto-translate",
    )
    @discord.app_commands.default_permissions(manage_channels=True)
    async def slash_removechannel(self, interaction: discord.Interaction) -> None:
        await remove_channel(str(interaction.channel_id))
        await interaction.response.send_message(
            embed=success_embed("Channel ini dihapus dari daftar auto-translate.")
        )

    # ─── /languages ───────────────────────────────────────────────────────────

    @discord.app_commands.command(
        name="languages",
        description="View all supported languages",
    )
    async def slash_languages(self, interaction: discord.Interaction) -> None:
        rows = "\n".join(
            f"`{code}` — {name}" for code, name in LANG_DISPLAY_NAME.items()
        )
        await interaction.response.send_message(
            embed=info_embed("🌐 Bahasa yang Didukung", rows),
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SettingsCog(bot))
