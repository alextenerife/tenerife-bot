# parsers/agency_vym_canarias.py
from .agency_template import get_listings as base_get_listings

START_URL = "https://tenerifecenter.com/"
SOURCE_NAME = "VYM Canarias"

def get_listings(start_url=None, max_pages=1, delay=1.2, source_name=None):
    url = start_url or START_URL
    name = source_name or SOURCE_NAME
    return base_get_listings(url, max_pages=max_pages, delay=delay, source_name=name)
