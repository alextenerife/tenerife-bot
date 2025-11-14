# show_debug.py — печатает debug_all_items.csv (первые N строк)
import csv, os, sys

path = os.path.join("outputs", "debug_all_items.csv")
if not os.path.exists(path):
    print("Debug CSV not found at", path)
    sys.exit(1)

with open(path, newline="", encoding="utf-8") as f:
    rdr = csv.DictReader(f)
    for i, row in enumerate(rdr):
        if i >= 50:
            break
        print(f"ROW {i}: source={row.get('source')}, title={row.get('title')[:80]!r}")
        print(f"      addr={row.get('address')[:80]!r}, price_raw={row.get('price_raw')!r}, price_norm={row.get('price_norm')!r}")
        print(f"      detected_type={row.get('detected_type')!r}, is_south={row.get('is_south')!r}, explain={row.get('explain')!r}")
        print("-" * 80)
