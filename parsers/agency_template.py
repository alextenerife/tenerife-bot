# parsers/agency_template.py
# Простой HTML-парсер-шаблон — адаптируй селекторы под конкретный сайт

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TenerifeBot/1.0)"}

def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.text

def parse_list_page(html, base_url, source_name="Agency"):
    soup = BeautifulSoup(html, "lxml")
    items = []
    # ВОТ ЭТОТ СЕЛЕКТОР нужно заменить под структуру конкретного сайта
    cards = soup.select(".listing, .property, article")
    for c in cards:
        title = c.select_one("h2, .title")
        price = c.select_one(".price, .value")
        link_el = c.select_one("a[href]")
        addr = c.select_one(".address, .location")
        link = urljoin(base_url, link_el['href']) if link_el else base_url
        price_text = price.get_text(strip=True) if price else ""
        # убираем нечисловые символы
        price_num = int(''.join(ch for ch in price_text if ch.isdigit())) if price_text else None
        items.append({
            "title": title.get_text(strip=True) if title else "",
            "price": price_num,
            "link": link,
            "address": addr.get_text(strip=True) if addr else "",
            "description": ""
        })
    return items

def get_listings(start_url, max_pages=1, delay=1.2, source_name="Agency"):
    try:
        html = fetch(start_url)
        return parse_list_page(html, start_url, source_name=source_name)
    except Exception as e:
        print("Agency parser error:", e)
        return []
