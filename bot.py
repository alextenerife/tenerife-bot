# bot.py
"""
Обновлённый Telegram-бот:
- использует config.SOURCES
- collect_and_notify принимает bot и использует notifier.notify_new_items(bot=bot)
- поддерживает включение/отключение БД через config.SETTINGS["enable_db"]
- периодический сбор запускается с app.bot
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
from utils import detect_type, is_south, is_price_ok, save_to_csv

# notifier и db
import notifier
try:
    from db import save_new_items as db_save_new_items
    DB_MODULE_AVAILABLE = True
except Exception:
    DB_MODULE_AVAILABLE = False

# кнопки/лимиты
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
        "Лимиты сохраняются в памяти (user_limits.py) и используются при фильтрации."
    )

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    try:
        if data == "collect_now":
            await query.edit_message_text("Запуск сбора объявлений... запускаю в фоне.")
            # запускаем сбор в фоне, передаём context.bot (telegram.Bot)
            threading.Thread(target=collect_and_notify, args=(context.bot,), daemon=True).start()
            return

        if data.startswith("select_"):
            type_name = data.split("_", 1)[1]
            options = LIMIT_OPTIONS.get(type_name, [])
            keyboard = [[InlineKeyboardButton(f"≤{p} €", callback_data=f"set_{type_name}_{p}")] for p in options]
            await query.edit_message_text(f"Выберите лимит цены для {type_name}:", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if data.startswith("set_"):
            _, type_name, price = data.split("_")
            price = int(price)
            user_price_limits[type_name] = price
            await query.edit_message_text(f"Лимит для {type_name} установлен: {price} €")
            return

    except Exception as e:
        tb = traceback.format_exc()
        print("callback handler error:", e, tb)
        try:
            await query.edit_message_text("Ошибка при обработке кнопки. Смотри логи.")
        except:
            pass

def collect_and_notify(bot):
    """
    Сбор и уведомление.
    bot: telegram.Bot (может быть None если собираем без контекста) — передаём в notifier.
    """
    try:
        print("Collect: starting")
        results = []
        sources = getattr(config, "SOURCES", [])
        max_pages = config.SETTINGS.get("max_pages_per_source", 1)
        delay = config.SETTINGS.get("delay_between_requests", 1.2)

        for module_path, start_url, friendly_name in sources:
            try:
                mod = importlib.import_module(module_path)
            except Exception as e:
                print(f"[{friendly_name}] import error: {e}")
                continue

            if not hasattr(mod, "get_listings"):
                print(f"[{friendly_name}] parser has no get_listings(), skipping")
                continue

            try:
                found = mod.get_listings(start_url, max_pages=max_pages, delay=delay, source_name=friendly_name)
                if not isinstance(found, list):
                    print(f"[{friendly_name}] parser returned non-list, skipping")
                    continue
                for it in found:
                    it.setdefault("source", friendly_name)
                print(f"[{friendly_name}] collected {len(found)} items")
                results.extend(found)
            except Exception as e:
                print(f"[{friendly_name}] runtime error: {e}")

        # Фильтрация и маркировка
        candidates = []
        for it in results:
            try:
                it.setdefault("title", "")
                it.setdefault("address", "")
                it.setdefault("description", "")
                it.setdefault("price", None)
                it['detected_type'] = detect_type(it)
                if not it['detected_type']:
                    continue
                if not is_south(it):
                    continue
                # нормализация цены
                try:
                    it['price'] = int(it['price']) if it.get('price') not in (None, "") else None
                except:
                    s = str(it.get('price') or "")
                    s = "".join(ch for ch in s if ch.isdigit())
                    it['price'] = int(s) if s else None
                if is_price_ok(it):
                    candidates.append(it)
            except Exception as e:
                print("item processing error:", e)

        print(f"Collect: candidates after filter = {len(candidates)}")

        # Сохранение CSV
        if config.SETTINGS.get("save_to_csv", True):
            csv_path = save_to_csv(candidates)
            if csv_path:
                print("Saved CSV:", csv_path)

        # Сохранение в БД (если включено)
        new_items = candidates
        if config.SETTINGS.get("enable_db", False) and DB_MODULE_AVAILABLE:
            try:
                new_items = db_save_new_items(candidates)
                print(f"DB: {len(new_items)} new items saved")
            except Exception as e:
                print("DB save error:", e)
        else:
            # если БД не используется — будем считать все кандидаты как 'новые'
            pass

        # Нотификация (передаём bot для использования notifier)
        if new_items:
            try:
                notifier.notify_new_items(new_items, bot=bot)
                print(f"Notified {len(new_items)} items")
            except Exception as e:
                print("Notify error:", e)
        else:
            print("No new items to notify")

    except Exception as e:
        print("Collect_and_notify critical error:", e)

def start_periodic_collect(app):
    """
    Запустить фоновые периодические сборы, передаём app.bot как bot.
    """
    interval = config.SETTINGS.get("collect_interval_seconds", 3600)
    def job():
        time.sleep(5)
        while True:
            try:
                print("Periodic collect triggered")
                # app.bot доступен после ApplicationBuilder().build()
                try:
                    bot = app.bot
                except Exception:
                    bot = None
                collect_and_notify(bot)
            except Exception as e:
                print("Periodic collect error:", e)
            time.sleep(interval)
    t = threading.Thread(target=job, daemon=True)
    t.start()

def main():
    token = config.TELEGRAM.get("bot_token")
    if not token:
        print("BOT_TOKEN not set in config.TELEGRAM or environment. Exiting.")
        return

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    print("Starting bot...")
    # start periodic collector thread (will access app.bot)
    start_periodic_collect(app)
    # run_polling (blocking)
    app.run_polling()

if __name__ == "__main__":
    main()
