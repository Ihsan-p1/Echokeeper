import aiohttp
import logging
from huggingface_hub import AsyncInferenceClient
from config import HF_API_TOKEN

log = logging.getLogger("translator")


class TranslationError(Exception):
    pass


# ── Helsinki-NLP opus-mt model mapping ────────────────────────────────────────
# Format: (src, tgt) → model_id
# Kalau tidak ada direct model → route lewat bahasa perantara (bridge via EN)

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


def _get_client() -> AsyncInferenceClient:
    return AsyncInferenceClient(
        provider="hf-inference",
        api_key=HF_API_TOKEN,
    )


async def _translate_single(text: str, src: str, tgt: str) -> str:
    """Single hop translation menggunakan opus-mt model."""
    model = OPUS_MODELS.get((src, tgt))
    if not model:
        raise TranslationError(
            f"Tidak ada model langsung untuk `{src}` → `{tgt}`. "
            f"Coba route lewat English."
        )

    log.debug(f"Using model {model} for [{src}→{tgt}]")
    client = _get_client()
    result = await client.translation(text, model=model)

    if hasattr(result, "translation_text"):
        return result.translation_text
    if isinstance(result, list) and result:
        item = result[0]
        return item.get("translation_text", str(item)) if isinstance(item, dict) else str(item)
    return str(result)


async def translate_text(
    text: str,
    target: str = "en",
    source: str = "id",
) -> str:
    """
    Translate teks menggunakan Helsinki-NLP opus-mt models.
    Kalau tidak ada direct model, otomatis bridge lewat English.

    Args:
        text:   Teks yang diterjemahkan.
        target: Kode bahasa tujuan (en, id, vi, dst.)
        source: Kode bahasa sumber.
    """
    if source == target:
        return text

    log.debug(f"Translate request: [{source} → {target}] {text[:60]!r}")

    # Coba direct translation dulu
    if (source, target) in OPUS_MODELS:
        try:
            return await _translate_single(text, source, target)
        except Exception as e:
            raise TranslationError(str(e))

    # Fallback: bridge via English (src→en→tgt)
    if source != "en" and target != "en":
        log.info(f"No direct model for {source}→{target}, bridging via EN")
        try:
            en_text = await _translate_single(text, source, "en")
            return await _translate_single(en_text, "en", target)
        except TranslationError:
            raise
        except Exception as e:
            raise TranslationError(f"Bridge translation gagal: {e}")

    raise TranslationError(
        f"Tidak ada model tersedia untuk `{source}` → `{target}`."
    )
