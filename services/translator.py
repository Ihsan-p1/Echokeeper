"""
EchoKeeper Translator — multi-backend
======================================
Supports two backends selectable via the `backend` parameter:

  "nllb"  — facebook/nllb-200-distilled-600M running locally (default)
             Better quality, offline after first ~2.4 GB download.

  "opus"  — Helsinki-NLP opus-mt via HuggingFace Inference API (cloud)
             Faster cold start, needs internet & HF API token.

Usage:
    translated = await translate_text("mày đi đâu", target="en", source="vi")
    translated = await translate_text(text, target="en", source="vi", backend="opus")
"""

import logging
import os
from huggingface_hub import AsyncInferenceClient
from config import HF_API_TOKEN, ACTIVE_BACKEND
from utils.constants import SUPPORTED_LANGUAGES

log = logging.getLogger("translator")

# Default backend — centralized in config
DEFAULT_BACKEND = ACTIVE_BACKEND


class TranslationError(Exception):
    pass


# ── OPUS-MT model map (cloud backend) ────────────────────────────────────────

OPUS_MODELS: dict[tuple[str, str], str] = {
    ("vi", "en"): "Helsinki-NLP/opus-mt-vi-en",
    ("en", "vi"): "Helsinki-NLP/opus-mt-en-vi",
    ("id", "en"): "Helsinki-NLP/opus-mt-id-en",
    ("en", "id"): "Helsinki-NLP/opus-mt-en-id",
    ("ms", "en"): "Helsinki-NLP/opus-mt-ms-en",
    ("en", "ms"): "Helsinki-NLP/opus-mt-en-ms",
    ("zh", "en"): "Helsinki-NLP/opus-mt-zh-en",
    ("en", "zh"): "Helsinki-NLP/opus-mt-en-zh",
    ("ja", "en"): "Helsinki-NLP/opus-mt-ja-en",
    ("en", "ja"): "Helsinki-NLP/opus-mt-en-jap",
    ("ko", "en"): "Helsinki-NLP/opus-mt-ko-en",
    ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
    ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
    ("de", "en"): "Helsinki-NLP/opus-mt-de-en",
    ("en", "de"): "Helsinki-NLP/opus-mt-en-de",
    ("es", "en"): "Helsinki-NLP/opus-mt-es-en",
    ("en", "es"): "Helsinki-NLP/opus-mt-en-es",
    ("ru", "en"): "Helsinki-NLP/opus-mt-ru-en",
    ("en", "ru"): "Helsinki-NLP/opus-mt-en-ru",
    ("ar", "en"): "Helsinki-NLP/opus-mt-ar-en",
    ("hi", "en"): "Helsinki-NLP/opus-mt-hi-en",
    ("en", "hi"): "Helsinki-NLP/opus-mt-en-hi",
}


def _get_opus_client() -> AsyncInferenceClient:
    return AsyncInferenceClient(provider="hf-inference", api_key=HF_API_TOKEN)


async def _opus_translate_single(text: str, src: str, tgt: str) -> str:
    """Single-hop OPUS-MT translation via HF API."""
    model = OPUS_MODELS.get((src, tgt))
    if not model:
        raise TranslationError(
            f"No OPUS-MT model for `{src}` → `{tgt}`. Try backend='nllb'."
        )
    log.debug(f"OPUS [{src}→{tgt}] model={model}")
    client = _get_opus_client()
    result = await client.translation(text, model=model)

    if hasattr(result, "translation_text"):
        return result.translation_text
    if isinstance(result, list) and result:
        item = result[0]
        return item.get("translation_text", str(item)) if isinstance(item, dict) else str(item)
    return str(result)


async def _translate_opus(text: str, source: str, target: str) -> str:
    """OPUS-MT backend: direct or bridge-via-EN."""
    if (source, target) in OPUS_MODELS:
        return await _opus_translate_single(text, source, target)

    # Bridge via English
    if source != "en" and target != "en":
        log.info(f"OPUS: no direct {source}→{target}, bridging via EN")
        en_text = await _opus_translate_single(text, source, "en")
        return await _opus_translate_single(en_text, "en", target)

    raise TranslationError(f"No OPUS model for `{source}` → `{target}`.")


# ── NLLB-200 local backend ────────────────────────────────────────────────────

async def _translate_nllb(
    text: str, source: str, target: str,
    context: list[str] | None = None,
) -> str:
    """NLLB-200 local backend — supports all 200 languages natively."""
    from services.nllb_backend import translate as nllb_translate

    src_nllb = SUPPORTED_LANGUAGES.get(source)
    tgt_nllb = SUPPORTED_LANGUAGES.get(target)

    if not src_nllb:
        raise TranslationError(f"Language '{source}' not in SUPPORTED_LANGUAGES.")
    if not tgt_nllb:
        raise TranslationError(f"Language '{target}' not in SUPPORTED_LANGUAGES.")

    try:
        return await nllb_translate(text, src_nllb, tgt_nllb, context=context)
    except Exception as e:
        raise TranslationError(f"NLLB-200 error: {e}") from e


# ── Public API ────────────────────────────────────────────────────────────────

async def translate_text(
    text: str,
    target: str = "en",
    source: str = "id",
    backend: str | None = None,
    context: list[str] | None = None,
) -> str:
    """
    Translate text using the chosen backend.

    Args:
        text:    Text to translate.
        target:  ISO 639-1 target language code (e.g. 'en', 'vi').
        source:  ISO 639-1 source language code.
        backend: 'nllb' (local, default) or 'opus' (cloud HF API).
                 If None, uses DEFAULT_BACKEND / ECHOKEEPER_BACKEND env var.
        context: Optional list of recent source-language sentences for
                 context-aware translation (NLLB only).

    Returns:
        Translated string.

    Raises:
        TranslationError on any failure.
    """
    if source == target:
        return text

    chosen = (backend or DEFAULT_BACKEND).lower()
    log.debug(f"translate_text [{source}→{target}] backend={chosen}: {text[:60]!r}")

    if chosen == "nllb":
        return await _translate_nllb(text, source, target, context=context)
    elif chosen == "opus":
        return await _translate_opus(text, source, target)
    else:
        raise TranslationError(f"Unknown backend '{chosen}'. Use 'nllb' or 'opus'.")
