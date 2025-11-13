# parsers/fotocasa.py
from bs4 import BeautifulSoup
from parsers._common import create_session, safe_get, polite_sleep

def parse_card(card):
    try:
        title_el = card.select_one(".re-Card-title, .re-card__title, h2")
        title = title_el.get_text(strip=True) if title_el else ""
        link_el = card.select_one("a")
        link = link_el["href"] if link_el and link_el.has_attr("href") else ""
        price_el = card.select_one(".re-Card-price, .re-card__price, .price")
        price = price_el.get_text(strip=True) if price_el else ""
        address_el = card.select_one(".re-Card-address, .re-card__address")
        address = address_el.get_text(strip=True) if address_el else ""
        return {"title": title, "address": address, "price": price, "link": link}
    except Exception as e:
        print("fotocasa.parse_card error:", e)
        return None

def get_listings(start_url, max_pages=1, delay=1.5, source_name="Fotocasa"):
    session = create_session()
    out = []
    for p in range(1, max_pages+1):
        if p == 1:
            url = start_url
        else:
            url = f"{start_url}?page={p}"
        html = safe_get(session, url)
        if not html:
            print(f"[{source_name}] fetch error for {url}")
            polite_sleep(delay, delay + 0.5)
            continue
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select(".re-Card, .re-card, .listing-item, article")
        if not cards:
            cards = soup.select("article")
        for c in cards:
            parsed = parse_card(c)
            if parsed:
                out.append(parsed)
        polite_sleep(delay, delay + 0.5)
    return out
