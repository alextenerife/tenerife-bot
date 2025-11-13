# parsers/_common.py
import time
import random
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Набор User-Agent'ов — ротация уменьшает шанс простого блокирования
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:115.0) Gecko/20100101 Firefox/115.0",
]

BASE_HEADERS = {
    "Accept-Language": "en-GB,en;q=0.9,ru;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/",
}

def _choose_ua():
    return random.choice(UA_LIST)

def create_session():
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    s.mount("https://", adapter)
    s.mount("http://", adapter)

    headers = BASE_HEADERS.copy()
    headers["User-Agent"] = _choose_ua()
    s.headers.update(headers)

    # Поддержка прокси через переменные окружения (опционально)
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("http_proxy")
    https_proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    if http_proxy or https_proxy:
        proxies = {}
        if http_proxy:
            proxies["http"] = http_proxy
        if https_proxy:
            proxies["https"] = https_proxy
        s.proxies.update(proxies)
        print("[_common] Using proxies from env")

    return s

def safe_get(session, url, timeout=20):
    try:
        # иногда помогает менять UA между попытками
        session.headers["User-Agent"] = _choose_ua()
        r = session.get(url, timeout=timeout, allow_redirects=True)
        # логируем линк и статус для диагностики
        if r.status_code != 200:
            print(f"[fetch error] {r.status_code} for url: {url}")
        r.raise_for_status()
        return r
    except requests.HTTPError as e:
        print(f"[fetch error] {e} for url: {url}")
        return getattr(e, "response", None)
    except Exception as e:
        print(f"[fetch error] {e} for url: {url}")
        return None

def polite_sleep(min_s=0.8, max_s=1.8):
    time.sleep(random.uniform(min_s, max_s))
