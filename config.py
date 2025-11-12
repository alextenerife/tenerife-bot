# config.py
"""
Конфигурация Tenerife Property Bot — с фильтрацией по югу острова.
Замените существующий config.py на этот файл в репозитории.
"""

import os

# -----------------------------
# ⚙️ Основные настройки
# -----------------------------
SETTINGS = {
    "max_pages_per_source": 2,
    "delay_between_requests": 1.5,
    "save_to_csv": True,
    "enable_db": True,
    "collect_interval_seconds": 3600,  # каждые 60 минут
}

# -----------------------------
# 💬 Telegram
# -----------------------------
TELEGRAM = {
    "bot_token": os.getenv("BOT_TOKEN", "ВСТАВЬ_ТОКЕН"),
    "chat_id": os.getenv("CHAT_ID", "ВСТАВЬ_CHAT_ID"),
}

# -----------------------------
# 💰 Пороговые цены (евро)
# -----------------------------
PRICE_THRESHOLDS = {
    "land": 200000,
    "rural_house": 250000,
    "villa": 300000,
    "finca": 250000,
}

# -----------------------------
# 🟢 Юг Тенерифе — ключевые слова (фильтр по тексту адреса/title/description)
# -----------------------------
# Бот проверяет появление любого из этих слов (case-insensitive) в поле address/title/description.
# При необходимости можно добавить или удалить топонимы.
SOUTH_KEYWORDS = [
    # основные муниципалитеты и популярные районы юга
    "adeje", "costa adeje", "san eugenio", "el duque", "la caleta",
    "arona", "los cristianos", "playa de las americas", "las americas", "tenerife south",
    "granadilla", "granadilla de abona", "san miguel de abona", "san miguel",
    "arico", "fasnia", "vilaflor", "guia de isora", "guía de isora",
    "callao salvaje", "chayofa", "la camella", "buzanada", "taucho",
    "los gigantes", "puerto de santiago", "santiago del teide",
    "alcalá", "el medano", "la teja", "las galletas", "chiñor", "ifonche",
    # вариации/сокращения
    "adeje/costa adeje", "playa de las americas", "los cristiano"
]

# -----------------------------
# 🏷 Типы недвижимости — ключевые слова для детекции
# -----------------------------
TYPE_KEYWORDS = {
    "land": ["parcela", "solar", "terreno", "plot", "land", "lote"],
    "rural_house": ["casa rural", "country house", "cottage", "casa de campo", "casa"],
    "villa": ["villa", "villas", "detached house", "chalet"],
    "finca": ["finca", "finca rústica", "finca con casa", "finca rustica"]
}

# -----------------------------
# 📚 Источники (модули парсеров, стартовые URL и дружелюбное имя)
# -----------------------------
SOURCES = [
    # порталы
    ("parsers.kyero", "https://www.kyero.com/en/property-for-sale/tenerife-islands?lang=en", "Kyero"),
    ("parsers.idealista", "https://www.idealista.com/en/venta-viviendas/tenerife/", "Idealista"),
    ("parsers.fotocasa", "https://www.fotocasa.es/en/buy/homes/santa-cruz-de-tenerife/all-zones/l", "Fotocasa"),

    # агентства (wrapper-модули должны существовать в parsers/)
    ("parsers.agency_engelvokkers", "https://www.engelvoelkers.com/en-es/tenerife/properties/", "Engel & Völkers Tenerife"),
    ("parsers.agency_vym_canarias", "https://tenerifecenter.com/", "VYM Canarias"),
    ("parsers.agency_asten_realty", "https://www.astenrealty.com/", "ASTEN Realty"),
    ("parsers.agency_clear_blue_skies", "https://www.clearbluetenerife.com/", "Clear Blue Skies Group"),
    ("parsers.agency_feel_good", "https://www.feelgoodpropertiestenerife.com/", "Feel Good Properties"),
    ("parsers.agency_tenerife_properties", "https://www.tenerifeproperties.es/", "Tenerife Properties"),
    ("parsers.agency_morfitt", "https://www.morfittpropertiestenerife.com/", "Morfitt Properties"),
    ("parsers.agency_tenerife_property_shop", "https://www.tenerifepropertyshop.com/", "Tenerife Property Shop"),
    ("parsers.agency_tenerife_royale", "https://www.teneriferoyale.com/", "Tenerife Royale"),
    ("parsers.agency_tenerife_property_consultancy", "https://www.tenerifepropertyconsultancy.com/", "Tenerife Property Consultancy"),
    ("parsers.agency_all_properties", "https://allpropertiestenerife.com/", "All Properties Tenerife"),
    ("parsers.agency_tenerife_real", "https://www.tenerifereal.com/", "Tenerife Real"),
]

# -----------------------------
# Доп. настройки
# -----------------------------
LOGGING = {
    "level": os.getenv("LOG_LEVEL", "INFO")
}
