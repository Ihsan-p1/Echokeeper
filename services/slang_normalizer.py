"""
Slang Normalizer - Pre-processes slang before sending to translation model.
Prioritized: Vietnamese > Indonesian > English

Strategy: Replace slang tokens with formal equivalents so Helsinki-NLP
opus-mt models (trained on formal corpora) can translate them accurately.
"""

import re
import logging
from typing import Optional

log = logging.getLogger("slang_normalizer")

# ─────────────────────────────────────────────────────────────────────────────
# Vietnamese Slang Dictionary (PRIORITY)
# Common internet slang, typos, abbreviations used by Vietnamese youth
# ─────────────────────────────────────────────────────────────────────────────
VI_SLANG: dict[str, str] = {
    # Profanity / expressions (normalized to non-offensive equivalents)
    "vcl": "trời ơi",         # very common exclamation → "oh god"
    "vl": "trời ơi",
    "vkl": "trời ơi",         # variant of vcl
    "vcđ": "trời ơi",         # variant
    "wtf": "cái gì vậy",
    "dm": "ôi trời",          # common expression
    "đm": "ôi trời",
    "đcm": "thật sự",         # profanity as intensifier → "really/damn"
    "đkm": "thật sự",         # variant
    "dcm": "thật sự",         # non-diacritic variant
    "tml": "im miệng đi",     # "shut up"
    "địt mẹ": "ôi trời",
    "cmnr": "hoàn toàn rồi",  # "completely already"
    "cl": "trời ơi",
    "clm": "trời ơi",
    "cc": "ôi trời",
    "clgt": "cái gì thế",     # "what is this"

    # 'mẹ' as intensifier (NOT "mother") — very common informal usage
    "quên mẹ": "quên hoàn toàn",     # "completely forgot"
    "chán mẹ": "chán hoàn toàn",     # "completely bored"
    "mệt mẹ": "mệt hoàn toàn",      # "completely tired"
    "sợ mẹ": "sợ hoàn toàn",         # "completely scared"

    # 'vl' as intensifier suffix — "adjective + vl" = "very adjective"
    "chán vl": "rất chán",
    "đẹp vl": "rất đẹp",
    "giỏi vl": "rất giỏi",
    "nhanh vl": "rất nhanh",
    "buồn vl": "rất buồn",
    "sợ vl": "rất sợ",
    "thì vl": "rất",            # common bridge for intensifiers
    "ghét vl": "rất ghét",

    # Affirmations / agreements
    "oke": "được rồi",
    "ok": "được rồi",
    "oce": "được rồi",
    "đc": "được",
    "dc": "được",
    "vâng ạ": "vâng",
    "nhé": "nhé",            # keep as-is (already formal enough)
    "nha": "nhé",
    "na": "nhé",

    # Common abbreviations
    "mk": "mình",            # "I/me" informal
    "mik": "mình",
    "tao": "tôi",            # "I" (rude) → formal
    "mày": "bạn",            # "you" (rude) → formal
    "m": "mình",
    "t": "tôi",
    "mn": "mọi người",       # "everyone"
    "mng": "mọi người",
    "ng": "người",           # "person"
    "bt": "bình thường",     # "normal"
    "bth": "bình thường",
    "bthg": "bình thường",   # variant
    "cx": "cũng",            # "also"
    "cg": "cũng",
    "ck": "cũng",            # variant
    "ns": "nói",             # "say"
    "ntn": "như thế nào",    # "how"
    "nttn": "như thế thì nào",
    "đk": "được không",      # "can I / is it okay"
    "kb": "kết bạn",         # "add friend"
    "ib": "nhắn tin",        # "inbox/message me"
    "ht": "hết",             # "done/finished"
    "thui": "thôi",          # "okay/stop"
    "thoy": "thôi",
    "r": "rồi",              # "already/then"
    "rùi": "rồi",
    "rồi á": "rồi",          # emphatic "already!"
    "lm": "làm",             # "do/make"
    "đag": "đang",           # "currently"
    "dag": "đang",
    "bh": "bây giờ",         # "now"
    "h": "giờ",              # "now" (single char)
    "trc": "trước",          # "before"
    "sau đó": "sau đó",      # keep as-is
    "vs": "với",             # "with"
    "vd": "ví dụ",           # "for example"
    "đng": "đừng",           # "don't"
    "dung": "đừng",
    "gì đó": "một thứ gì đó",
    "j": "gì",               # "what/something"
    "j đó": "gì đó",
    "j v": "gì vậy",
    "v": "vậy",              # "so/like that"
    "vay": "vậy",
    "sao v": "sao vậy",
    "no": "nó",              # "it/he/she"
    "pro": "giỏi",           # "skilled/pro"
    "newbie": "người mới",
    "noob": "người mới chơi",

    # Emotions / reactions
    "haha": "haha",          # keep
    "hihi": "hehe",
    "hehe": "hehe",
    "kk": "haha",
    "kkk": "haha",
    "uh": "ừ",               # "yeah"
    "ừa": "ừ",
    "uhm": "ừm",
    "hmm": "ừm",
    "haizz": "thở dài",      # sigh
    "haizzz": "thở dài",
    "hic": "buồn quá",       # sad expression
    "huhu": "buồn quá",      # crying
    "T_T": "buồn quá",
    "buồn v": "rất buồn",    # "so sad"
    "vui v": "rất vui",
    "cute v": "rất dễ thương",
    "đẹp v": "rất đẹp",

    # Internet / social media slang
    "lol": "buồn cười",      # "funny/lol"
    "bff": "bạn thân nhất",  # "best friend forever"
    "bestie": "bạn thân",
    "crush": "người thích",
    "date": "hẹn hò",
    "ship": "ghép đôi",
    "oot": "không liên quan", # "out of topic"
    "spam": "nhắn tin liên tục",
    "flex": "khoe khoang",
    "sus": "đáng ngờ",
    "vibe": "cảm giác",
    "mood": "tâm trạng",
    "slay": "tuyệt vời",

    # Time / urgency
    "asap": "sớm nhất có thể",
    "nvm": "thôi không cần",  # "never mind"
    "omw": "đang trên đường đến",

    # Questions
    "sao v": "tại sao vậy",
    "kh": "không",           # "no/not"
    "ko": "không",
    "k": "không",
    "khum": "không",
    "hem": "không",          # southern dialect
    "hok": "không",

    # Multi-word phrases & connectors (order matters — longer first)
    "được cả": "thậm chí",   # 'even' (context: 'even X is bad')
    "ngay cả": "thậm chí",   # same meaning
    "có vẻ": "có vẻ như",    # 'seems like'
    "hơi bị": "rất",         # 'quite/very' (intensifier slang)
    "kiểu gì": "theo cách nào",
    "kiểu": "theo kiểu",      # 'like / in the style of'
    "đúng không": "phải không",  # 'right?'
    "thật ra": "thực ra",    # 'actually'
    "tất nhiên rồi": "tất nhiên",

    # Gaming slang — VI-specific only
    # NOTE: English loanwords (lag, op, meta, buff, nerf, afk, gank, troll, etc.)
    # are intentionally NOT normalized here. The VI→EN model recognises these
    # loanwords better in their original form than as Vietnamese expansions.
    # E.g. keeping 'lag' lets the model output 'lag'; replacing with 'chậm mạng'
    # causes it to say 'slow' instead.
    "ngu build": "bộ trang bị kém",   # no English equivalent
    "build ngu": "bộ trang bị kém",
    "ngu": "dốt",                      # 'stupid'

    # ── EVERYDAY VIETNAMESE SLANG - EXPANDED ─────────────────────────────────

    # Texting shortcuts & phonetic spellings
    "hok bik": "không biết",
    "ờ mây gót": "ôi trời ơi",      # phonetic "oh my god"
    "gét gâu": "bắt đầu thôi",       # phonetic "let's go"
    "gét gô": "bắt đầu thôi",
    "ui chời": "ôi trời",             # southern "oh lord"
    "chời ơi": "trời ơi",             # southern "oh god"
    "ủa sao": "sao vậy",
    "hen gặp": "hẹn gặp",
    "hok": "không",
    "pls": "làm ơn",
    "plz": "làm ơn",
    "tyvm": "cảm ơn rất nhiều",
    "tth": "thật hả",
    "hok bik": "không biết",
    "rep": "trả lời",
    "seen": "đã xem",
    "nt": "nói thật",
    "z": "vậy",
    "zậy": "vậy",
    "dzậy": "vậy",
    "ik": "biết",
    "bik": "biết",
    "ui": "ôi",
    "úi": "ôi",
    "ủa": "à",
    "ha": "hả",
    "nè": "này",
    "lắk": "lắm",
    "okê": "được rồi",
    "chời": "trời",

    # Intensifiers (tagged — normalize() caps max 2 per sentence from this group)
    "đỉnh của chóp": "xuất sắc nhất",  # best of best
    "vãi cả người": "thật bất ngờ",
    "vãi chưởng": "thật bất ngờ",
    "ảo vãi": "tuyệt vời thật",
    "chất lừ": "rất hay",
    "bá đạo": "cực kỳ giỏi",
    "thần thánh": "xuất sắc",
    "quá trời": "rất nhiều",
    "dữ vậy": "cực kỳ mạnh",
    "ghê vậy": "thật sự vậy",
    "đỉnh": "tuyệt vời",
    "xịn sò": "chất lượng cao",
    "xịn": "chất lượng tốt",
    "chất": "hay",
    "ảo mạng": "không thật",
    "ảo": "tuyệt vời",
    "vãi": "quá",
    "bá": "giỏi nhất",
    "siêu": "rất",
    "hơi": "một chút",
    "ghê": "thật sự",
    "dữ": "mạnh mẽ",

    # Emotions & reactions
    "cười muốn xỉu": "cười rất nhiều",
    "chết cười": "cười không ngừng",
    "choáng vãi": "cực kỳ ngạc nhiên",
    "xỉu ngang": "quá xúc động",
    "tức điên": "rất tức giận",
    "haizz": "thở dài",
    "haizt": "thở dài",
    "hiz": "thở dài",
    "sktt": "sắp khóc tới nơi",
    "xỉu": "ngã xỉu vì xúc động",
    "choáng": "ngạc nhiên",
    "sượng": "ngại ngùng",
    "ngại": "xấu hổ",
    "tức": "tức giận",
    "bực": "khó chịu",
    "ehe": "hehe ngại ngùng",

    # Relationship & social
    "hóng drama": "tò mò về drama",
    "thả thính": "tán tỉnh",
    "thả tym": "bày tỏ tình cảm",
    "bơi thuyền": "không chung thủy",
    "iu lắm": "yêu nhiều",
    "đứa bạn": "người bạn",
    "con này": "người này",
    "iu": "yêu",
    "tym": "trái tim / yêu",
    "thính": "lời tán tỉnh",
    "hóng": "đang chờ xem",
    "drama": "câu chuyện rắc rối",
    "tám": "nói chuyện phiếm",
    "ghiền": "nghiện",
    "men": "bạn bè",
    "thanh niên": "bạn",
    "đứa": "người bạn",
    "thằng": "người đó",
    "report": "báo cáo",
    "block": "chặn",
    "unfollow": "bỏ theo dõi",
    "follow": "theo dõi",
    "stan": "người hâm mộ cuồng nhiệt",
    "antifan": "người ghét",

    # Daily life & internet
    "ảnh sống ảo": "ảnh chụp để đăng mạng",
    "sống ảo": "chụp ảnh để đăng mạng",
    "hot trend": "xu hướng nổi",
    "check in": "ghé thăm và chụp ảnh",
    "ngon vãi": "rất ngon",
    "đói vãi": "rất đói",
    "mlem": "trông ngon",
    "chill": "thư giãn",
    "healing": "đang thư giãn",
    "flex": "khoe khoang",
    "trend": "xu hướng",
    "viral": "lan truyền rộng rãi",
    "no rồi": "đã ăn no rồi",

    # Southern dialect
    "hổng có": "không có",
    "thiệt hả": "thật hả",
    "bổng dưng": "bỗng nhiên",
    "dzạo ni": "dạo này",
    "hổng": "không",
    "thiệt": "thật",
    "dzui": "vui",
    "dzô": "vào",
    "rứa": "vậy",

    # Central dialect (Huế / Đà Nẵng)
    "răng": "sao",
    "mô": "đâu",
    "ri": "này",
}

# ─────────────────────────────────────────────────────────────────────────────
# Indonesian Slang Dictionary
# ─────────────────────────────────────────────────────────────────────────────
ID_SLANG: dict[str, str] = {
    # Common abbreviations
    "gw": "saya",             # "I/me"
    "gue": "saya",
    "gua": "saya",
    "lo": "kamu",             # "you"
    "lu": "kamu",
    "lw": "kamu",
    "yg": "yang",             # "that/which"
    "ygg": "yang",
    "dgn": "dengan",          # "with"
    "dg": "dengan",
    "sm": "sama",             # "same/with"
    "jg": "juga",             # "also"
    "juga": "juga",
    "tp": "tapi",             # "but"
    "tpi": "tapi",
    "krn": "karena",          # "because"
    "karna": "karena",
    "krna": "karena",
    "bntr": "sebentar",       # "wait a moment"
    "bentar": "sebentar",
    "bntran": "sebentar",
    "skrg": "sekarang",       # "now"
    "skr": "sekarang",
    "udah": "sudah",          # "already"
    "udh": "sudah",
    "sdh": "sudah",
    "blm": "belum",           # "not yet"
    "blum": "belum",
    "msh": "masih",           # "still"
    "masi": "masih",
    "ga": "tidak",            # "no/not"
    "gak": "tidak",
    "nggak": "tidak",
    "engga": "tidak",
    "enggak": "tidak",
    "ngga": "tidak",
    "tdk": "tidak",
    "dpt": "dapat",           # "get/can"
    "bs": "bisa",             # "can"
    "bsa": "bisa",
    "lg": "lagi",              # keep 'lagi' (sedang breaks grammar with tidak)
    "hrs": "harus",           # "must"
    "bgt": "banget",          # "banget" abbreviation
    "banget": "sangat",       # "very/so much"
    "pol": "banget",          # another form "banget"

    # Gaul / slang
    "gaskeun": "ayo",          # "let's go" — 'ayo' maps to 'let's go' better than 'ayo lakukan'
    "gass": "ayo",
    "gas": "ayo",
    "mantul": "mantap betul",  # "awesome"
    "mantap": "bagus sekali",
    "baper": "bawa perasaan",  # "overly emotional"
    "mager": "malas bergerak",  # "lazy to move"
    "gabut": "sangat bosan",    # "bored/have nothing to do" — simpler for model
    "bucin": "budak cinta",    # "lovesick"
    "julid": "iri dan jahat",  # "jealous and mean"
    "lebay": "berlebihan",     # "overdramatic"
    "kepo": "ingin tahu urusan orang lain", # "nosy"
    "bete": "bad mood",        # keep as-is understood
    "galau": "bimbang dan sedih",
    "santuy": "santai",        # "chill/relax"
    "sabi": "bisa",
    "woles": "santai saja",   # "chill"
    "ngab": "teman",          # "bro/dude"
    "bestie": "sahabat",
    "gws": "semoga cepat sembuh", # "get well soon"
    "oot": "tidak relevan",
    "ntar": "nanti",          # "later"
    "tar": "nanti",
    "trus": "lalu",           # "then/and"
    "terus": "lalu",
    "sama aja": "sama saja",
    "gimana": "bagaimana",    # "how"
    "gmn": "bagaimana",
    "emg": "memang",          # "indeed"
    "emang": "memang",
    "sih": "sih",             # particle, keep
    "dong": "dong",           # particle, keep
    "nih": "ini",             # "this"
    "tuh": "itu",             # "that"
    "guys": "teman-teman",    # "guys"
    "wkwk": "haha",           # laugh
    "wkwkwk": "haha",
    "wk": "haha",
    "xixi": "haha",
    "hehe": "hehe",

    # Social media / gen-z
    "otw": "sedang dalam perjalanan",
    "irl": "di dunia nyata",
    "fyi": "sebagai informasi",
    "tbh": "jujur saja",
    "ngl": "tidak bohong",
    "imo": "menurut saya",
    "idk": "saya tidak tahu",
    "lol": "lucu",
    "omg": "ya ampun",
    "btw": "ngomong-ngomong",
    "asap": "sesegera mungkin",
    "typo": "salah ketik",
    "slay": "keren sekali",
    "vibe": "nuansa",
    "mood": "suasana hati",
    "healing": "menenangkan diri",
    "toxic": "buruk/berbahaya",
    "ghosting": "tiba-tiba menghilang",
}

# ─────────────────────────────────────────────────────────────────────────────
# English Slang Dictionary
# ─────────────────────────────────────────────────────────────────────────────
EN_SLANG: dict[str, str] = {
    # Abbreviations
    "idk": "I don't know",
    "imo": "in my opinion",
    "imho": "in my honest opinion",
    "ngl": "not going to lie",
    "tbh": "to be honest",
    "nvm": "never mind",
    "omg": "oh my god",
    "omw": "on my way",
    "otw": "on the way",
    "btw": "by the way",
    "fyi": "for your information",
    "irl": "in real life",
    "asap": "as soon as possible",
    "lol": "laughing out loud",
    "lmao": "laughing a lot",
    "rofl": "rolling on the floor laughing",
    "smh": "shaking my head",
    "icymi": "in case you missed it",
    "tfw": "that feeling when",
    "mfw": "my face when",
    "iirc": "if I recall correctly",
    "afaik": "as far as I know",
    "wdym": "what do you mean",
    "wym": "what you mean",
    "hmu": "hit me up",
    "dm": "direct message",
    "imo": "in my opinion",
    "smth": "something",
    "sth": "something",
    "rn": "right now",
    "rq": "real quick",
    "brb": "be right back",
    "bbl": "be back later",
    "gtg": "got to go",
    "g2g": "got to go",
    "ttyl": "talk to you later",
    "ty": "thank you",
    "thx": "thanks",
    "np": "no problem",
    "yw": "you're welcome",
    "u": "you",
    "r": "are",
    "b4": "before",
    "2": "to",
    "4": "for",
    "gr8": "great",
    "luv": "love",
    "w/": "with",
    "w/o": "without",

    # Gen-Z slang
    "fr": "for real",
    "fr fr": "for real",
    "no cap": "no lie / seriously",
    "cap": "lie",
    "bussin": "very good",
    "slay": "doing great",
    "lowkey": "kind of / secretly",
    "highkey": "very much / openly",
    "sus": "suspicious",
    "mid": "mediocre",
    "fire": "amazing",
    "goat": "greatest of all time",
    "lit": "exciting",
    "vibe": "atmosphere / mood",
    "vibe check": "checking the mood",
    "mood": "relatable feeling",
    "salty": "upset / bitter",
    "extra": "over the top",
    "basic": "unoriginal",
    "flex": "show off",
    "ghosting": "suddenly ignoring someone",
    "glow up": "significant improvement",
    "bet": "okay / agreed",
    "yeet": "throw / expression of excitement",
    "tea": "gossip",
    "spill the tea": "share the gossip",
    "simp": "someone who does too much for another",
    "stan": "dedicated fan",
    "clout": "fame / influence",
    "shade": "disrespect",
    "periodt": "that's final",
    "hits different": "feels uniquely good",
    "understood the assignment": "did a great job",
    "rent free": "can't stop thinking about",
    "toxic": "harmful / bad",
    "red flag": "warning sign",
    "green flag": "positive sign",
    "ship": "support a romantic pairing",
    "bff": "best friend forever",
    "bestie": "best friend",
    "sis": "friend (female)",
    "bro": "friend",
    "fam": "close friend group",
    "innit": "isn't it",
    "gonna": "going to",
    "wanna": "want to",
    "gotta": "got to",
    "kinda": "kind of",
    "sorta": "sort of",
    "lemme": "let me",
    "gimme": "give me",
    "dunno": "don't know",
    "ya": "you",
    "yep": "yes",
    "nope": "no",
    "yup": "yes",
}

# Map lang code → slang dictionary
SLANG_DICTS: dict[str, dict[str, str]] = {
    "vi": VI_SLANG,
    "id": ID_SLANG,
    "en": EN_SLANG,
}


# Keys that are pure intensifiers — capped at MAX_INTENSIFIERS per sentence
# to prevent model repetition when they stack up.
INTENSIFIER_KEYS: frozenset[str] = frozenset({
    "đỉnh của chóp", "đỉnh", "xịn sò", "xịn", "chất lừ", "chất",
    "bá đạo", "bá", "thần thánh", "vãi chưởng", "vãi cả người",
    "ảo vãi", "ảo", "vãi", "siêu", "ghê", "ghê vậy", "dữ", "dữ vậy",
    "quá trời",
})
MAX_INTENSIFIERS = 2  # cap per sentence to avoid model repetition


def normalize(text: str, lang: Optional[str] = None) -> tuple[str, list[str]]:
    """
    Normalize slang in text before translation.

    Args:
        text: Input text (may contain slang)
        lang: ISO 639-1 language code ('vi', 'id', 'en').
              If None, tries VI → ID → EN order.

    Returns:
        (normalized_text, list of replacements made)
        Replacements are formatted as 'slang → formal'
    """
    replacements: list[str] = []

    if lang and lang in SLANG_DICTS:
        dicts_to_apply = [(lang, SLANG_DICTS[lang])]
    else:
        dicts_to_apply = [
            ("vi", VI_SLANG),
            ("id", ID_SLANG),
            ("en", EN_SLANG),
        ]

    result = text
    protected: set[str] = set()
    intensifier_count = 0  # track how many intensifiers we've already replaced

    for lang_code, slang_dict in dicts_to_apply:
        # Longer phrases first to avoid partial matches
        sorted_items = sorted(slang_dict.items(), key=lambda x: len(x[0]), reverse=True)
        for slang, formal in sorted_items:
            # Cap intensifier replacements per sentence
            if slang in INTENSIFIER_KEYS and intensifier_count >= MAX_INTENSIFIERS:
                continue

            # Protect already-translated output from being re-matched
            if any(slang.lower() in p.lower() for p in protected):
                continue

            pattern = r"(?<!\w)" + re.escape(slang) + r"(?!\w)"
            new_result, n = re.subn(pattern, formal, result, flags=re.IGNORECASE)
            if n > 0:
                replacements.append(f'"{slang}" → "{formal}"')
                protected.add(formal)
                result = new_result
                if slang in INTENSIFIER_KEYS:
                    intensifier_count += 1

    if replacements:
        log.debug(f"Slang normalized ({len(replacements)} replacements): {replacements}")

    return result, replacements


def post_process(text: str) -> str:
    """
    Clean up common model translation artifacts:
    - Remove consecutively repeated sentences (e.g. "It's great. It's great. It's great.")
    - Normalize spacing and punctuation

    Args:
        text: Raw translation output from model

    Returns:
        Cleaned translation string
    """
    import re as _re

    # Strip HTML/API artifacts that occasionally appear in Helsinki-NLP output
    # e.g. 'fontcolor="#FFFF00"' markers, stray XML tags
    text = _re.sub(r'fontcolor\s*=\s*"[^"]*"', '', text)
    text = _re.sub(r'<[^>]+>', '', text)
    text = text.strip()

    # Split into sentences on . ! ? ; keeping delimiter
    sentences = _re.split(r'(?<=[.!?;])\s+', text)

    # Deduplicate consecutive identical sentences (case-insensitive)
    deduped: list[str] = []
    for sent in sentences:
        normalized_sent = sent.strip().lower().rstrip('.!?;')
        if not deduped or normalized_sent != deduped[-1].strip().lower().rstrip('.!?;'):
            deduped.append(sent.strip())

    result = ' '.join(deduped)

    # Clean up extra spaces
    result = _re.sub(r'  +', ' ', result).strip()

    return result
