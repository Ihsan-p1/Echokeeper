import os
from dotenv import load_dotenv

load_dotenv()

# ── Bot ──────────────────────────────────────────────
DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")

# ── HuggingFace ───────────────────────────────────────
HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")

# ── Translation Logic ─────────────────────────────────
ACTIVE_BACKEND: str = os.getenv("ECHOKEEPER_BACKEND", "nllb")
NLLB_MODEL_ID: str = os.getenv("NLLB_MODEL_ID", "facebook/nllb-200-distilled-1.3B")

# ── Translate defaults ────────────────────────────────
DEFAULT_TARGET_LANG: str = os.getenv("DEFAULT_TARGET_LANG", "en")

# ── Auto-translate channels (list of channel ID strings) ─
_raw_channels = os.getenv("AUTO_TRANSLATE_CHANNELS", "")
AUTO_TRANSLATE_CHANNELS: list[str] = (
    [c.strip() for c in _raw_channels.split(",") if c.strip()]
    if _raw_channels else []
)

# ── Tuning & Hardware ─────────────────────────────────
COOLDOWN_SECONDS: int = 3
QUEUE_SLEEP_SECONDS: float = 1.0
USE_FP16: bool = os.getenv("ECHOKEEPER_FP16", "true").lower() == "true"
