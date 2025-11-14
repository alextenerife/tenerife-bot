# parsers/fotocasa.py
# Парсер для Fotocasa — пытается читать JSON-LD, иначе парсит HTML-карточки.
# Зависит от: parsers._common.create_session, parsers._common.safe_get, parsers._common.polite_sleep

from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin

from parsers._common import create_session, safe_get, polite_sleep

DEFAULT_URL = "https://www.fotocasa.es/en/buy/homes/santa-cruz-de-tenerife-province/all-zones/l"
SOURCE_DOMAIN = "https://www.fotocasa.es"

PRICE_CLEAN_RE = re.compile(r"[^\d]")

def _clean_price_to_int(price_text):
    """
    Попытка извлечь цену в EUR из текстовой строки.
    Примеры входа: "€250,000", "250.000 €", "From €250,000", "250.000", "250000€"
    Возвращает int или None.
    """
    if not price_text:
        return None
    s = str(price_text)
    # Удалим non-breaking spaces и пр.
    s = s.replace('\xa0', '').replace('\u202f', '').strip()
    # Заменяем запятые в дробных частях на точку, но сначала уберём тысячные разделители
    # Уберём всё кроме цифр
    digits = "".join(ch for ch in s if ch.isdigit())
    if not digits:
        return None
    try:
        return int(digits)
    except Exception:
        return None

def _abs_link(href):
    if not href:
        return ""
    if href.startswith("http://") or href.startswith("https://"):
        return href
    # Относительный путь — делаем абсолютным для fotocasa
    return urljoin(SOURCE_DOMAIN, href)

def _try_parse_json_ld(soup):
    out = []
    scripts = soup.select("script[type='application/ld+json']")
    if not scripts:
        return out
    for tag in scripts:
        text = (tag.string or "").strip()
        if not text:
            continue
        try:
            data = json.loads(text)
        except Exception:
            # иногда в теге несколько JSON объектов или мусор — попробуем аккуратно
            try:
                # попытка выделить JSON внутри
                start = text.find("{")
                end = text.rfind("}") + 1
                data = json.loads(text[start:end])
            except Exception:
                continue
        # standard JSON-LD may be dict or list
        items = []
        if isinstance(data, dict):
            # возможно @graph или itemListElement
            if "@graph" in data and isinstance(data["@graph"], list):
                items = data["@graph"]
            elif "itemListElement" in data and isinstance(data["itemListElement"], list):
                # itemListElement may be list of {"item": {...}} or direct
                items = []
                for el in data["itemListElement"]:
                    if isinstance(el, dict):
                        if "item" in el and isinstance(el["item"], dict):
                            items.append(el["item"])
                        else:
                            items.append(el)
            else:
                items = [data]
        elif isinstance(data, list):
            items = data
        # normalize some item shapes (Offer, Residence, Product, ListItem)
        for el in items:
            if not isinstance(el, dict):
                continue
            title = el.get("name") or el.get("headline") or ""
            link = el.get("url") or el.get("@id") or ""
            price = ""
            # price may be inside offers
            offers = el.get("offers") or el.get("priceSpecification") or {}
            if isinstance(offers, dict):
                price = offers.get("price") or offers.get("priceCurrency") or ""
            elif isinstance(offers, str):
                price = offers
            # if el describes an ItemList, it may contain itemListElement as nested items
            out.append({
                "title": title,
                "address": el.get("address", "") if isinstance(el.get("address", ""), str) else "",
                "price": price,
                "link": link,
            })
    return out

def _parse_html_cards(soup):
    out = []
    # Попробуем несколько вероятных селекторов карточек
    card_selectors = [
        ".re-Card", ".re-card", ".fc-Card", ".listing-item", ".offer-item", "article", ".Card"
    ]
    cards = []
    for sel in card_selectors:
        cards = soup.select(sel)
        if cards:
            break
    # fallback: выбирать элементы с ссылками и ценой
    if not cards:
        cards = soup.select("a")
    for c in cards:
        try:
            # Title
            title = ""
            t = None
            for sel in (".re-Card-title", ".re-card__title", ".card-title", "h2", "h3", ".title"):
                t = c.select_one(sel)
                if t:
                    title = t.get_text(strip=True)
                    break
            if not title:
                # try anchor text
                a = c.select_one("a")
                if a:
                    title = a.get_text(strip=True)[:180]

            # Price
            price = ""
            for sel in (".re-Card-price", ".re-card__price", ".price", ".Card-price", ".fc-price"):
                p = c.select_one(sel)
                if p:
                    price = p.get_text(strip=True)
                    break

            # Link
            link = ""
            a = c.select_one("a")
            if a and a.has_attr("href"):
                link = a["href"]

            # Address (if available)
            address = ""
            for sel in (".re-Card-location", ".re-card__address", ".address", ".location"):
                ad = c.select_one(sel)
                if ad:
                    address = ad.get_text(strip=True)
                    break

            # minimal sanity: skip very short items without title and link
            if not title and not link:
                continue

            out.append({
                "title": title,
                "address": address,
                "price": price,
                "link": link
            })
        except Exception:
            continue
    return out

def get_listings(start_url=None, max_pages=1, delay=1.5, source_name="Fotocasa"):
    """
    Возвращает список dict:
    {"title":..., "address":..., "price": <raw string>, "price_eur": <int or None>, "link":..., "source": source_name}
    """
    session = create_session()
    out = []
    if not start_url:
        start_url = DEFAULT_URL

    for p in range(1, max_pages + 1):
        if p == 1:
            url = start_url
        else:
            # Fotocasa pagination: часто uses ?page=N or /pagina-N — this works as a common fallback
            if "?" in start_url:
                url = f"{start_url}&page={p}"
            else:
                url = f"{start_url}?page={p}"

        resp = safe_get(session, url)
        if resp is None or getattr(resp, "status_code", None) != 200:
            print(f"[{source_name}] fetch error for {url}")
            polite_sleep(delay, delay + 0.5)
            continue

        text = resp.text or ""
        soup = BeautifulSoup(text, "lxml")

        # 1) Попытка JSON-LD
        json_items = _try_parse_json_ld(soup)
        if json_items:
            for it in json_items:
                title = it.get("title") or it.get("name") or ""
                link = it.get("link") or ""
                price_raw = it.get("price") or ""
                # make link absolute
                link = _abs_link(link)
                price_eur = _clean_price_to_int(price_raw)
                out.append({
                    "title": title,
                    "address": it.get("address", "") or "",
                    "price": price_raw,
                    "price_eur": price_eur,
                    "link": link,
                    "source": source_name
                })
            print(f"[{source_name}] parsed {len(json_items)} items from JSON-LD (page {p})")
        else:
            # 2) HTML parsing
            html_items = _parse_html_cards(soup)
            # Normalize and make links absolute
            for it in html_items:
                title = it.get("title","")
                address = it.get("address","")
                price_raw = it.get("price","")
                link = _abs_link(it.get("link",""))
                price_eur = _clean_price_to_int(price_raw)
                out.append({
                    "title": title,
                    "address": address,
                    "price": price_raw,
                    "price_eur": price_eur,
                    "link": link,
                    "source": source_name
                })
            print(f"[{source_name}] parsed {len(html_items)} items from HTML (page {p})")

        polite_sleep(delay, delay + 0.5)

    # de-duplicate by link+title simple key
    seen = set()
    deduped = []
    for it in out:
        key = (it.get("link",""), (it.get("title") or "")[:120])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(it)

    return deduped
