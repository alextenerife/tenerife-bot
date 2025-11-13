# parsers/idealista.py
from bs4 import BeautifulSoup
from parsers._common import create_session, safe_get, polite_sleep

def parse_card(card):
    try:
        title_el = card.select_one("a.item-link, a > span")
        title = title_el.get_text(strip=True) if title_el else card.get_text(strip=True)[:120]
        link_el = card.select_one("a[itemprop='url'], a")
        link = link_el["href"] if link_el and link_el.has_attr("href") else ""
        price_el = card.select_one(".price, .precio, .item-price")
        price = price_el.get_text(strip=True) if price_el else ""
        address_el = card.select_one(".item-address, .location, .address")
        address = address_el.get_text(strip=True) if address_el else ""
        return {"title": title, "address": address, "price": price, "link": link}
    except Exception as e:
        print("idealista.parse_card error:", e)
        return None

def get_listings(start_url, max_pages=1, delay=1.5, source_name="Idealista"):
    session = create_session()
    out = []
    for p in range(1, max_pages+1):
        # Idealista pagination often via page number in query; tweak as needed
        url = start_url if p == 1 else f"{start_url}?ordenado-por=fecha&page={p}"
        html = safe_get(session, url)
        if not html:
            print(f"[{source_name}] fetch error for {url}")
            polite_sleep(delay, delay + 0.5)
            continue
        soup = BeautifulSoup(html, "lxml")
        # try several selectors
        cards = soup.select(".item, .ad, .offer-item, article")
        if not cards:
            cards = soup.select("article")
        for c in cards:
            parsed = parse_card(c)
            if parsed:
                out.append(parsed)
        polite_sleep(delay, delay + 0.5)
    return out
