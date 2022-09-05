from pypinyin import Style, lazy_pinyin
import re
import numpy

def get_acronym(raw) -> str:
    return ''.join(lazy_pinyin(str(raw), style=Style.FIRST_LETTER))

def sanitize(raw) -> str:
    # Only keep "safe" chars
    step1 = re.sub(r"[^a-zA-Z0-9_.,]", "", str(raw))
    # Move leading digits to the end
    match = re.search(r'(\d*)(.*)', step1)
    step2 = match[2] + match[1]
    return step2

def sanitize_ext(raw) -> str:
    # Only keep "safe" chars
    step1 = re.sub(r"[^a-zA-Z0-9()_.,]", "", str(raw))
    # Move leading digits to the end
    match = re.search(r'(\d*)(.*)', step1)
    step2 = match[2] + match[1]
    return step2

def stripHTML(html: str) -> str:
    return re.sub(r"<.*?>", "", html)

def printable(raw: str) -> str:
    return ''.join(c for c in raw if c.isprintable())

def printableList(rawList: list) -> list:
    return list(map(printable, rawList))

def nan2num(rawList: list, nan=0) -> list:
    newList = rawList.copy()
    for i in range(len(rawList)):
        x = rawList[i]
        try: # Check numbers for np.nan
            newList[i] = nan if numpy.isnan(x) else x
        except TypeError: # Keep strings (and possibily other types) unchanged
            newList[i] = x
    return newList
