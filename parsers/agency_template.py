# parsers/agency_template.py
"""
Улучшённый универсальный шаблон-парсер для агентств.
- Пытается несколько популярных селекторов карточек/цены/ссылки/адреса
- Если в карточке нет цены — пробует перейти в detail page (если ссылка ведёт)
- Возвращает list[dict] с полями:
  title, price (int|None), link, address, description, source
- Логи пригодны для дальнейшей отладки по конкретному сайту
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TenerifeBot/1.0)"}

# наборы селекторов, которые пробуем (в порядке приоритета)
CARD_SELECTORS = [
    "article", ".property", ".listing", ".resultItem", ".propertyItem", ".card", ".item", ".listing-item",
    ".search-result", ".property-card", ".property-list-item"
]

TITLE_SELECTORS = [
    "h2", "h3", ".title", ".property-title", ".card-title", ".item-link", ".listing-title", "a[title]"
]

PRICE_SELECTORS = [
    ".price", ".property-price", ".card-price", ".listing-price", ".precio", ".price", ".item-price",
    ".re-Card-price", ".result-price"
]

ADDRESS_SELECTORS = [
    ".address", ".location", ".property-location", ".card-location", ".item-location", ".zone"
]

DESC_SELECTORS = [
    ".description", ".desc", ".property-description", ".card-text", "p"
]

LINK_SELECTORS = [
    "a[href]"
]

def _fetch(url, timeout=18):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r.text
    except Exception as e:
        # возврат None — обработаем в вызывающем коде
        print(f"[agency_template] fetch error for {url}: {e}")
        return None

def _parse_price(text):
    if not text:
        return None
    # remove non-digits
    s = re.sub(r'[^\d]', '', text)
    try:
        return int(s) if s else None
    except:
        return None

def _safe_text(el):
    try:
        return el.get_text(" ", strip=True)
    except:
        return ""

def _first_matching(soup, selectors):
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            return el
    return None

def parse_card(card, base_url):
    # card is a BeautifulSoup element for a property
    item = {"title":"", "price":None, "link":"", "address":"", "description":""}

    # title
    title_el = None
    for sel in TITLE_SELECTORS:
        title_el = card.select_one(sel)
        if title_el:
            break
    item["title"] = _safe_text(title_el) if title_el else ""

    # price: try many selectors
    price_el = None
    for sel in PRICE_SELECTORS:
        price_el = card.select_one(sel)
        if price_el:
            break
    price_text = _safe_text(price_el) if price_el else ""
    item["price"] = _parse_price(price_text) if price_text else None

    # link
    link_el = None
    for sel in LINK_SELECTORS:
        link_el = card.select_one(sel)
        if link_el and link_el.get("href"):
            break
    if link_el and link_el.get("href"):
        href = link_el.get("href")
        item["link"] = href if href.startswith("http") else urljoin(base_url, href)
    else:
        item["link"] = ""

    # address
    addr_el = None
    for sel in ADDRESS_SELECTORS:
        addr_el = card.select_one(sel)
        if addr_el:
            break
    item["address"] = _safe_text(addr_el) if addr_el else ""

    # description
    desc_el = None
    for sel in DESC_SELECTORS:
        desc_el = card.select_one(sel)
        if desc_el:
            break
    item["description"] = _safe_text(desc_el) if desc_el else ""

    return item

def parse_list_page(html, base_url):
    soup = BeautifulSoup(html, "lxml")
    items = []

    # пробуем набор селекторов карточек
    cards = []
    for sel in CARD_SELECTORS:
        found = soup.select(sel)
        if found and len(found) > 0:
            cards = found
            break

    # fallback — некоторые сайты рендерят списки как <a class="..."> карточки
    if not cards:
        cards = soup.select("a[href]")

    for c in cards:
        try:
            it = parse_card(c, base_url)
            # если в карточке нет названия и нет ссылки — пропускаем
            if not it["title"] and not it["link"]:
                continue
            # если нет цены в карточке, попытка перейти на detail page
            if it["price"] is None and it["link"]:
                # только для внутренних/внешних ссылок одного домена (короткий таймаут)
                parsed = urlparse(it["link"])
                if parsed.scheme and parsed.netloc:
                    detail_html = _fetch(it["link"])
                    if detail_html:
                        dsoup = BeautifulSoup(detail_html, "lxml")
                        # найти цену на детальной странице
                        price_el = _first_matching(dsoup, PRICE_SELECTORS)
                        if price_el:
                            it["price"] = _parse_price(_safe_text(price_el))
                        # также можно уточнить адрес/description
                        addr_el = _first_matching(dsoup, ADDRESS_SELECTORS)
                        if addr_el:
                            it["address"] = _safe_text(addr_el)
                        desc_el = _first_matching(dsoup, DESC_SELECTORS)
                        if desc_el:
                            it["description"] = _safe_text(desc_el)
                        # небольшая пауза — чтобы не перегружать сайт
                        time.sleep(0.6)
            items.append(it)
        except Exception as e:
            print("[agency_template] parse_card error:", e)
            continue
    return items

def get_listings(start_url, max_pages=1, delay=1.2, source_name="Agency"):
    results = []
    base_url = start_url
    for page in range(1, max_pages+1):
        # пробуем общую пагинацию: ?page=N или ?p=N или /page/N
        url = start_url
        if page > 1:
            if "?" in start_url:
                # try common query param
                if "page=" in start_url or "p=" in start_url:
                    url = start_url + f"&page={page}"
                else:
                    url = start_url + f"?page={page}"
            else:
                # naive append - может не работать для некоторых сайтов
                url = start_url.rstrip("/") + f"/?page={page}"

        html = _fetch(url)
        if not html:
            continue

        page_items = parse_list_page(html, base_url)
        # attach source name for each
        for it in page_items:
            it["source"] = source_name
        results.extend(page_items)
        time.sleep(delay)
    return results
