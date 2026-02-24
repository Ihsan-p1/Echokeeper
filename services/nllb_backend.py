"""
NLLB-200 Local Translation Backend
====================================
Uses facebook/nllb-200-distilled-1.3B running locally via transformers.
Model is downloaded once (~5.2 GB) and cached in ~/.cache/huggingface/.

Key features:
- One model handles all 200 languages (no per-pair model needed)
- Runs on-device — no internet after first download
- GPU auto-detected (CUDA) for faster inference
- Context-aware: accepts previous sentences for better coherence
- Tuned generation params: beam search + length penalty + no_repeat
"""

import asyncio
import logging
import sys
import threading
from pathlib import Path
from config import NLLB_MODEL_ID, USE_FP16

log = logging.getLogger("nllb_backend")

MODEL_ID = NLLB_MODEL_ID

# Singleton cache — model loaded once, reused for all calls
_tokenizer = None
_model = None
_device = None
_load_lock = threading.Lock()


def _load_model():
    """Load NLLB-200 model + tokenizer (blocking — call via asyncio.to_thread)."""
    global _tokenizer, _model, _device

    with _load_lock:
        if _model is not None:
            return  # already loaded

        import torch
        import transformers

        _device = "cuda" if torch.cuda.is_available() else "cpu"
        dev_label = "GPU (CUDA)" if _device == "cuda" else "CPU"

        # Precision optimization
        if _device == "cuda" and USE_FP16:
            dtype = torch.float16
        else:
            dtype = torch.float32

        log.info(f"Loading NLLB-200 model ({dev_label}) ...")
        log.info(f"{MODEL_ID} [Precision: {dtype}]")
        
        # Using more direct access to avoid potential __init__ import issues
        _tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL_ID)
        _model = transformers.AutoModelForSeq2SeqLM.from_pretrained(
            MODEL_ID,
            dtype=dtype,
            low_cpu_mem_usage=True
        )
        _model.to(_device)
        _model.eval()

        log.info(f"Model loaded on {dev_label}")
        log.info(f"NLLB-200 1.3B ({dtype}) loaded on {_device}")


def _translate_sync(
    text: str,
    src_nllb: str,
    tgt_nllb: str,
    context: list[str] | None = None,
) -> str:
    """
    Synchronous translation — called via asyncio.to_thread().

    Args:
        text:      Text to translate.
        src_nllb:  NLLB BCP-47 source code, e.g. 'vie_Latn'
        tgt_nllb:  NLLB BCP-47 target code, e.g. 'eng_Latn'
        context:   Optional list of recent sentences (same source lang)
                   prepended to the input for better coherence.
    """
    import torch

    _load_model()

    # Build input with context (if provided)
    if context:
        # Prepend last 1–2 sentences as context (3 is too long for NLLB's 512 context when using 1.3B)
        ctx_str = ". ".join(context[-2:]) + ". "
        full_input = ctx_str + text
    else:
        full_input = text

    # Tokenize with source language
    _tokenizer.src_lang = src_nllb
    inputs = _tokenizer(
        full_input, return_tensors="pt", padding=True,
        truncation=True, max_length=512,
    ).to(_device)

    # Get target language token id for forced_bos
    tgt_lang_id = _tokenizer.convert_tokens_to_ids(tgt_nllb)

    with torch.no_grad():
        output_ids = _model.generate(
            **inputs,
            forced_bos_token_id=tgt_lang_id,
            max_new_tokens=256,
            num_beams=4,
            length_penalty=1.0,
            no_repeat_ngram_size=3,
            early_stopping=True,
        )

    result = _tokenizer.decode(output_ids[0], skip_special_tokens=True)

    # Context stripping logic
    if context:
        ctx_sentence_count = len(context[-2:])
        # Split into sentences (simple period-based)
        result_sentences = [s.strip() for s in result.split(".") if s.strip()]
        
        if len(result_sentences) > ctx_sentence_count:
            # Successfully generated new translation after context
            result = ". ".join(result_sentences[ctx_sentence_count:]).strip()
            if not result.endswith((".", "!", "?")):
                result += "."
        else:
            # Model got 'stuck' or absorbed the input into the context.
            # Fallback: Re-translate WITHOUT context for accuracy.
            log.warning("Context absorption detected, retrying without context.")
            return _translate_sync(text, src_nllb, tgt_nllb, context=None)

    log.debug(f"NLLB [{src_nllb}→{tgt_nllb}]: {text[:40]!r} → {result[:40]!r}")
    return result


async def translate(
    text: str,
    src_nllb: str,
    tgt_nllb: str,
    context: list[str] | None = None,
) -> str:
    """
    Async NLLB-200 translation.

    Args:
        text:      Text to translate.
        src_nllb:  NLLB BCP-47 source code, e.g. 'vie_Latn'
        tgt_nllb:  NLLB BCP-47 target code, e.g. 'eng_Latn'
        context:   Optional list of recent source-language sentences.

    Returns:
        Translated string.
    """
    if src_nllb == tgt_nllb:
        return text
    return await asyncio.to_thread(_translate_sync, text, src_nllb, tgt_nllb, context)


def is_loaded() -> bool:
    """Returns True if model is already in memory."""
    return _model is not None


def preload():
    """Preload model synchronously (call at startup to avoid first-translate delay)."""
    _load_model()
