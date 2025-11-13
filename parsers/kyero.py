# parsers/kyero.py
from bs4 import BeautifulSoup
from parsers._common import create_session, safe_get, polite_sleep

def parse_card(card):
    try:
        title_el = card.select_one("h3 a")
        title = title_el.get_text(strip=True) if title_el else ""
        link = title_el["href"] if title_el and title_el.has_attr("href") else ""
        price_el = card.select_one(".price")
        price = price_el.get_text(strip=True) if price_el else ""
        addr_el = card.select_one(".location")
        address = addr_el.get_text(strip=True) if addr_el else ""
        return {"title": title, "address": address, "price": price, "link": link}
    except Exception as e:
        print("kyero.parse_card error:", e)
        return None

def get_listings(start_url, max_pages=1, delay=1.5, source_name="Kyero"):
    session = create_session()
    out = []
    for p in range(1, max_pages+1):
        url = start_url if p == 1 else f"{start_url}?page={p}"
        html = safe_get(session, url)
        if not html:
            print(f"[{source_name}] fetch error for {url}")
            polite_sleep(delay, delay + 0.5)
            continue
        soup = BeautifulSoup(html, "lxml")
        # cards selector based on Kyero structure; may need tweak
        cards = soup.select(".property-listing, .property") or soup.select(".list-item")
        if not cards:
            # try alternate selector
            cards = soup.select("article")
        for c in cards:
            parsed = parse_card(c)
            if parsed:
                out.append(parsed)
        polite_sleep(delay, delay + 0.5)
    return out
