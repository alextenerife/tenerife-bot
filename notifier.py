# notifier.py
import os
from config import TELEGRAM
from telegram import Bot
import time

def _get_bot():
    token = os.getenv("BOT_TOKEN") or TELEGRAM.get("bot_token")
    chat_id = os.getenv("CHAT_ID") or TELEGRAM.get("chat_id")
    if not token or not chat_id:
        return None, None
    return Bot(token=token), chat_id

def send_message(text):
    bot, chat_id = _get_bot()
    if not bot:
        print("Telegram token/chat not set — сообщение не отправлено:")
        print(text)
        return False
    try:
        bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML', disable_web_page_preview=True)
        time.sleep(0.3)  # короткая пауза, чтобы не спамить API
        return True
    except Exception as e:
        print("Telegram send error:", e)
        return False

def notify_new_items(items):
    # items — список dict. отправляем по одному сообщению (или можно группировать)
    for it in items:
        title = it.get('title') or ""
        price = it.get('price') or "?"
        addr = it.get('address') or ""
        link = it.get('link') or ""
        src = it.get('source') or ""
        text = f"<b>{price}€</b> — {title}\n{addr}\nSource: {src}\n{link}"
        send_message(text)
