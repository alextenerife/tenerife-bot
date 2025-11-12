# notifier.py
import os
import time
from typing import List, Dict, Optional

import config

# Используем telegram.Bot напрямую (python-telegram-bot)
try:
    from telegram import Bot
except Exception:
    Bot = None

# Параметры отправки
BATCH_SIZE = 1          # сколько объявлений в одном сообщении (1 = по-одному)
PAUSE_BETWEEN_MSGS = 0.4  # секунда (ограничение на скорость отправки)

def _get_bot_and_chat() -> (Optional[object], Optional[str]):
    token = os.getenv("BOT_TOKEN") or config.TELEGRAM.get("bot_token")
    chat_id = os.getenv("CHAT_ID") or config.TELEGRAM.get("chat_id")
    if not token or not chat_id:
        return None, None
    if Bot is None:
        return None, chat_id
    return Bot(token=token), str(chat_id)

def _format_item(it: Dict) -> str:
    title = it.get("title") or ""
    price = it.get("price") or "?"
    addr = it.get("address") or ""
    src = it.get("source") or ""
    link = it.get("link") or ""
    # HTML-safe-ish formatting (we rely on Telegram parse_mode=HTML)
    return f"<b>{price} €</b> — {title}\n📍 {addr}\n🔗 {link}\nSource: {src}"

def send_message(text: str) -> bool:
    bot, chat_id = _get_bot_and_chat()
    if not bot:
        # Фаллбэк: печатаем в лог (удобно при локальном тестировании)
        print("[notify - fallback] MESSAGE:")
        print(text)
        return False
    try:
        bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", disable_web_page_preview=True)
        return True
    except Exception as e:
        print("Telegram send_message error:", e)
        return False

def notify_new_items(items: List[Dict]):
    """
    Отправляет новые объекты в Telegram.
    items — список dict с полями title, price, address, link, source.
    Отправка идёт пачками BATCH_SIZE.
    """
    if not items:
        return

    bot, chat_id = _get_bot_and_chat()
    if not bot:
        # Выводим в консоль, чтобы можно было увидеть, что нашёлся результат
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
            parts = []
            for it in batch:
                parts.append(_format_item(it))
            text = "\n\n".join(parts)
        ok = send_message(text)
        if not ok:
            # на ошибке — печатаем пакет и продолжаем (не ломаем цикл)
            print("Failed sending batch, continuing. Batch preview:")
            print(text[:1000])
        time.sleep(PAUSE_BETWEEN_MSGS)
        i += BATCH_SIZE
