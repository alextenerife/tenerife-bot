# db.py
import sqlite3
import os
import re
from datetime import datetime
from difflib import SequenceMatcher

DB_PATH = os.getenv("DB_PATH", "props.db")
CREATE_SQL = """
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    link TEXT UNIQUE,
    title TEXT,
    price INTEGER,
    address TEXT,
    source TEXT,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.execute(CREATE_SQL)
    return conn

def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r'[^0-9a-zа-яё\u00C0-\u017F\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def is_duplicate(conn: sqlite3.Connection, link: str, title: str, address: str, threshold: float = 0.86) -> bool:
    cur = conn.cursor()
    # 1) по ссылке
    if link:
        cur.execute("SELECT 1 FROM listings WHERE link = ? LIMIT 1", (link,))
        if cur.fetchone():
            return True
    # 2) по сходству title+address
    key = normalize_text(" ".join(filter(None, [title, address])))
    if not key:
        return False
    cur.execute("SELECT title, address FROM listings")
    rows = cur.fetchall()
    for rtitle, raddr in rows:
        existing = normalize_text(" ".join(filter(None, [rtitle, raddr])))
        if not existing:
            continue
        if similar(existing, key) >= threshold:
            return True
    return False

def save_new_items(items):
    """
    Save items to SQLite.
    items: list of dicts with keys link, title, price, address, source
    Returns list of items that were inserted (new).
    """
    if not items:
        return []

    conn = get_conn()
    cur = conn.cursor()
    new_inserted = []

    for it in items:
        link = it.get("link") or ""
        title = it.get("title") or ""
        address = it.get("address") or ""
        price = None
        try:
            price = int(it.get("price")) if it.get("price") not in (None, "") else None
        except:
            price = None

        try:
            if is_duplicate(conn, link, title, address):
                continue
            cur.execute(
                "INSERT INTO listings (link, title, price, address, source, first_seen) VALUES (?, ?, ?, ?, ?, ?)",
                (link, title, price, address, it.get("source"), datetime.utcnow())
            )
            conn.commit()
            new_inserted.append(it)
        except sqlite3.IntegrityError:
            # возможно race condition — уже вставлено, пропускаем
            continue
        except Exception as e:
            print("DB insert error:", e)
            continue

    conn.close()
    return new_inserted
