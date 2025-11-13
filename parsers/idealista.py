# parsers/idealista.py (diagnostic)
from bs4 import BeautifulSoup
from parsers._common import create_session, safe_get, polite_sleep

DEFAULT_URL = "https://www.idealista.com/en/venta-viviendas/tenerife/"

def get_listings(start_url=None, max_pages=1, delay=1.5, source_name="Idealista"):
    session = create_session()
    out = []
    if not start_url:
        start_url = DEFAULT_URL

    for p in range(1, max_pages+1):
        url = start_url if p == 1 else f"{start_url}?ordenado-por=fecha&page={p}"
        resp = safe_get(session, url)
        if resp is None:
            print(f"[{source_name}] fetch returned None for {url}")
            polite_sleep(delay, delay + 0.5)
            continue

        status = getattr(resp, "status_code", None)
        print(f"[{source_name}] status={status} for {url}")
        headers = getattr(resp, "headers", {}) or {}
        for h in ("Server", "Content-Type", "Set-Cookie"):
            if headers.get(h):
                print(f"[{source_name}] header {h}: {headers.get(h)}")
        try:
            text = resp.text or ""
            snippet = text[:2000].replace("\n", " ")
        except Exception:
            snippet = "(no text)"
        print(f"[{source_name}] body snippet (first 2000 chars):\n{snippet}")

        if status != 200:
            print(f"[{source_name}] fetch error for {url}")
            polite_sleep(delay, delay + 0.5)
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select(".item, .ad, .offer-item, article")
        if not cards:
            print(f"[{source_name}] no cards found (maybe JS or selectors changed)")
        for c in cards[:50]:
            title_el = c.select_one("a.item-link, a > span")
            title = title_el.get_text(strip=True) if title_el else c.get_text(strip=True)[:120]
            price_el = c.select_one(".price, .precio, .item-price")
            price = price_el.get_text(strip=True) if price_el else ""
            link_el = c.select_one("a[itemprop='url'], a")
            link = link_el["href"] if link_el and link_el.has_attr("href") else ""
            out.append({"title": title, "address": "", "price": price, "link": link, "source": source_name})
        polite_sleep(delay, delay + 0.5)
    return out
