from pypinyin import Style, lazy_pinyin
import re

def get_acronym(raw):
    return ''.join(lazy_pinyin(raw, style=Style.FIRST_LETTER))

def sanitize(raw):
    # Only keey "safe" chars
    return re.sub(r"[^a-zA-Z0-9()_]", "", raw)
