# parsers/fotocasa.py
# Парсер-стартер для Fotocasa — возвращает список объявлений с основных полей

import re
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TenerifeBot/1.0)"}

def _parse_price(text):
    if not text:
        return None
    s = re.sub(r'[^\d]', '', text)
    return int(s) if s else None

def _safe_get_text(el):
    return el.get_text(" ", strip=True) if el else ""

def parse_list_page(html, base_url, source_name="Fotocasa"):
    soup = BeautifulSoup(html, "lxml")
    items = []

    # примерные селекторы карточек
    cards = soup.select("article, .re-Card, .re-Searchresult, .listing")
    if not cards:
        # попробовать селектор ссылок
        cards = soup.select("a[href*='/es/comprar/viviendas/'], a[href*='/venta/']")

    for c in cards:
        title_el = c.select_one("h2, .re-Card-title, .card-title, a")
        price_el = c.select_one(".re-Card-price, .price, .card-price, .re-Card-price > span")
        link_el = c.select_one("a[href]")
        addr_el = c.select_one(".re-Card-address, .address, .card-location, .re-Card-location")
        desc_el = c.select_one(".re-Card-description, .description, p")

        title = _safe_get_text(title_el)
        price = _parse_price(_safe_get_text(price_el))
        link = ""
        if link_el and link_el.get("href"):
            href = link_el.get("href")
            link = href if href.startswith("http") else urljoin(base_url, href)
        address = _safe_get_text(addr_el)
        description = _safe_get_text(desc_el)

        items.append({
            "title": title or "No title",
            "price": price,
            "link": link,
            "address": address,
            "description": description,
            "source": source_name
        })
    return items

def get_listings(start_url, max_pages=1, delay=1.2, source_name="Fotocasa"):
    results = []
    base_url = start_url
    for page in range(1, max_pages+1):
        url = start_url
        if page > 1:
            if "?" in start_url:
                url = f"{start_url}&page={page}"
            else:
                url = f"{start_url}?page={page}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"[Fotocasa] fetch error: {e} (url: {url})")
            break
        try:
            page_items = parse_list_page(resp.text, base_url, source_name=source_name)
            results.extend(page_items)
        except Exception as e:
            print(f"[Fotocasa] parse error: {e}")
        time.sleep(delay)
    return results
