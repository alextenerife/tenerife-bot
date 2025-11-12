# utils.py
# Утилиты для Tenerife Property Bot.
# В этом файле нет тройных кавычек, чтобы избежать синтаксических ошибок при деплое.

import re
import os
import csv
import math
from datetime import datetime
from difflib import SequenceMatcher

import config
from user_limits import user_price_limits

# Пороговые значения для нечёткого соответствия
FUZZY_THRESHOLD = float(os.getenv("FUZZY_THRESHOLD", 0.86))
TOKEN_FUZZY_THRESHOLD = float(os.getenv("TOKEN_FUZZY_THRESHOLD", 0.92))


# Вспомогательная функция: расстояние Haversine (в километрах)
def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# Нормализация текста
def text_norm(s):
    if s is None:
        return ""
    s = str(s).lower()
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


# Нечёткая похожесть двух строк
def _similar(a, b):
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


# Определение типа объекта (land, rural_house, villa, finca)
def detect_type(item):
    text = " ".join([str(item.get(k, "") or "") for k in ("title", "address", "description")])
    txt = text_norm(text)
    for t, keys in config.TYPE_KEYWORDS.items():
        for k in keys:
            if not k:
                continue
            if k in txt:
                return t
            # token fuzzy: сравнить ключ с токенами текста
            for tok in _tokens(txt):
                if _similar(k, tok) >= TOKEN_FUZZY_THRESHOLD:
                    return t
        for k in keys:
            if _similar(k, txt) >= FUZZY_THRESHOLD:
                return t
    return None


# Проверка, относится ли объект к южной части острова
def is_south(item):
    text = " ".join([str(item.get(k, "") or "") for k in ("title", "address", "description")])
    txt = text_norm(text)
    if not txt:
        return False

    # blacklist (если задан в config)
    bl = getattr(config, "SOUTH_BLACKLIST", []) or []
    for b in bl:
        if b and b in txt:
            return False

    # GEO фильтрация (если включена в config.GEO_FILTER)
    geo_conf = getattr(config, "GEO_FILTER", None)
    if geo_conf and geo_conf.get("enabled", False):
        lat = item.get("lat") or item.get("latitude") or item.get("geo_lat")
        lon = item.get("lon") or item.get("longitude") or item.get("geo_lon")
        try:
            if lat is not None and lon is not None:
                lat = float(lat); lon = float(lon)
                center = geo_conf.get("center")
                radius_km = float(geo_conf.get("radius_km", 30.0))
                if center and len(center) == 2:
                    dist = _haversine_km(lat, lon, float(center[0]), float(center[1]))
                    return dist <= radius_km
        except Exception:
            pass  # при ошибке гео-данных продолжаем текстовые проверки

    # точный поиск ключевых слов
    south_keys = getattr(config, "SOUTH_KEYWORDS", []) or []
    for kw in south_keys:
        if not kw:
            continue
        if kw in txt:
            return True

    # token-wise fuzzy match
    txt_tokens = _tokens(txt)
    for kw in south_keys:
        if not kw:
            continue
        kw_norm = text_norm(kw)
        if kw_norm in txt_tokens:
            return True
        kw_tokens = _tokens(kw_norm)
        for kt in kw_tokens:
            for tok in txt_tokens:
                if _similar(kt, tok) >= TOKEN_FUZZY_THRESHOLD:
                    return True
        if _similar(kw_norm, txt) >= FUZZY_THRESHOLD:
            return True

    return False


# Пояснение, почему объявление признано (или не признано) южным — полезно для логов
def explain_is_south(item):
    text = " ".join([str(item.get(k, "") or "") for k in ("title", "address", "description")])
    txt = text_norm(text)

    bl = getattr(config, "SOUTH_BLACKLIST", []) or []
    for b in bl:
        if b in txt:
            return f"BLACKLIST match: '{b}'"

    geo_conf = getattr(config, "GEO_FILTER", None)
    if geo_conf and geo_conf.get("enabled", False):
        lat = item.get("lat") or item.get("latitude") or item.get("geo_lat")
        lon = item.get("lon") or item.get("longitude") or item.get("geo_lon")
        if lat is not None and lon is not None:
            try:
                center = geo_conf.get("center")
                radius_km = float(geo_conf.get("radius_km", 30.0))
                dist = _haversine_km(float(lat), float(lon), float(center[0]), float(center[1]))
                if dist <= radius_km:
                    return f"GEO match: distance {dist:.1f} km <= {radius_km} km"
                else:
                    return f"GEO non-match: distance {dist:.1f} km > {radius_km} km"
            except Exception:
                pass

    south_keys = getattr(config, "SOUTH_KEYWORDS", []) or []
    for kw in south_keys:
        if kw in txt:
            return f"KEYWORD exact match: '{kw}'"
    for kw in south_keys:
        if _similar(text_norm(kw), txt) >= FUZZY_THRESHOLD:
            return f"KEYWORD fuzzy full match: '{kw}'"
        kw_tokens = _tokens(text_norm(kw))
        for kt in kw_tokens:
            for tok in _tokens(txt):
                if _similar(kt, tok) >= TOKEN_FUZZY_THRESHOLD:
                    return f"KEYWORD fuzzy token match: '{kt}' ~ '{tok}'"
    return "No south match"


# Нормализация цены: строка/число -> int (евро) или None
def normalize_price(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        try:
            return int(v)
        except Exception:
            return None
    s = str(v).lower()
    s = s.replace('.', '').replace(',', '')
    m = re.search(r'(\d+)\s*([km]?)', s)
    if not m:
        digits = re.sub(r'[^\d]', '', s)
        return int(digits) if digits else None
    num = int(m.group(1))
    suffix = m.group(2)
    if suffix == 'k':
        return num * 1000
    if suffix == 'm':
        return num * 1000000
    return num


# Проверка цены относительно лимитов
def is_price_ok(item):
    t = item.get("detected_type")
    raw_price = item.get("price")
    price = normalize_price(raw_price)
    if t is None:
        return False
    if price is None:
        return False
    limit = user_price_limits.get(t)
    if limit is None:
        limit = config.PRICE_THRESHOLDS.get(t)
    if limit is None:
        return False
    try:
        return int(price) <= int(limit)
    except Exception:
        return False


# Сохранение результатов в CSV
def save_to_csv(items, filename=None):
    if not items:
        return None
    os.makedirs("outputs", exist_ok=True)
    if not filename:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"candidates_{ts}.csv"
    path = os.path.join("outputs", filename)
    fieldnames = ["title", "price", "link", "address", "source", "detected_type"]
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for it in items:
                writer.writerow({k: it.get(k, "") for k in fieldnames})
        return path
    except Exception as e:
        print("save_to_csv error:", e)
        return None
