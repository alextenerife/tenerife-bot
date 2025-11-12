# parsers/idealista.py
# Простой устойчивый парсер для Idealista (списочные страницы)
# Возвращает list[dict] с title, price (int|None), link, address, description, source

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
    try:
        return int(s) if s else None
    except:
        return None

def _safe_get_text(el):
    return el.get_text(" ", strip=True) if el else ""

def parse_list_page(html, base_url, source_name="Idealista"):
    soup = BeautifulSoup(html, "lxml")
    items = []

    # Часто карточки имеют класс "item" или "article"
    cards = soup.select("article, .item, .item-info-container, .ad") 
    if not cards:
        cards = soup.select("a[href*='/inmueble/'], a[href*='/venta-viviendas/']")

    for c in cards:
        # title
        title_el = c.select_one("a.item-link, a[href].item-link, h2, .item-link, .title")
        # price
        price_el = c.select_one(".item-price, .precio, .price, .price-big, .price")
        # link
        link_el = c.select_one("a[href]")
        link = ""
        if link_el:
            href = link_el.get("href")
            link = href if href.startswith("http") else urljoin(base_url, href)
        # address / district
        addr_el = c.select_one(".item-detail, .item-detail-char, .zone, .item-location, .detail")
        desc_el = c.select_one(".item-description, .description, p")

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

def get_listings(start_url, max_pages=1, delay=1.2, source_name="Idealista"):
    results = []
    base_url = "https://www.idealista.com"
    for page in range(1, max_pages+1):
        # Common Idealista pagination: 'pagina-N.htm' or '?orden=...&pagina=N'
        url = start_url
        if page > 1:
            if "pagina" in start_url or "pagina-" in start_url:
                # try to append pagina-N
                if start_url.endswith("/"):
                    url = f"{start_url}pagina-{page}.htm"
                else:
                    url = f"{start_url}pagina-{page}.htm"
            else:
                if "?" in start_url:
                    url = f"{start_url}&pagina={page}"
                else:
                    url = f"{start_url}?pagina={page}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"[Idealista] fetch error: {e} (url: {url})")
            break
        try:
            page_items = parse_list_page(resp.text, base_url, source_name=source_name)
            results.extend(page_items)
        except Exception as e:
            print(f"[Idealista] parse error: {e}")
        time.sleep(delay)
    return results
