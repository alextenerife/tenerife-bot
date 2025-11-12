# config.py
import os

# --- Telegram (через переменные окружения на Render/GitHub secrets) ---
TELEGRAM = {
    "enabled": True,
    "bot_token": os.getenv("BOT_TOKEN", ""),   # установите в Render / GitHub secrets
    "chat_id": os.getenv("CHAT_ID", "")        # ваш telegram chat id
}

# --- Пороговые цены (евро) ---
PRICE_THRESHOLDS = {
    "land": 200000,
    "rural_house": 250000,
    "villa": 300000,
    "finca": 300000
}

# --- Динамические лимиты по умолчанию (поддержка user_limits.py) ---
DEFAULT_USER_LIMITS = {
    "land": PRICE_THRESHOLDS["land"],
    "rural_house": PRICE_THRESHOLDS["rural_house"],
    "villa": PRICE_THRESHOLDS["villa"],
    "finca": PRICE_THRESHOLDS["finca"]
}

# --- Районы юга Тенерифе (фильтр по тексту) ---
SOUTH_KEYWORDS = [
    "adeje", "costa adeje", "arona", "los cristianos", "playa de las americas",
    "granadilla", "granadilla de abona", "san miguel", "san miguel de abona",
    "arico", "fasnia", "vilaflor", "guia de isora", "guía de isora",
    "callao salvaje", "la caleta", "el madroñal", "chayofa", "la camella",
    "buzanada", "taucho"
]

# --- TYPE_KEYWORDS: ключевые слова для определения типа объекта ---
TYPE_KEYWORDS = {
    "land": ["parcela", "solar", "terreno", "plot", "land", "lote"],
    "rural_house": ["casa rural", "country house", "cottage", "casa de campo", "casa"],
    "villa": ["villa", "villas"],
    "finca": ["finca", "finca rústica", "finca con casa"]
}

# --- Источники: (module_path, start_url, friendly_name) ---
SOURCES = [
    # порталы
    ("parsers.kyero", "https://www.kyero.com/en/tenerife-property-for-sale-0l55570", "Kyero"),
    ("parsers.idealista", "https://www.idealista.com/en/venta-viviendas/tenerife/", "Idealista"),
    ("parsers.fotocasa", "https://www.fotocasa.es/es/comprar/viviendas/tenerife-provincia/tenerife/l", "Fotocasa"),

    # 15 агентств (модули, которые ты добавил)
    ("parsers.agency_engelvokkers", "https://www.engelvoelkers.com/en-es/tenerife/", "Engel & Völkers Tenerife"),
    ("parsers.agency_vym_canarias", "https://tenerifecenter.com/", "VYM Canarias"),
    ("parsers.agency_asten_realty", "https://www.astenrealty.com/", "ASTEN Realty"),
    ("parsers.agency_clear_blue_skies", "
