# bot.py
"""
Главный Telegram-бот.
- Меню выбора типа недвижимости и лимитов (InlineKeyboard)
- Кнопка "Run now (collect)" для немедленного запуска сбора
- Фоновый поток: периодический сбор объявлений (интервал в config.SETTINGS)
- Использует парсеры из config.SOURCES и вспомогательные функции из utils.py
"""

import threading
import time
import importlib
import traceback

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

import config
from user_limits import user_price_limits
from notifier import notify_new_items
from utils import detect_type, is_south, is_price_ok, save_to_csv
# db — опционально
try:
    from db import save_new_items as db_save_new_items
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False

# варианты лимитов для быстрого выбора (можно менять)
LIMIT_OPTIONS = {
    "land": [100000, 150000, 200000, 250000],
    "rural_house": [150000, 200000, 250000, 300000],
    "villa": [250000, 300000, 350000, 400000],
    "finca": [200000, 250000, 300000, 350000]
}

def build_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("Land", callback_data="select_land")],
        [InlineKeyboardButton("Rural House", callback_data="select_rural_house")],
        [InlineKeyboardButton("Villa", callback_data="select_villa")],
        [InlineKeyboardButton("Finca", callback_data="select_finca")],
        [InlineKeyboardButton("▶ Run now (collect)", callback_data="collect_now")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для поиска дешевой недвижимости на юге Тенерифе.\n\n"
        "Выберите тип для настройки лимита или нажмите 'Run now' для немедленного сбора.",
        reply_markup=build_main_keyboard()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — меню\n"
        "Кнопка 'Run now (collect)' запускает немедленный сбор\n"
        "Лимиты сохраняются в памяти
