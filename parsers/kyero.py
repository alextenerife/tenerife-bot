# parsers/kyero.py
# Парсер для Kyero (упрощённый, устойчивый к разным вариантам верстки)
# Возвращает list[dict]: title, price (int|None), link, address, description, source

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

def parse_list_page(html, base_url, source_name="Kyero"):
    soup = BeautifulSoup(html, "lxml")
    items = []

    # Попытки разных селекторов, чтобы поймать карточки
    cards = soup.select("article.property, .propertyItem, .resultItem, article") 
    if not cards:
        # fallback: ссылки с рубрикой
        cards = soup.select("a[href*='/property/'], a[href*='/property/for-sale/']")

    for c in cards:
        # title
        title_el = c.select_one("h2, .title, .property-title, a[property-title]")
        if not title_el:
            # если карточка — ссылочный элемент
            title_el = c.select_one("a[href]")

        # price
        price_el = c.select_one(".price, .property-price, .card-price, .priceLarge")

        # link
        link_el = c.select_one("a[href]")
        link = ""
        if link_el:
            href = link_el.get("href")
            link = href if href.startswith("http") else urljoin(base_url, href)

        # address/location
        addr_el = c.select_one(".location, .property-location, .address, .card-location")
        # description (if available inside card)
        desc_el = c.select_one(".description, .prop-description, .card-text")

        title = _safe_get_text(title_el)
        price = _parse_price(_safe_get_text(price_el))
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

def get_listings(start_url, max_pages=1, delay=1.2, source_name="Kyero"):
    results = []
    base_url = start_url
    for page in range(1, max_pages+1):
        # Kyero pagination pattern can vary; try common patterns
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
            print(f"[Kyero] fetch error: {e} (url: {url})")
            break
        try:
            page_items = parse_list_page(resp.text, base_url, source_name=source_name)
            results.extend(page_items)
        except Exception as e:
            print(f"[Kyero] parse error: {e}")
        time.sleep(delay)
    return results
