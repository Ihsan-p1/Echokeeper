# NLLB-200 BCP-47 language codes
# Referensi: https://github.com/facebookresearch/flores/blob/main/flores200/README.md

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en":  "eng_Latn",   # English
    "id":  "ind_Latn",   # Indonesian
    "vi":  "vie_Latn",   # Vietnamese
    "ms":  "zsm_Latn",   # Malay
    "zh":  "zho_Hans",   # Chinese (Simplified)
    "ja":  "jpn_Jpan",   # Japanese
    "ko":  "kor_Hang",   # Korean
    "ar":  "arb_Arab",   # Arabic
    "fr":  "fra_Latn",   # French
    "de":  "deu_Latn",   # German
    "es":  "spa_Latn",   # Spanish
    "pt":  "por_Latn",   # Portuguese
    "ru":  "rus_Cyrl",   # Russian
    "th":  "tha_Thai",   # Thai
    "hi":  "hin_Deva",   # Hindi
}

LANG_DISPLAY_NAME: dict[str, str] = {
    "en": "English",
    "id": "Indonesian",
    "vi": "Vietnamese",
    "ms": "Malay",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "pt": "Portuguese",
    "ru": "Russian",
    "th": "Thai",
    "hi": "Hindi",
}

# Emoji reaction yang memicu translate
TRANSLATE_REACTION = "🌐"

# Panjang max teks yang diterjemahkan
MAX_TEXT_LENGTH = 1000
