"""
EchoKeeper CLI - Terminal-based translator with Mode system

Usage:
    python cli.py                  # free mode (use !tl commands)
    python cli.py vi-en            # start in VI→EN mode
    python cli.py en-vi            # start in EN→VI mode
    python cli.py vi-id            # start in VI→ID mode
    python cli.py auto             # auto-detect source language

In any mode, just type text directly — no !tl needed!

Commands:
    !mode <src-tgt>    Switch translation mode  (e.g. !mode vi-en)
    !mode auto         Auto-detect source, still need !tl <lang>
    !mode off          Disable mode, back to manual !tl
    !tl <lang> <text>  Manual translate (always works)
    !langs             Show available language codes
    !slang <lang>      Show supported slang examples
    !help              Show this help
    !quit / !q         Exit
"""

import asyncio
import sys
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from services.translator import translate_text, TranslationError
from services.language_detect import detect_language
from services.slang_normalizer import normalize, post_process, SLANG_DICTS
from utils.constants import SUPPORTED_LANGUAGES, LANG_DISPLAY_NAME

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

# Active backend — set at startup, used for every translation
ACTIVE_BACKEND = "nllb"

# ── ANSI colors ───────────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
DIM     = "\033[2m"
MAGENTA = "\033[95m"
BLUE    = "\033[94m"


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_mode_arg(mode_str: str) -> tuple[str | None, str | None]:
    """
    Parse 'vi-en' → ('vi', 'en').
    Also accepts 'vi_en', 'vien', or language codes directly.
    Returns (None, None) if invalid, ('auto', None) if 'auto'.
    """
    if not mode_str:
        return None, None
    s = mode_str.lower().strip()
    if s in ("off", "none", "manual"):
        return None, None
    if s == "auto":
        return "auto", None

    # try separator  vi-en  vi→en  vi_en  vi>en
    for sep in ("-", "→", "_", ">", " "):
        if sep in s:
            parts = s.split(sep, 1)
            if len(parts) == 2:
                src, tgt = parts[0].strip(), parts[1].strip()
                if src in SUPPORTED_LANGUAGES and tgt in SUPPORTED_LANGUAGES:
                    return src, tgt

    # Try 4-char concat like "vien"
    if len(s) == 4:
        src, tgt = s[:2], s[2:]
        if src in SUPPORTED_LANGUAGES and tgt in SUPPORTED_LANGUAGES:
            return src, tgt

    # Try 5-char like "vi-en" already handled above
    return None, None


def mode_label(src: str | None, tgt: str | None) -> str:
    if src is None:
        return f"{DIM}no mode{RESET}"
    if src == "auto":
        return f"{MAGENTA}auto → {tgt}{RESET}" if tgt else f"{MAGENTA}auto-detect{RESET}"
    src_name = LANG_DISPLAY_NAME.get(src, src.upper())
    tgt_name = LANG_DISPLAY_NAME.get(tgt, tgt.upper()) if tgt else "?"
    return f"{MAGENTA}{src_name} → {tgt_name}{RESET}"


def prompt_str(src: str | None, tgt: str | None) -> str:
    if src is None:
        return f"{CYAN}>{RESET} "
    arrow = f"{src}→{tgt}" if tgt else f"auto→?"
    return f"{CYAN}[{MAGENTA}{arrow}{CYAN}]{CYAN}>{RESET} "


# ── Banner ────────────────────────────────────────────────────────────────────

def print_banner(src: str | None, tgt: str | None, backend: str = "nllb"):
    mode_str = mode_label(src, tgt)
    model_str = (
        f"NLLB-200 distilled 600M {DIM}(local){RESET}"
        if backend == "nllb"
        else f"Helsinki-NLP OPUS-MT {DIM}(cloud API){RESET}"
    )
    print(f"""
{CYAN}{BOLD}╔══════════════════════════════════════════╗
║    🌐  EchoKeeper Translator CLI       ║
║    VI · ID · EN slang supported        ║
╚══════════════════════════════════════════╝{RESET}

  Mode  : {mode_str}
  Model : {model_str}

{DIM}In mode  — just {RESET}{BOLD}type your text{RESET}{DIM} and press Enter
Manual — {RESET}{BOLD}!tl <lang> <text>{RESET}{DIM} (always works){RESET}

{DIM}  !mode vi-en    switch to VI→EN mode
  !mode en-vi    switch to EN→VI mode
  !mode off      disable mode (manual only)
  !langs         show language codes
  !slang <lang>  show slang examples
  !help          show this banner
  !quit          exit{RESET}
""")


# ── Per-result output ─────────────────────────────────────────────────────────

def print_result(
    original: str,
    normalized: str,
    translated: str,
    src_lang: str,
    tgt_lang: str,
    replacements: list[str],
):
    src_name = LANG_DISPLAY_NAME.get(src_lang, src_lang)
    tgt_name = LANG_DISPLAY_NAME.get(tgt_lang, tgt_lang)

    print(f"\n{DIM}{'─' * 45}{RESET}")
    print(f"  {DIM}Source   : {src_name} ({src_lang}){RESET}")
    print(f"  {DIM}Target   : {tgt_name} ({tgt_lang}){RESET}")

    if replacements:
        print(f"\n{YELLOW}  ✦ Slang detected & normalized:{RESET}")
        for r in replacements:
            print(f"    {DIM}{r}{RESET}")
        print(f"  {DIM}Normalized: {normalized}{RESET}")

    print(f"\n{GREEN}{BOLD}  Translation:{RESET}")
    print(f"  {BOLD}{translated}{RESET}")
    print(f"{DIM}{'─' * 45}{RESET}\n")


# ── Core translate logic ──────────────────────────────────────────────────────

async def do_translate(text: str, src_lang: str, tgt_lang: str, context: list[str] | None = None):
    """Normalize, translate, post-process and print."""
    if src_lang == tgt_lang:
        print(f"{YELLOW}  Source and target are both '{tgt_lang}'. Nothing to translate.{RESET}\n")
        return

    normalized, replacements = normalize(text, src_lang)
    print(f"{DIM}  {src_lang} → {tgt_lang} [{ACTIVE_BACKEND}] …{RESET}", end="\r")

    try:
        raw = await translate_text(
            text=normalized, target=tgt_lang, source=src_lang,
            backend=ACTIVE_BACKEND, context=context
        )
        translated = post_process(raw)
        print_result(text, normalized, translated, src_lang, tgt_lang, replacements)
        return text  # Return original text to be added to history
    except TranslationError as e:
        print(f"\n{RED}Translation error: {e}{RESET}\n")
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}\n")
    return None


# ── Command handlers ──────────────────────────────────────────────────────────

async def handle_tl_command(parts: list[str]):
    """Handle explicit  !tl <lang> <text>"""
    if len(parts) < 3:
        print(f"{RED}Usage: !tl <target_lang> <text>{RESET}")
        print(f"Example: {DIM}!tl en mày đi đâu vậy vcl{RESET}\n")
        return
    tgt_lang = parts[1].lower().strip()
    if tgt_lang not in SUPPORTED_LANGUAGES:
        print(f"{RED}Unknown language code: '{tgt_lang}'{RESET}")
        print(f"Run {BOLD}!langs{RESET} to see available codes.\n")
        return
    text = " ".join(parts[2:]).strip()
    if not text:
        print(f"{RED}Please provide text to translate.{RESET}\n")
        return
    src_lang = detect_language(text)
    await do_translate(text, src_lang, tgt_lang)


def handle_langs():
    print(f"\n{BOLD}Available language codes:{RESET}")
    for code in SUPPORTED_LANGUAGES:
        name = LANG_DISPLAY_NAME.get(code, code)
        print(f"  {CYAN}{code:4}{RESET} → {name}")
    print()


def handle_slang(parts: list[str]):
    lang = parts[1].lower() if len(parts) > 1 else "vi"
    if lang not in SLANG_DICTS:
        print(f"{RED}No slang dict for '{lang}'. Available: {', '.join(SLANG_DICTS)}{RESET}\n")
        return
    lang_name = LANG_DISPLAY_NAME.get(lang, lang)
    slang_dict = SLANG_DICTS[lang]
    print(f"\n{BOLD}[{lang_name}] Slang dictionary ({len(slang_dict)} entries):{RESET}")
    for slang, formal in list(slang_dict.items())[:15]:
        print(f"  {YELLOW}{slang:20}{RESET} → {formal}")
    if len(slang_dict) > 15:
        print(f"  {DIM}... and {len(slang_dict) - 15} more{RESET}")
    print()


async def repl(init_src: str | None, init_tgt: str | None):
    src_mode = init_src  # current source lang (or 'auto' or None)
    tgt_mode = init_tgt  # current target lang (or None)
    history: list[str] = []  # Rolling history for context

    print_banner(src_mode, tgt_mode, backend=ACTIVE_BACKEND)

    # Preload NLLB model in background — so first translation is instant
    if ACTIVE_BACKEND == "nllb":
        from services.nllb_backend import preload as _nllb_preload, is_loaded as _nllb_loaded
        if not _nllb_loaded():
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, _nllb_preload)

    while True:
        try:
            raw = input(prompt_str(src_mode, tgt_mode)).strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}Goodbye! 👋{RESET}\n")
            break

        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0].lower()

        # ── Exit ──────────────────────────────────────────────────────────────
        if cmd in ("!quit", "!exit", "!q"):
            print(f"\n{DIM}Goodbye! 👋{RESET}\n")
            break

        # ── Mode switch ───────────────────────────────────────────────────────
        elif cmd == "!mode":
            arg = " ".join(parts[1:]) if len(parts) > 1 else ""
            new_src, new_tgt = parse_mode_arg(arg)

            if arg and (new_src is None) and arg.lower() not in ("off", "none", "manual"):
                print(f"{RED}Unknown mode: '{arg}'{RESET}")
                print(f"  Examples: {DIM}!mode vi-en  !mode en-vi  !mode auto  !mode off{RESET}\n")
            else:
                src_mode, tgt_mode = new_src, new_tgt
                if src_mode is None:
                    print(f"  {DIM}Mode disabled — use !tl <lang> <text>{RESET}\n")
                else:
                    print(f"  Mode → {mode_label(src_mode, tgt_mode)}  [{ACTIVE_BACKEND}]\n")
                history.clear()  # Reset context on mode change
        
        elif cmd == "!clear":
            history.clear()
            print(f"  {DIM}Conversation context cleared.{RESET}\n")

        # ── Help / misc ───────────────────────────────────────────────────────
        elif cmd == "!help":
            print_banner(src_mode, tgt_mode)

        elif cmd == "!langs":
            handle_langs()

        elif cmd == "!slang":
            handle_slang(parts)

        # ── Manual translate ──────────────────────────────────────────────────
        elif cmd == "!tl":
            await handle_tl_command(parts)

        elif cmd.startswith("!"):
            print(f"{DIM}Unknown command: {raw!r}{RESET}")
            print(f"Try {BOLD}!help{RESET} for available commands.\n")

        # ── MODE: auto-translate anything that's not a command ────────────────
        else:
            if src_mode is None:
                # No mode set — hint the user
                print(f"{DIM}No mode active. Set one with {RESET}{BOLD}!mode vi-en{RESET}"
                      f"{DIM} or use {RESET}{BOLD}!tl <lang> <text>{RESET}\n")
                continue

            # Determine source language
            if src_mode == "auto":
                src_lang = detect_language(raw)
                # In auto mode, tgt_mode must be set (else we can't translate)
                if tgt_mode is None:
                    print(f"{DIM}Auto mode needs a target. Use {RESET}{BOLD}!mode auto-en{RESET}"
                          f"{DIM} for example.{RESET}\n")
                    continue
                actual_tgt = tgt_mode
            else:
                src_lang = src_mode
                actual_tgt = tgt_mode  # guaranteed not None

            # Pass history as context
            sent = await do_translate(raw, src_lang, actual_tgt, context=history)
            if sent:
                history.append(sent)
                if len(history) > 3:
                    history.pop(0)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    global ACTIVE_BACKEND

    parser = argparse.ArgumentParser(
        description="EchoKeeper Translator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py                        # manual mode, NLLB-200 (local)
  python cli.py vi-en                  # VI→EN mode, NLLB-200 (local)
  python cli.py en-vi --backend opus   # EN→VI mode, OPUS-MT (cloud)
  python cli.py auto-en                # auto-detect → EN
""",
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default=None,
        help="Translation mode: vi-en, en-vi, auto-en, etc.",
    )
    parser.add_argument(
        "--backend",
        choices=["nllb", "opus"],
        default="nllb",
        help="Translation backend: nllb (local, default) or opus (cloud HF API)",
    )
    args = parser.parse_args()

    ACTIVE_BACKEND = args.backend

    src, tgt = parse_mode_arg(args.mode) if args.mode else (None, None)

    if args.mode and src is None and args.mode.lower() not in ("off", "none"):
        print(f"{RED}Invalid mode '{args.mode}'. Use vi-en, en-vi, auto-en, etc.{RESET}")
        sys.exit(1)

    asyncio.run(repl(src, tgt))


if __name__ == "__main__":
    main()
