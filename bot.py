# bot.py
# Telegram polling bot + minimal HTTP server so Render Web Service is happy (binds a port).
# Совместим с config.py, user_limits.py, utils.py, notifier.py, db.py и parsers/*.

import threading
import time
import importlib
import traceback
import os
from threading import Thread

from http.server import SimpleHTTPRequestHandler, HTTPServer

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

# notifier и db (db — опционально)
import notifier
try:
    from db import save_new_items as db_save_new_items
    DB_MODULE_AVAILABLE = True
except Exception:
    DB_MODULE_AVAILABLE = False

# Быстрые опции лимитов (можно менять)
LIMIT_OPTIONS = {
    "land": [100000, 150000, 200000, 250000],
    "rural_house": [150000, 200000, 250000, 300000],
    "villa": [250000, 300000, 350000, 400000],
    "finca": [200000, 250000, 300000, 350000]
}


# --------------------------
# Minimal HTTP server helper
# --------------------------
def start_http_server_in_background():
    """
    Запускает очень простой HTTP сервер на порту из окружения (PORT) или 8000.
    Нужен чтобы Render при Web Service видел привязанный порт.
    """
    try:
        port_env = os.getenv("PORT") or os.getenv("RENDER_INTERNAL_PORT")
        port = int(port_env) if port_env else 8000
    except Exception:
        port = 8000

    class _Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            # возвращаем короткий health-check ответ
            self.send_response(200)
            self.send_header("Content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"OK\n")

        def log_message(self, format, *args):
            # подавляем стандартные логи обработчика
            return

    def _run():
        try:
            httpd = HTTPServer(("0.0.0.0", port), _Handler)
            print(f"[http] Listening on 0.0.0.0:{port}")
            httpd.serve_forever()
        except Exception as e:
            print("[http] Server error:", e)

    t = Thread(target=_run, daemon=True)
    t.start()


# --------------------------
# Bot: keyboard / handlers
# --------------------------
def set_user_limit(user_id: int, type_name: str, price: int):
    # В простой реализации сохраняем глобально в user_price_limits
    user_price_limits[type_name] = int(price)
    print(f"[limits] Set {type_name} limit to {price} (user {user_id})")


def build_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("Land", callback_data="select_land")],
        [InlineKeyboardButton("Rural House", callback_data="select_rural_house")],
        [InlineKeyboardButton("Villa", callback_data="select_villa")],
        [InlineKeyboardButton("Finca", callback_data="select_finca")],
        [InlineKeyboardButton("▶ Run now (collect)", callback_data="collect_now")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для поиска дешёвой недвижимости на юге Тенерифе.\n\n"
        "Выберите тип, чтобы установить лимит цены, или нажмите 'Run now' для немедленного сбора.",
        reply_markup=build_main_keyboard()
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — меню\n"
        "Нажмите кнопку с типом недвижимости, чтобы выбрать лимит.\n"
        "Кнопка 'Run now (collect)' запускает немедленный сбор."
    )


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    try:
        if data == "collect_now":
            await query.edit_message_text("Запуск сбора объявлений... выполняю в фоне.")
            threading.Thread(target=collect_and_notify, args=(context.bot,), daemon=True).start()
            return

        if data.startswith("select_"):
            type_name = data.split("_", 1)[1]
            options = LIMIT_OPTIONS.get(type_name, [])
            keyboard = [[InlineKeyboardButton(f"≤{p} €", callback_data=f"set_{type_name}_{p}")] for p in options]
            await query.edit_message_text(f"Выберите лимит цены для {type_name}:", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        if data.startswith("set_"):
            parts = data.split("_", 2)
            if len(parts) == 3:
                _, type_name, price_str = parts
                try:
                    price = int(price_str)
                except Exception:
                    await query.edit_message_text("Неверный формат цены.")
                    return
                uid = update.effective_user.id if update.effective_user else 0
                set_user_limit(uid, type_name, price)
                await query.edit_message_text(f"Лимит для {type_name} установлен: ≤{price} €")
                return

    except Exception as e:
        tb = traceback.format_exc()
        print("callback handler error:", e)
        print(tb)
        try:
            await query.edit_message_text("Ошибка при обработке кнопки. Смотри логи.")
        except Exception:
            pass


# --------------------------
# Collect & notify
# --------------------------
def collect_and_notify(bot):
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
                print(traceback.format_exc())

        candidates = []
        for it in results:
            try:
                it.setdefault("title", "")
                it.setdefault("address", "")
                it.setdefault("description", "")
                it.setdefault("price", None)
                it["detected_type"] = detect_type(it)
                if not it["detected_type"]:
                    continue
                if not is_south(it):
                    continue
                try:
                    it["price"] = int(it["price"]) if it.get("price") not in (None, "") else None
                except Exception:
                    s = str(it.get("price") or "")
                    s = "".join(ch for ch in s if ch.isdigit())
                    it["price"] = int(s) if s else None
                if is_price_ok(it):
                    candidates.append(it)
            except Exception as e:
                print("item processing error:", e)
                print(traceback.format_exc())

        print(f"Collect: candidates after filter = {len(candidates)}")

        if config.SETTINGS.get("save_to_csv", True):
            csv_path = save_to_csv(candidates)
            if csv_path:
                print("Saved CSV:", csv_path)

        new_items = candidates
        if config.SETTINGS.get("enable_db", False) and DB_MODULE_AVAILABLE:
            try:
                new_items = db_save_new_items(candidates)
                print(f"DB: {len(new_items)} new items saved")
            except Exception as e:
                print("DB save error:", e)
                print(traceback.format_exc())

        if new_items:
            try:
                notifier.notify_new_items(new_items, bot=bot)
                print(f"Notified {len(new_items)} items")
            except Exception as e:
                print("Notify error:", e)
                print(traceback.format_exc())
        else:
            print("No new items to notify")

    except Exception as e:
        print("Collect_and_notify critical error:", e)
        print(traceback.format_exc())


# --------------------------
# Periodic collect
# --------------------------
def start_periodic_collect(app):
    interval = config.SETTINGS.get("collect_interval_seconds", 3600)

    def job():
        time.sleep(5)
        while True:
            try:
                print("Periodic collect triggered")
                try:
                    bot = app.bot
                except Exception:
                    bot = None
                collect_and_notify(bot)
            except Exception as e:
                print("Periodic collect error:", e)
                print(traceback.format_exc())
            time.sleep(interval)

    t = threading.Thread(target=job, daemon=True)
    t.start()


# --------------------------
# Main
# --------------------------
def main():
    token = config.TELEGRAM.get("bot_token") or os.getenv("BOT_TOKEN", "")
    if not token or str(token).strip() == "":
        print("BOT_TOKEN не задан в config.TELEGRAM или окружении. Выход.")
        return

    # optional masked preview for debug
    try:
        preview = token[:6] + "..." + token[-3:] if len(token) > 9 else token
        print("[INFO] BOT_TOKEN preview (masked):", preview)
    except Exception:
        pass

    # Start a minimal HTTP server so Render Web Service sees an open port
    start_http_server_in_background()

    app = ApplicationBuilder().token(token).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    print("Starting bot...")
    start_periodic_collect(app)
    app.run_polling()


if __name__ == "__main__":
    main()
