import os

# -----------------------------
# ⚙️ Основные настройки
# -----------------------------
SETTINGS = {
    "max_pages_per_source": 2,        # максимум страниц на одно агентство
    "delay_between_requests": 1.5,    # задержка между запросами (сек)
    "save_to_csv": True,              # сохранять найденные объекты в CSV
    "enable_db": True,                # включить сохранение в базу данных
    "collect_interval_seconds": 3600  # интервал автосбора (сек) = 1 час
}

# -----------------------------
# 💬 Telegram
# -----------------------------
# Эти значения подставляются из переменных окружения на Render:
# BOT_TOKEN — токен бота
# CHAT_ID   — chat_id получателя уведомлений
TELEGRAM = {
    "bot_token": os.getenv("BOT_TOKEN", ""),  # Токен бота
    "chat_id": os.getenv("CHAT_ID", ""),      # ID твоего чата (можно пустым)
}

# -----------------------------
# 💶 Пороговые значения «дешёвой» цены
# -----------------------------
PRICE_THRESHOLDS = {
    "land": 200000,        # участки <= 200 000 €
    "rural_house": 250000, # деревенские дома <= 250 000 €
    "villa": 300000,       # виллы <= 300 000 €
    "finca": 250000        # финки с домом <= 250 000 €
}

# -----------------------------
# 📦 Источники данных (агентства)
# -----------------------------
SOURCES = [
    ("parsers.kyero", "https://www.kyero.com/en/property-for-sale/canary-islands/tenerife", "Kyero"),
    ("parsers.idealista", "https://www.idealista.com/en/venta-viviendas/tenerife/", "Idealista"),
    ("parsers.fotocasa", "https://www.fotocasa.es/en/buy/homes/santa-cruz-de-tenerife-province/all-zones/l", "Fotocasa"),

    # Кастомные агентства (пример — замени URL на реальные)
    ("parsers.agency1", "https://example1.com/tenerife", "Agency 1"),
    ("parsers.agency2", "https://example2.com/tenerife", "Agency 2"),
    ("parsers.agency3", "https://example3.com/tenerife", "Agency 3"),
    ("parsers.agency4", "https://example4.com/tenerife", "Agency 4"),
    ("parsers.agency5", "https://example5.com/tenerife", "Agency 5"),
    ("parsers.agency6", "https://example6.com/tenerife", "Agency 6"),
    ("parsers.agency7", "https://example7.com/tenerife", "Agency 7"),
    ("parsers.agency8", "https://example8.com/tenerife", "Agency 8"),
    ("parsers.agency9", "https://example9.com/tenerife", "Agency 9"),
    ("parsers.agency10", "https://example10.com/tenerife", "Agency 10"),
    ("parsers.agency11", "https://example11.com/tenerife", "Agency 11"),
    ("parsers.agency12", "https://example12.com/tenerife", "Agency 12"),
    ("parsers.agency13", "https://example13.com/tenerife", "Agency 13"),
    ("parsers.agency14", "https://example14.com/tenerife", "Agency 14"),
    ("parsers.agency15", "https://example15.com/tenerife", "Agency 15"),
]

# -----------------------------
# 🏷️ Ключевые слова типов недвижимости
# -----------------------------
TYPE_KEYWORDS = {
    "villa": ["villa", "house", "chalet", "дом", "вилла", "haus"],
    "rural_house": ["country house", "cottage", "деревенский", "finca", "farmhouse"],
    "finca": ["finca", "farm", "ranch", "ферма"],
    "land": ["land", "plot", "parcel", "земля", "terrain", "suelo"],
    "apartment": ["apartment", "flat", "studio", "квартира", "apartamento"],
    "bungalow": ["bungalow", "bungalo"],
    "duplex": ["duplex", "двухуровневая"],
    "penthouse": ["penthouse", "пентхаус"],
    "townhouse": ["townhouse", "row house", "таунхаус"],
}

# -----------------------------
# 📍 Районы юга Тенерифе (для фильтрации)
# -----------------------------
SOUTH_KEYWORDS = [
    "adeje", "los cristianos", "costa adeje", "playa de las americas",
    "arona", "callao salvaje", "la caleta", "el madroñal",
    "torviscas", "fanabe", "chayofa", "guaza", "palm mar",
    "las galletas", "amarilla golf", "golf del sur", "san miguel de abona",
]
