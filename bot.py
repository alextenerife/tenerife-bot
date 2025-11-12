# bot.py
import threading
import time
import importlib
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from config import TELEGRAM, SOURCES
from user_limits import user_price_limits
import config
import requests

# Простая утилита: покажем, что бот жив
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Land", callback_data='select_land')],
        [InlineKeyboardButton("Rural House", callback_data='select_rural_house')],
        [InlineKeyboardButton("Villa", callback_data='select_villa')],
        [InlineKeyboardButton("Finca", callback_data='select_finca')],
        [InlineKeyboardButton("Run now (collect)", callback_data='collect_now')]
    ]
    reply = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите тип для настройки лимита или запустите сбор:", reply_markup=reply)

# варианты лимитов
LIMIT_OPTIONS = {
    "land": [100000, 150000, 200000, 250000],
    "rural_house": [150000, 200000, 250000, 300000],
    "villa": [250000, 300000, 350000, 400000],
    "finca": [200000, 250000, 300000, 350000]
}

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    data = query.data

    if data == "collect_now":
        query.edit_message_text("Запуск сбора объявлений...")
        threading.Thread(target=collect_and_notify, args=(context,)).start()
        return

    if data.startswith("select_"):
        type_name = data.split("_",1)[1]
        keyboard = [[InlineKeyboardButton(f"≤{p} €", callback_data=f"set_{type_name}_{p}")] for p in LIMIT_OPTIONS[type_name]]
        reply = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(f"Выберите лимит цены для {type_name}:", reply_markup=reply)
        return

    if data.startswith("set_"):
        _, type_name, price = data.split("_")
        user_price_limits[type_name] = int(price)
        query.edit_message_text(f"Лимит для {type_name} установлен: {price} €")
        return

# --- Нотификатор (простая отправка в чат) ---
def notify_item(item, context: CallbackContext):
    bot = context.bot
    chat_id = TELEGRAM.get("chat_id")
    msg = f"🏠 <b>{item.get('title','(no title)')}</b>\n💶 {item.get('price','?')} €\n📍 {item.get('address','')}\n🔗 {item.get('link','')}"
    try:
        bot.send_message(chat_id=chat_id, text=msg, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        print("Notify error:", e)

# --- Функция сбора и фильтрации (упрощённая) ---
# Здесь мы импортируем парсеры по SOURCES и вызываем get_listings.
# При первом запуске парсеры могут быть шаблонными — заменяй селекторы в parsers/.
def collect_and_notify(context=None):
    print("Collect: starting")
    items = []
    for module_path, url, name in SOURCES:
        try:
            mod = importlib.import_module(module_path)
            if hasattr(mod, "get_listings"):
                try:
                    found = mod.get_listings(url, max_pages=1, delay=1.2, source_name=name)
                    if isinstance(found, list):
                        for it in found:
                            it.setdefault("source", name)
                        items.extend(found)
                        print(f"[{name}] collected {len(found)}")
                except Exception as e:
                    print(f"[{name}] parser runtime error:", e)
            else:
                print(f"[{name}] module has no get_listings()")
        except Exception as e:
            print(f"Import parser {module_path} failed:", e)

    # Простая фильтрация: тип/юг/цена — используем утилиты из utils (если есть), иначе очень простая
    from utils import detect_type, is_south, is_price_ok
    candidates = []
    for it in items:
        it['detected_type'] = detect_type(it)
        if not it['detected_type']:
            continue
        if not is_south(it):
            continue
        # учёт динамических лимитов
        it_price = it.get('price')
        try:
            pr = int(it_price) if it_price else None
            it['price'] = pr
        except:
            it['price'] = None
        if is_price_ok(it):
            candidates.append(it)

    print(f"Collect: candidates after filter = {len(candidates)}")
    # Отправляем уведомления (покоординатно — один за другим)
    if context:
        for c in candidates:
            notify_item(c, context)
    else:
        print("No context to send Telegram messages (running without bot context).")

# --- Периодический запуск (каждый час) ---
def start_periodic(updater, interval_seconds=3600):
    # запустим сбор в отдельном потоке каждые interval_seconds
    def job():
        while True:
            try:
                collect_and_notify(updater.dispatcher)
            except Exception as e:
                print("Periodic collect error:", e)
            time.sleep(interval_seconds)
    t = threading.Thread(target=job, daemon=True)
    t.start()

def main():
    token = TELEGRAM.get("bot_token")
    if not token:
        print("BOT_TOKEN не задан в переменных окружения.")
        return
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    print("Bot started")
    # Запускаем периодический сбор (каждый час)
    start_periodic(updater, interval_seconds=3600)
    updater.idle()

if __name__ == "__main__":
    main()
