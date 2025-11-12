import os

# --- Telegram (через переменные окружения на Render) ---
TELEGRAM = {
    "enabled": True,
    "bot_token": os.getenv("BOT_TOKEN", ""),   # установим в Render
    "chat_id": os.getenv("CHAT_ID", "")        # установим в Render
}

# --- Пороговые цены (можно менять) ---
PRICE_THRESHOLDS = {
    "land": 200000,
    "rural_house": 250000,
    "villa": 300000,
    "finca": 300000
}

# --- Районы юга Тенерифе ---
SOUTH_KEYWORDS = [
    "adeje", "costa adeje", "arona", "los cristianos", "playa de las americas",
    "granadilla", "granadilla de abona", "san miguel", "san miguel de abona",
    "arico", "fasnia", "vilaflor", "guia de isora", "guía de isora",
    "callao salvaje", "la caleta", "el madroñal", "chayofa", "la camella",
    "buzanada", "taucho"
]

# --- Типы и ключевые слова (упрост.) ---
TYPE_KEYWORDS = {
    "land": ["parcela", "solar", "terreno", "plot", "land", "lote"],
    "rural_house": ["casa rural", "country house", "cottage", "casa de campo", "casa"],
    "villa": ["villa", "villas"],
    "finca": ["finca", "finca rústica", "finca con casa"]
}

# --- Источники (module_path, start_url, friendly_name)
# Пока указываем шаблонные парсеры/URL — позже можно заменить на реальные
SOURCES = [
    ("parsers.kyero", "https://www.kyero.com/en/tenerife-property-for-sale-0l55570", "Kyero"),
    ("parsers.idealista", "https://www.idealista.com/en/venta-viviendas/tenerife/", "Idealista"),
    ("parsers.fotocasa", "https://www.fotocasa.es/es/comprar/viviendas/tenerife-provincia/tenerife/l", "Fotocasa"),
    # агентства - можно заменить на реальные URL
    ("parsers.agency_template", "https://www.example-agency1.com/tenerife/properties", "Agency1"),
    ("parsers.agency_template", "https://www.example-agency2.com/tenerife/listings", "Agency2")
]
