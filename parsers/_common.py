# parsers/_common.py
# Общая логика HTTP считывания для парсеров: сессия, заголовки, retry и safe_get.

import time
import random
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9,ru;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}

def create_session():
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.headers.update(HEADERS)
    return s

def safe_get(session, url, timeout=15):
    try:
        r = session.get(url, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r.text
    except requests.HTTPError as e:
        print(f"[fetch error] {e} for url: {url}")
        return None
    except Exception as e:
        print(f"[fetch error] {e} for url: {url}")
        return None

def polite_sleep(min_s=0.8, max_s=1.8):
    time.sleep(random.uniform(min_s, max_s))
