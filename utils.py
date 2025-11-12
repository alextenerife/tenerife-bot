# utils.py
"""
Вспомогательные функции:
- text_norm: нормализация строки
- detect_type: определяет тип объекта по ключевым словам
- is_south: проверяет присутствие локаций юга Тенерифе
- is_price_ok: проверка по текущим user limits (user_limits.py) или PRICE_THRESHOLDS
- save_to_csv: сохранение кандидатов в outputs/
"""

import re
import os
import csv
from datetime import datetime

import config
from user_limits import user_price_limits

def text_norm(s):
    if not s:
        return ""
    s = str(s).lower()
    # оставить буквы/цифры/пробел/диакритику
    s = re.sub(r'[^0-9a-zа-яё\u00C0-\u017F\s\-]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def contains_any(text, keywords):
    txt = text_norm(text)
    for k in keywords:
        if k in txt:
            return True
    return False

def detect_type(item):
    """
    Вернёт одну из ключей TYPE_KEYWORDS ('land','rural_house','villa','finca') или None.
    Ищем совпадения в title, address, description.
    """
    text = " ".join([
        str(item.get("title","") or ""),
        str(item.get("address","") or ""),
        str(item.get("description","") or "")
    ])
    txt = text_norm(text)
    for t, keys in config.TYPE_KEYWORDS.items():
        for k in keys:
            if k in txt:
                return t
    return None

def is_south(item):
    txt = text_norm(" ".join([item.get("address","") or "", item.get("title","") or ""]))
    for kw in config.SOUTH_KEYWORDS:
        if kw in txt:
            return True
    return False

def is_price_ok(item):
    t = item.get("detected_type")
    price = item.get("price")
    if not t or price is None:
        return False
    try:
        p = int(price)
    except:
        return False
    # сначала смотрим пользовательский лимит
    limit = user_price_limits.get(t)
    if limit is None:
        limit = config.PRICE_THRESHOLDS.get(t)
    if limit is None:
        return False
    try:
        return p <= int(limit)
    except:
        return False

def save_to_csv(items, filename=None):
    """
    Сохраняет candidates в outputs/candidates_YYYYMMDD_HHMMSS.csv
    Возвращает путь к файлу или None
    """
    if not items:
        return None
    os.makedirs("outputs", exist_ok=True)
    if not filename:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"candidates_{ts}.csv"
    path = os.path.join("outputs", filename)
    fieldnames = ["title","price","link","address","source","detected_type"]
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for it in items:
                row = {k: it.get(k,"") for k in fieldnames}
                writer.writerow(row)
        return path
    except Exception as e:
        print("save_to_csv error:", e)
        return None
