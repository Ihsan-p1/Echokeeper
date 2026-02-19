import os
from dotenv import load_dotenv

load_dotenv()

# ── Bot ──────────────────────────────────────────────
DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")

# ── HuggingFace ───────────────────────────────────────
HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")

# ── Translate defaults ────────────────────────────────
DEFAULT_TARGET_LANG: str = os.getenv("DEFAULT_TARGET_LANG", "en")

# ── Auto-translate channels (list of channel ID strings) ─
_raw_channels = os.getenv("AUTO_TRANSLATE_CHANNELS", "")
AUTO_TRANSLATE_CHANNELS: list[str] = (
    [c.strip() for c in _raw_channels.split(",") if c.strip()]
    if _raw_channels else []
)

# ── Rate-limit ────────────────────────────────────────
COOLDOWN_SECONDS: int = 3
QUEUE_SLEEP_SECONDS: float = 1.0
