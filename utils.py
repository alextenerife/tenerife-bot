# utils.py
import re
from config import SOUTH_KEYWORDS, TYPE_KEYWORDS
from user_limits import user_price_limits

def text_norm(s):
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r'[^0-9a-zа-яё\u00C0-\u017F\s\-]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def detect_type(item):
    text = " ".join([str(item.get(k,"")) for k in ("title","address","description")])
    txt = text_norm(text)
    for t, keys in TYPE_KEYWORDS.items():
        for k in keys:
            if k in txt:
                return t
    return None

def is_south(item):
    txt = text_norm(" ".join([item.get("address",""), item.get("title","")]))
    for kw in SOUTH_KEYWORDS:
        if kw in txt:
            return True
    return False

def is_price_ok(item):
    t = item.get("detected_type")
    price = item.get("price")
    if not t or price is None:
        return False
    limit = user_price_limits.get(t)
    if limit is None:
        return False
    try:
        return int(price) <= int(limit)
    except:
        return False
