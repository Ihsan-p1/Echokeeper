# EchoKeeper: local translation bot for Discord

EchoKeeper translates Discord messages on your own hardware. It runs NLLB-200 locally, so
after the first model download nothing leaves the machine: no Google Translate, no DeepL,
no API key. The same engine is reachable from a terminal CLI.

Slang is handled before the model sees it. Vietnamese and Indonesian chat text is
normalised to formal spellings first, because NLLB is trained on formal corpora and
mistranslates informal registers.

## Features

- Prefix and slash commands, a 🌐 reaction trigger, and per-channel auto-translation.
- Two runtimes for the same model: CTranslate2 when a converted model directory is
  present, Transformers with PyTorch otherwise. The fallback is automatic.
- Slang dictionaries with 257 Vietnamese, 103 Indonesian, and 105 English entries, applied
  before translation and cleaned up after.
- Per-user target language and per-channel target language, stored in SQLite.
- One translation at a time through an internal queue, with a 3-second per-user cooldown.

## Commands

| Command | What it does |
|---|---|
| `!tl <text>` | Translate to your target language |
| `!tl <lang> <text>` | Translate to a specific language code |
| `/tl` | Same as `!tl`, as a slash command |
| `/lang <code>` | Set your personal target language |
| `/optin` | Opt in to being auto-translated |
| `/myinfo` | Show your current settings |
| `/setchannel <lang>` | Auto-translate this channel into `lang`. Needs Manage Channels. |
| `/removechannel` | Stop auto-translating this channel |
| `/languages` | List the supported language codes |

React 🌐 to any message to get it translated into your own target language.

In an auto-translate channel, every message is detected and translated unless it is
already in the channel's target language.

## Languages

NLLB-200 covers 200 languages. EchoKeeper exposes 15 of them by short code, mapped to
NLLB's BCP-47 codes in `utils/constants.py`:

`en`, `id`, `vi`, `ms`, `zh`, `ja`, `ko`, `ar`, `fr`, `de`, `es`, `pt`, `ru`, `th`, `hi`

Source language is detected with `langdetect`, which is unreliable on very short strings,
so it falls back to Indonesian. Messages longer than 1000 characters are rejected.

## Requirements

- Python 3.10 or newer (the code uses `str | None` annotations)
- About 6 GB of VRAM for the 1.3B model in FP16, or about 3 GB for the 600M variant.
  CPU works and is slower.
- A Discord bot token, with the Message Content intent enabled for prefix commands

The first run downloads roughly 5.2 GB of model weights into `~/.cache/huggingface/`.

## Install

```bash
git clone https://github.com/Ihsan-p1/Echokeeper.git
cd Echokeeper

python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux, macOS

pip install -r requirements.txt
cp .env.example .env
```

Then put your token in `.env`.

## Configuration

Everything is read from `.env` through `config.py`:

| Variable | Default | Meaning |
|---|---|---|
| `DISCORD_TOKEN` | required | Bot token |
| `ECHOKEEPER_BACKEND` | `nllb` | Translation engine |
| `NLLB_MODEL_ID` | `facebook/nllb-200-distilled-1.3B` | HuggingFace model id |
| `ECHOKEEPER_FP16` | `true` | Half precision on GPU |
| `DEFAULT_TARGET_LANG` | `en` | Target language before a user sets their own |
| `AUTO_TRANSLATE_CHANNELS` | empty | Comma-separated channel IDs translated on startup |
| `NLLB_CT2_MODEL_DIR` | `models/nllb-ct2-int8` | CTranslate2 model directory |
| `NLLB_TOKENIZER_ID` | same as `NLLB_MODEL_ID` | Tokenizer for the CT2 path |
| `NLLB_CT2_DEVICE` | `cuda` | Device for CTranslate2 |
| `NLLB_CT2_COMPUTE_TYPE` | `int8_float16` | Quantisation for CTranslate2 |

## CTranslate2 for faster inference

CTranslate2 runs the same model with less VRAM and lower latency. Convert the weights
once:

```bash
pip install ctranslate2 sentencepiece

ct2-transformers-converter \
  --model facebook/nllb-200-distilled-1.3B \
  --output_dir models/nllb-ct2-int8 \
  --quantization int8_float16
```

Then point `.env` at the output directory:

```bash
NLLB_CT2_MODEL_DIR=models/nllb-ct2-int8
NLLB_TOKENIZER_ID=facebook/nllb-200-distilled-1.3B
NLLB_CT2_DEVICE=cuda
NLLB_CT2_COMPUTE_TYPE=int8_float16
```

If that directory is missing or fails to load, EchoKeeper logs it and uses the Transformers
backend instead.

## Running

The Discord bot:

```bash
python bot.py
```

The CLI, which shares the translation service and the slang normaliser:

```bash
python cli.py              # free mode, use !tl commands
python cli.py vi-en        # Vietnamese to English, type text directly
python cli.py en-vi
python cli.py vi-id
python cli.py auto         # detect the source language per line
```

## Project structure

```
EchoKeeper/
├── bot.py                        # Discord entrypoint, loads the cogs
├── cli.py                        # Terminal translator with modes
├── config.py                     # Environment configuration
├── cogs/
│   ├── translate.py              # !tl, /tl, 🌐 reaction, auto-translate listener
│   └── settings.py               # /lang, /optin, /myinfo, /setchannel, /removechannel, /languages
├── services/
│   ├── translator.py             # Backend dispatch
│   ├── nllb_backend.py           # NLLB via CTranslate2 or Transformers
│   ├── slang_normalizer.py       # VI/ID/EN slang dictionaries, pre and post processing
│   ├── language_detect.py        # langdetect wrapper with an Indonesian fallback
│   └── queue.py                  # Serialises translation requests
├── database/
│   ├── db.py                     # aiosqlite connection
│   └── models.py                 # User and channel settings
├── utils/
│   ├── constants.py              # Language codes, reaction emoji, length limit
│   └── embeds.py                 # Response formatting
├── scripts/finetune_nllb.py      # Fine-tuning scaffold
└── data/slang_parallel.jsonl     # 10 parallel slang examples for that scaffold
```

## Fine-tuning

`scripts/finetune_nllb.py` is a scaffold, not a trained pipeline.
`data/slang_parallel.jsonl` holds 10 examples, which is enough to check that the script
runs and nowhere near enough to specialise the model. Bring your own parallel data before
expecting a quality change.
