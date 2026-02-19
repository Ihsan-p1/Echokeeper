import discord
from utils.constants import LANG_DISPLAY_NAME


def translation_embed(
    original: str,
    translated: str,
    source_lang: str,
    target_lang: str,
    author: discord.User | discord.Member,
) -> discord.Embed:
    src_name = LANG_DISPLAY_NAME.get(source_lang, source_lang.upper())
    tgt_name = LANG_DISPLAY_NAME.get(target_lang, target_lang.upper())

    embed = discord.Embed(
        color=discord.Color.from_rgb(88, 101, 242),
    )
    embed.set_author(
        name=f"{author.display_name}",
        icon_url=author.display_avatar.url,
    )
    embed.add_field(
        name=f"🔤 {src_name}",
        value=f"```{original[:900]}```",
        inline=False,
    )
    embed.add_field(
        name=f"🌐 {tgt_name}",
        value=f"```{translated[:900]}```",
        inline=False,
    )
    embed.set_footer(text="Powered by Helsinki-NLP opus-mt · Open Source")
    return embed


def error_embed(message: str) -> discord.Embed:
    return discord.Embed(
        description=f"❌ {message}",
        color=discord.Color.red(),
    )


def success_embed(message: str) -> discord.Embed:
    return discord.Embed(
        description=f"✅ {message}",
        color=discord.Color.green(),
    )


def info_embed(title: str, message: str) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=message,
        color=discord.Color.blurple(),
    )
