# EchoKeeper 🌐

A Discord translation bot supporting **Vietnamese 🇻🇳 · English 🇬🇧 · Indonesian 🇮🇩** and 14 other languages — powered by [Helsinki-NLP opus-mt](https://huggingface.co/Helsinki-NLP) open-source models.

---

## ✨ Features

- `!tl` & `/tl` — Translate any text on command
- 🌐 **Reaction trigger** — React to any message to translate it
- 🔁 **Auto-translate channels** — Set a channel to auto-translate all messages
- 👤 **Per-user language preference** — Each user sets their own default language
- 🗃️ **SQLite persistence** — Settings stored locally, survive restarts
- ⚡ **Async queue** — Rate-limit safe, non-blocking

---

## 🚀 Setup

### 1. Clone & install dependencies
```bash
git clone https://github.com/Ihsan-p1/Echokeeper.git
cd Echokeeper
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
```
Fill in `.env`:
```env
DISCORD_TOKEN=your_discord_bot_token
HF_API_TOKEN=your_huggingface_token   # free at huggingface.co/settings/tokens
DEFAULT_TARGET_LANG=en
```

### 3. Run
```bash
python bot.py
```

---

## 🎮 Commands

| Command | Description |
|---|---|
| `!tl <text>` | Translate to your default language |
| `!tl <lang> <text>` | Translate to a specific language |
| `/tl` | Slash command version |
| `/lang <code>` | Set your default language |
| `/optin` | Toggle auto-translate on/off |
| `/myinfo` | View your current settings |
| `/languages` | List all supported languages |
| `/setchannel <lang>` | *(Admin)* Enable auto-translate in this channel |
| `/removechannel` | *(Admin)* Disable auto-translate in this channel |
| React 🌐 | Translate any message to your default language |

---

## 🌍 Supported Languages

`en` `id` `vi` `ms` `zh` `ja` `ko` `ar` `fr` `de` `es` `pt` `ru` `hi`

---

## 📁 Project Structure

```
EchoKeeper/
├── bot.py              # Entry point
├── config.py           # Environment config
├── cogs/
│   ├── translate.py    # Translation commands & listeners
│   └── settings.py     # User preference commands
├── services/
│   ├── translator.py   # Helsinki-NLP API wrapper
│   ├── language_detect.py
│   └── queue.py        # Async rate-limit queue
├── database/
│   ├── db.py           # SQLite connection
│   └── models.py       # CRUD operations
└── utils/
    ├── embeds.py
    └── constants.py
```

---

## 📄 License

MIT
