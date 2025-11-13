# parsers/kyero.py  (diagnostic)
from bs4 import BeautifulSoup
from parsers._common import create_session, safe_get, polite_sleep

DEFAULT_URL = "https://www.kyero.com/en/property-for-sale/canary-islands/tenerife"

def get_listings(start_url=None, max_pages=1, delay=1.5, source_name="Kyero"):
    session = create_session()
    out = []
    if not start_url:
        start_url = DEFAULT_URL

    for p in range(1, max_pages+1):
        url = start_url if p == 1 else f"{start_url}?page={p}"
        resp = safe_get(session, url)
        # safe_get теперь возвращает Response (on success) or Response (with error code) or None
        if resp is None:
            print(f"[{source_name}] fetch returned None for {url}")
            polite_sleep(delay, delay + 0.5)
            continue

        # если это объект Response — логируем статус и часть тела
        try:
            status = getattr(resp, "status_code", None)
            print(f"[{source_name}] status={status} for {url}")
            headers = getattr(resp, "headers", {}) or {}
            # Покажем несколько заголовков (Server, Content-Type, Set-Cookie если есть)
            for h in ("Server", "Content-Type", "Set-Cookie"):
                if headers.get(h):
                    print(f"[{source_name}] header {h}: {headers.get(h)}")
            body_snippet = ""
            try:
                text = resp.text or ""
                body_snippet = text[:2000].replace("\n"," ")
            except Exception:
                body_snippet = "(no text)"
            print(f"[{source_name}] body snippet (first 2000 chars):\n{body_snippet}")
        except Exception as e:
            print(f"[{source_name}] diagnostic logging error: {e}")

        # Если статус !=200 — пропускаем парсинг; иначе парсим как обычно
        if getattr(resp, "status_code", None) != 200:
            print(f"[{source_name}] fetch error for {url}")
            polite_sleep(delay, delay + 0.5)
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        # Попытка парсинга — базовый selector, но основное сейчас — диагностика
        cards = soup.select(".property-listing, .property, article, .listing-item")
        if not cards:
            print(f"[{source_name}] no cards found (possibly JS or different selectors)")
        for c in cards[:50]:
            title_el = c.select_one("h3 a, a")
            title = title_el.get_text(strip=True) if title_el else ""
            price_el = c.select_one(".price, .property-price")
            price = price_el.get_text(strip=True) if price_el else ""
            link = title_el["href"] if title_el and title_el.has_attr("href") else ""
            out.append({"title": title, "address": "", "price": price, "link": link, "source": source_name})
        polite_sleep(delay, delay + 0.5)

    return out
