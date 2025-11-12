# config.py
"""
Основной файл конфигурации Tenerife Property Bot.
Настройки парсинга, Telegram и фильтрации по цене.
"""

import os

# -----------------------------
# ⚙️ Основные настройки
# -----------------------------
SETTINGS = {
    # Количество страниц, которые парсим с каждого источника
    "max_pages_per_source": 2,

    # Задержка между запросами (в секундах)
    "delay_between_requests": 1.5,

    # Сохранять ли результаты в CSV
    "save_to_csv": True,

    # Включить ли базу данных (если настроена db.py)
    "enable_db": True,

    # Интервал между автоматическими проверками (в секундах)
    "collect_interval_seconds": 3600,  # каждый час
}

# -----------------------------
# 💬 Telegram настройки
# -----------------------------
TELEGRAM = {
    # Токен бота из BotFather
    "bot_token": os.getenv("BOT_TOKEN", "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН"),

    # Твой chat_id (узнать через @userinfobot)
    "chat_id": os.getenv("CHAT_ID", "ВСТАВЬ_СЮДА_СВОЙ_CHAT_ID"),
}

# -----------------------------
# 💰 Пороги "дешёвой" цены (евро)
# -----------------------------
PRICE_THRESHOLDS = {
    "land": 200000,         # участки <= 200 000 €
    "rural_house": 250000,  # деревенские / маленькие дома <= 250 000 €
    "villa": 300000,        # виллы <= 300 000 €
    "finca": 250000,        # финки с домом <= 250 000 €
}

# -----------------------------
# 🌍 Источники данных (порталы и агентства)
# -----------------------------
SOURCES = [
    # === Порталы ===
    ("parsers.kyero", "https://www.kyero.com/en/property-for-sale/tenerife-islands?lang=en", "Kyero"),
    ("parsers.idealista", "https://www.idealista.com/en/venta-viviendas/tenerife/", "Idealista"),
    ("parsers.fotocasa", "https://www.fotocasa.es/en/buy/homes/santa-cruz-de-tenerife/all-zones/l", "Fotocasa"),

    # === Агентства недвижимости ===
    ("parsers.agency_01", "https://www.engelvoelkers.com/en-es/tenerife/properties/", "Engel & Völkers Tenerife"),
    ("parsers.agency_02", "https://www.vymcanarias.com/properties-for-sale", "VYM Canarias"),
    ("parsers.agency_03", "https://www.astenrealty.com/properties/", "Asten Realty"),
    ("parsers.agency_04", "https://www.clearbluetenerife.com/search", "Clear Blue Skies Group"),
    ("parsers.agency_05", "https://www.feelgoodpropertiestenerife.com/properties/", "Feel Good Properties"),
    ("parsers.agency_06", "https://www.tenerifeproperties.es/en/properties", "Tenerife Properties"),
    ("parsers.agency_07", "https://www.morfittpropertiestenerife.com/properties", "Morfitt Properties"),
    ("parsers.agency_08", "https://www.tenerifepropertyshop.com/property-listings/", "Tenerife Property Shop"),
    ("parsers.agency_09", "https://secondhometenerife.com/en/properties", "Second Home Tenerife"),
    ("parsers.agency_10", "https://teneriferesidential.com/en/sales/", "Tenerife Residential"),
    ("parsers.agency_11", "https://www.luxuryproperties.es/en/properties", "Luxury Properties Tenerife"),
    ("parsers.agency_12", "https://www.rightmove.co.uk/overseas-property/in-Tenerife.html", "Rightmove (Spain)"),
    ("parsers.agency_13", "https://www.atlanticproperties.com/en/properties", "Atlantic Properties Tenerife"),
    ("parsers.agency_14", "https://www.casascanarias.com/en/properties", "Casas Canarias"),
    ("parsers.agency_15", "https://www.tenerifeestates.com/en/sales", "Tenerife Estates"),
]
