# utils.py
"""
Улучшенные утилиты для Tenerife RealEstate Bot.

Функции:
- text_norm(s)
- detect_type(item)
- is_south(item)
- explain_is_south(item)  # для отладки
- normalize_price(v)
- is_price_ok(item)
- save_to_csv(items, filename=None)

Зависимости: стандартная библиотека.
"""

import re
import os
import csv
import math
from datetime import datetime
from difflib import SequenceMatcher

import config
from user_limits import user_price_limits

# --- Параметры нечёткого сравнения ---
FUZZY_THRESHOLD = float(os.getenv("FUZZY_THRESHOLD", 0.86))  # >= -> считать совпадением
TOKEN_FUZZY_THRESHOLD = float(os.getenv("TOKEN_FUZZY_THRESHOLD", 0.92))

# --- Вспомогательные (haversine) ---
def _haversine_km(lat1, lon1, lat2, lon2):
    # Returns distance in kilometers
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# --- Нормализация текста ---
def text_norm(s):
    if s is None:
        return ""
    s = str(s).lower()
    # keep letters (latin + accented), digits, spaces and hyphen
    s = re.sub(r'[^0-9a-zа-яё\u00C0-\u017F\s\-\.,]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def _tokens(s):
    return [t for t in re.split(r'[\s,;:/\-]+', text_norm(s)) if t]

def contains_any(text, keywords):
    txt = text_norm(text)
    for k in keywords:
        if k and k in txt:
            return True
    return False

# --- Нечёткая похожесть ---
def _similar(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

# --- Определение типа объекта ---
def detect_type(item):
    """
    Ищет ключевые слова из config.TYPE_KEYWORDS в title/address/description.
    Возвращает ключ ('land','rural_house','
