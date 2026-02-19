# EchoKeeper

A Discord bot for real-time text translation across Vietnamese, English, and Indonesian, with support for 14 additional languages. Built with discord.py and Helsinki-NLP open-source models via HuggingFace.

## Features

- Prefix command `!tl` and slash command `/tl` for on-demand translation
- Reaction-based translation trigger
- Per-channel auto-translate
- Per-user language preference stored in SQLite
- Async queue to avoid API rate limits

## Requirements

- Python 3.10+
- A Discord bot token ([discord.com/developers](https://discord.com/developers))
- A HuggingFace API token ([huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)) — free

## Installation

```bash
git clone https://github.com/Ihsan-p1/Echokeeper.git
cd Echokeeper
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your tokens, then run:

```bash
python bot.py
```

## Commands

| Command | Description |
|---|---|
| `!tl <text>` | Translate to your default language |
| `!tl <lang> <text>` | Translate to a specific language |
| `/tl` | Slash command version of `!tl` |
| `/lang <code>` | Set your default target language |
| `/optin` | Toggle auto-translate for your messages |
| `/myinfo` | View your current settings |
| `/languages` | List all supported language codes |
| `/setchannel <lang>` | (Admin) Enable auto-translate in this channel |
| `/removechannel` | (Admin) Disable auto-translate in this channel |
| React with globe emoji | Translate a message to your default language |

## Supported Languages

`en` `id` `vi` `ms` `zh` `ja` `ko` `ar` `fr` `de` `es` `pt` `ru` `hi`

## Project Structure

```
EchoKeeper/
├── bot.py
├── config.py
├── cogs/
│   ├── translate.py
│   └── settings.py
├── services/
│   ├── translator.py
│   ├── language_detect.py
│   └── queue.py
├── database/
│   ├── db.py
│   └── models.py
└── utils/
    ├── embeds.py
    └── constants.py
```

## License

MIT
