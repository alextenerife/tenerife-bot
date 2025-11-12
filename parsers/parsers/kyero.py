# parsers/kyero.py
# Пример парсера объявлений с сайта Kyero.com (недвижимость на Тенерифе)

from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TenerifeBot/1.0)"}

def get_listings(max_pages=1):
    base_url = "https://www.kyero.com/en/tenerife-property-for-sale-0l47425"
    all_items = []

    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
        except Exception as e:
            print("Kyero error:", e)
            continue

        soup = BeautifulSoup(r.text, "lxml")
        cards = soup.select("article.card")
        for c in cards:
            title = c.select_one("h2")
            price_el = c.select_one(".card-price")
            link_el = c.select_one("a[href]")
            location_el = c.select_one(".card-location")
            price_text = price_el.get_text(strip=True) if price_el else ""
            price_num = int("".join(ch for ch in price_text if ch.isdigit())) if price_text else None

            all_items.append({
                "title": title.get_text(strip=True) if title else "No title",
                "price": price_num,
                "link": urljoin(base_url, link_el["href"]) if link_el else "",
                "address": location_el.get_text(strip=True) if location_el else "",
                "source": "Kyero"
            })
        time.sleep(1.2)

    return all_items
