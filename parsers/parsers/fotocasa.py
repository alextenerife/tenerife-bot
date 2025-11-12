# parsers/fotocasa.py
# Простой парсер для Fotocasa (версия-стартер).
# Выполняет запрос start_url, извлекает карточки объявлений и возвращает список dict.
#
# Замечание: селекторы примерные и могут требовать корректировки под реальную верстку.
# Если что-то не собирается — открой страницу в браузере -> DevTools -> найди реальные классы.

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import re

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TenerifeBot/1.0)"}

def _parse_price(text):
    if not text:
        return None
    # Оставляем цифры
    s = re.sub(r'[^\d]', '', text)
    try:
        return int(s) if s else None
    except:
        return None

def parse_list_page(html, base_url, source_name="Fotocasa"):
    soup = BeautifulSoup(html, "lxml")
    items = []

    # Примерный селектор карточек — возможно потребуется изменить
    cards = soup.select("article, .re-Card, .re-Searchresult") or soup.select(".listing")
    for c in cards:
        # Попробуем несколько вариантов селекторов, чтобы поймать максимум
        title_el = c.select_one("h2, .re-Card-title, .card-title, a")
        price_el = c.select_one(".re-Card-price, .re-Card-price > span, .price, .card-price")
        link_el = c.select_one("a[href]")
        addr_el = c.select_one(".re-Card-address, .address, .card-location, .re-Card-location")

        title = title_el.get_text(strip=True) if title_el else ""
        price_text = price_el.get_text(" ", strip=True) if price_el else ""
        price = _parse_price(price_text)
        link = ""
        if link_el and link_el.get("href"):
            link = link_el.get("href")
            if not link.startswith("http"):
                link = urljoin(base_url, link)
        address = addr_el.get_text(strip=True) if addr_el else ""

        items.append({
            "title": title,
            "price": price,
            "link": link,
            "address": address,
            "description": "",
            "source": source_name
        })
    return items

def get_listings(start_url, max_pages=1, delay=1.2, source_name="Fotocasa"):
    """
    Интерфейс, совместимый с bot.py:
    get_listings(start_url, max_pages=..., delay=..., source_name=...)
    Возвращает список объектов: dict с ключами title, price (int|None), link, address, description, source
    """
    results = []
    base_url = start_url
    for page in range(1, max_pages+1):
        # Формируем URL для страницы пагинации — для Fotocasa это может быть разным.
        # Простая попытка: добавить query param ?page=...
        url = start_url
        if page > 1:
            if "?" in start_url:
                url = f"{start_url}&page={page}"
            else:
                url = f"{start_url}?page={page}"

        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
        except Exception as e:
            print(f"[Fotocasa] fetch error: {e} (url: {url})")
            break

        try:
            page_items = parse_list_page(r.text, base_url, source_name=source_name)
            results.extend(page_items)
        except Exception as e:
            print(f"[Fotocasa] parse error: {e}")
        time.sleep(delay)
    return results
