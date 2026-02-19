import logging
from langdetect import detect, LangDetectException
from utils.constants import SUPPORTED_LANGUAGES

log = logging.getLogger("language_detect")

# Langdetect kadang salah deteksi teks pendek → fallback ke 'id'
FALLBACK_LANG = "id"


def detect_language(text: str) -> str:
    """
    Detect language from text.
    Returns ISO 639-1 language code yang ada di SUPPORTED_LANGUAGES.
    Falls back to FALLBACK_LANG jika tidak dikenal.
    """
    try:
        lang = detect(text)
        log.debug(f"Detected: {lang!r} for: {text[:50]!r}")

        # Pastikan hasilnya ada di daftar bahasa yang kita support
        if lang in SUPPORTED_LANGUAGES:
            return lang

        # Beberapa edge case: langdetect mengembalikan zh-cn, zh-tw → normalize
        if lang.startswith("zh"):
            return "zh"

        log.warning(f"Unsupported detected lang {lang!r}, falling back to {FALLBACK_LANG!r}")
        return FALLBACK_LANG

    except LangDetectException:
        log.warning(f"Detection failed for: {text[:50]!r}, falling back to {FALLBACK_LANG!r}")
        return FALLBACK_LANG
