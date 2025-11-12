# ===============================================
# 🏝️ config.py — настройки бота Tenerife Parser
# ===============================================
# Этот файл содержит общие параметры, конфигурацию Telegram и список источников.
# Все чувствительные данные (токен, chat_id) читаются из переменных окружения Render.
# ===============================================

import os

# -----------------------------
# ⚙️ Основные настройки
# -----------------------------
SETTINGS = {
    "max_pages_per_source": 2,            # сколько страниц парсить с каждого сайта
    "delay_between_requests": 1.5,        # задержка между запросами (сек)
    "save_to_csv": True,                  # сохранять результаты в CSV
    "enable_db": True,                    # сохранять в базу (если есть db.py)
    "collect_interval_seconds": 3600,     # интервал автосбора (в секундах) — 3600 = 1 час
}

# -----------------------------
# 💬 Telegram
# -----------------------------
# Эти значения подставляются из переменных окружения на Render:
# BOT_TOKEN — токен бота
# CHAT_ID   — chat_id получателя уведомлений (можно оставить пустым)
TELEGRAM = {
    "bot_token": os.getenv("BOT_TOKEN", ""),   # ← токен бота
    "chat_id": os.getenv("CHAT_ID", ""),       # ← твой chat_id
}

# -----------------------------
# 💶 Пороговые значения "дешёвых" объектов
# -----------------------------
# Эти лимиты используются при фильтрации объявлений.
PRICE_THRESHOLDS = {
    "land": 200000,        # участки <= 200 000 €
    "rural_house": 250000, # деревенские / маленькие дома <= 250 000 €
    "villa": 300000,       # виллы <= 300 000 €
    "finca": 250000,       # финки с домом <= 250 000 €
}

# -----------------------------
# 🌐 Источники данных (модули парсеров)
# -----------------------------
# Каждый элемент — это (модуль, URL, читаемое имя)
SOURCES = [
    ("parsers.kyero", "https://www.kyero.com/en/property-for-sale/canary-islands/tenerife", "Kyero"),
    ("parsers.idealista", "https://www.idealista.com/en/venta-viviendas/tenerife/", "Idealista"),
    ("parsers.fotocasa", "https://www.fotocasa.es/en/buy/homes/santa-cruz-de-tenerife-province/all-zones/l", "Fotocasa"),
    # агентства недвижимости (пример, подставь свои реальные URL)
    ("parsers.agency1", "https://example1.com/properties", "Agency 1"),
    ("parsers.agency2", "https://example2.com/properties", "Agency 2"),
    ("parsers.agency3", "https://example3.com/properties", "Agency 3"),
    ("parsers.agency4", "https://example4.com/properties", "Agency 4"),
    ("parsers.agency5", "https://example5.com/properties", "Agency 5"),
    ("parsers.agency6", "https://example6.com/properties", "Agency 6"),
    ("parsers.agency7", "https://example7.com/properties", "Agency 7"),
    ("parsers.agency8", "https://example8.com/properties", "Agency 8"),
    ("parsers.agency9", "https://example9.com/properties", "Agency 9"),
    ("parsers.agency10", "https://example10.com/properties", "Agency 10"),
    ("parsers.agency11", "https://example11.com/properties", "Agency 11"),
    ("parsers.agency12", "https://example12.com/properties", "Agency 12"),
    ("parsers.agency13", "https://example13.com/properties", "Agency 13"),
    ("parsers.agency14", "https://example14.com/properties", "Agency 14"),
    ("parsers.agency15", "https://example15.com/properties", "Agency 15"),
]

# ===============================================
# Конец config.py
# ===============================================
