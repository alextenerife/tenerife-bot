# parsers/idealista.py
# Парсер недвижимости с Idealista (упрощённая версия)

import requests
from bs4 import BeautifulSoup
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TenerifeBot/1.0)"}

def get_listings(max_pages=1):
    base_url = "https://www.idealista.com/en/venta-viviendas/tenerife/"
    all_items = []

    for page in range(1, max_pages + 1):
        url = f"{base_url}pagina-{page}.htm"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
        except Exception as e:
            print("Idealista error:", e)
            continue

        soup = BeautifulSoup(r.text, "lxml")
        cards = soup.select(".item-info-container")
        for c in cards:
            title = c.select_one(".item-link")
            price_el = c.select_one(".item-price")
            addr = c.select_one(".item-detail-char")
            price_text = price_el.get_text(strip=True) if price_el else ""
            price_num = int("".join(ch for ch in price_text if ch.isdigit())) if price_text else None

            all_items.append({
                "title": title.get_text(strip=True) if title else "No title",
                "price": price_num,
                "link": "https://www.idealista.com" + title["href"] if title else "",
                "address": addr.get_text(strip=True) if addr else "",
                "source": "Idealista"
            })
        time.sleep(1.2)

    return all_items
