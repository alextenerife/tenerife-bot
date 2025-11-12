# notifier.py
import os
import time
from typing import List, Dict, Optional

import config

# Попытка импортировать telegram.Bot
try:
    from telegram import Bot
except Exception:
    Bot = None

BATCH_SIZE = 1
PAUSE_BETWEEN_MSGS = 0.4

def _format_item(it: Dict) -> str:
    title = it.get("title") or ""
    price = it.get("price") or "?"
    addr = it.get("address") or ""
    src = it.get("source") or ""
    link = it.get("link") or ""
    return f"<b>{price} €</b> — {title}\n📍 {addr}\n🔗 {link}\nSource: {src}"

def _get_bot_from_env() -> Optional[object]:
    token = os.getenv("BOT_TOKEN") or config.TELEGRAM.get("bot_token")
    if not token or Bot is None:
        return None
    try:
        return Bot(token=token)
    except Exception as e:
        print("Notifier: failed to init Bot from env:", e)
        return None

def _send_with_bot(bot_obj, chat_id: str, text: str) -> bool:
    try:
        bot_obj.send_message(chat_id=chat_id, text=text, parse_mode="HTML", disable_web_page_preview=True)
        return True
    except Exception as e:
        print("Notifier: telegram send error:", e)
        return False

def send_message_via(bot_obj, chat_id: str, text: str) -> bool:
    if bot_obj:
        return _send_with_bot(bot_obj, chat_id, text)
    # fallback: try to create bot from env
    fallback_bot = _get_bot_from_env()
    if fallback_bot:
        return _send_with_bot(fallback_bot, chat_id, text)
    # final fallback: print to console
    print("[notify fallback] ", text)
    return False

def notify_new_items(items: List[Dict], bot=None):
    """
    Отправляет новые объекты. Если bot (telegram.Bot) передан — используется он (рекомендуется).
    Если bot не передан — пытается создать Bot из переменных окружения.
    """
    if not items:
        return

    chat_id = os.getenv("CHAT_ID") or config.TELEGRAM.get("chat_id")
    if not chat_id:
        # печатаем в консоль как fallback
        for it in items:
            print(_format_item(it))
        return

    # отправляем пачками
    i = 0
    while i < len(items):
        batch = items[i:i+BATCH_SIZE]
        if BATCH_SIZE == 1:
            text = _format_item(batch[0])
        else:
            text = "\n\n".join(_format_item(it) for it in batch)
        ok = send_message_via(bot, chat_id, text)
        if not ok:
            print("Notifier: failed to send message (see log).")
        time.sleep(PAUSE_BETWEEN_MSGS)
        i += BATCH_SIZE
