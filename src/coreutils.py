from pypinyin import Style, lazy_pinyin
import re

def get_acronym(raw) -> str:
    return ''.join(lazy_pinyin(str(raw), style=Style.FIRST_LETTER))

def sanitize(raw) -> str:
    # Only keep "safe" chars
    step1 = re.sub(r"[^a-zA-Z0-9()_.,]", "", str(raw))
    # Move leading digits to the end
    match = re.search(r'(\d*)(.*)', step1)
    step2 = match[2] + match[1]
    return step2

def stripHTML(html: str) -> str:
    return re.sub(r"<.*?>", "", html)

