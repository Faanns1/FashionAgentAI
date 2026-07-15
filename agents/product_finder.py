import time
import requests
import re
from agents.state import FashionState
from config import RAPIDAPI_KEY, RAPIDAPI_HOST, PRODUCT_SEARCH_URL, MAX_PRODUCTS_PER_SEARCH


def parse_price_to_number(price_str: str) -> float:
    """Convert string harga ke float.
    Handle: 'Rp 150,000' / 'Rp150.000' / 'Rp\xa0150.000'
    """
    if not price_str:
        return 0
    cleaned = re.sub(r'[^\d.,]', '', str(price_str))
    if not cleaned:
        return 0
    if '.' in cleaned:
        parts = cleaned.split('.')
        if len(parts[-1]) == 3:
            cleaned = cleaned.replace('.', '')
    if ',' in cleaned:
        parts = cleaned.split(',')
        if len(parts[-1]) == 3:
            cleaned = cleaned.replace(',', '')
        else:
            cleaned = cleaned.replace(',', '.')
    try:
        return float(cleaned)
    except ValueError:
        return 0


def parse_budget_allocation(budget_result: str, total_budget: float) -> dict:
    """Parse output Budget Agent → dict alokasi per kategori."""
    allocation = {}
    category_map = {
        "sepatu": ["sepatu"],
        "atasan": ["atasan"],
        "bawahan": ["bawahan"],
        "outer": ["outer"],
        "aksesoris": ["aksesoris"],
    }

    lines = budget_result.split("\n")
    for line in lines:
        line_lower = line.lower()
        for category, keywords in category_map.items():
            if category in allocation:
                continue
            for kw in keywords:
                if kw in line_lower:
                    cleaned_line = re.sub(r'[Rr][Pp]', '', line)
                    cleaned_line = cleaned_line.replace('\xa0', ' ')
                    matches = re.findall(r'\d{1,3}(?:[.,]\d{3})+', cleaned_line)
                    for m in matches:
                        num_clean = m.replace('.', '').replace(',', '')
                        try:
                            num = float(num_clean)
                            if 10_000 <= num <= total_budget:
                                allocation[category] = num
                                print(f"✅ Budget parsed: {category} = Rp{num:,.0f}")
                                break
                        except ValueError:
                            continue
                    break

    # Fallback persentase default
    defaults = {
        "sepatu": 0.30,
        "atasan": 0.24,
        "bawahan": 0.20,
        "outer": 0.16,
        "aksesoris": 0.10,
    }
    for cat, pct in defaults.items():
        if cat not in allocation:
            allocation[cat] = total_budget * pct
            print(f"⚠️ Budget fallback: {cat} = Rp{allocation[cat]:,.0f} ({pct*100:.0f}%)")

    return allocation


def search_google_shopping(query: str, max_price: float = None, max_results: int = 1) -> list[dict]:
    """Fetch produk dari Google Shopping API dengan retry dan budget filter."""
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    params = {
        "q": query,
        "country": "id",
        "language": "id",
        "limit": max_results * 3,
    }

    for attempt in range(3):  # Retry max 3x
        try:
            response = requests.get(
                PRODUCT_SEARCH_URL,
                headers=headers,
                params=params,
                timeout=30,  # Naikkan timeout
            )

            if response.status_code == 429:
                print(f"Rate limit, tunggu 3 detik... (attempt {attempt+1})")
                time.sleep(3)
                continue

            response.raise_for_status()
            data = response.json()
            items = data.get("data", {}).get("products", [])

            if not items:
                return []

            # Filter berdasarkan budget
            filtered = []
            all_parsed = []

            for item in items:
                raw_price = item.get("price", "0")
                price_num = parse_price_to_number(raw_price)
                photos = item.get("product_photos", [])

                product = {
                    "nama": item.get("product_title", "Unknown"),
                    "harga": item.get("price", "N/A"),
                    "harga_num": price_num,
                    "rating": item.get("product_rating", "-"),
                    "gambar": photos[0] if photos else "",
                    "link": item.get("product_page_url", ""),
                    "toko": item.get("store_name", "Unknown"),
                    "query": query,
                }

                all_parsed.append(product)

                if max_price and price_num > 0 and price_num > max_price:
                    print(f"  Skip '{item.get('product_title','')[:30]}' Rp{price_num:,.0f} > budget Rp{max_price:,.0f}")
                    continue

                filtered.append(product)
                if len(filtered) >= max_results:
                    break

            if filtered:
                return filtered

            # Fallback: semua over budget → return yang PALING DEKAT dengan budget
            if all_parsed:
                # Sort by selisih harga dengan budget (terkecil dulu)
                if max_price:
                    all_parsed.sort(key=lambda x: abs(x["harga_num"] - max_price) if x["harga_num"] > 0 else 999_999_999)
                else:
                    all_parsed.sort(key=lambda x: x["harga_num"] if x["harga_num"] > 0 else 999_999_999)
                print(f"  Fallback: ambil terdekat budget → {all_parsed[0]['nama'][:40]} {all_parsed[0]['harga']}")
                return [all_parsed[0]]

            return []

        except requests.exceptions.ReadTimeout:
            print(f"Timeout attempt {attempt+1} untuk '{query}', retry dalam 3 detik...")
            time.sleep(3)
            continue
        except requests.exceptions.RequestException as e:
            print(f"API Error attempt {attempt+1} untuk '{query}': {e}")
            time.sleep(2)
            continue

    # Semua retry gagal
    print(f"Semua retry gagal untuk '{query}'")
    return [{
        "nama": f"[Timeout] {query}",
        "harga": "N/A",
        "harga_num": 0,
        "rating": "-",
        "gambar": "",
        "link": "",
        "toko": "N/A",
        "query": query,
        "error": "timeout",
    }]


def get_category(query: str) -> str:
    """Mapping query → kategori berdasarkan keyword."""
    category_keywords = {
        "sepatu": ["sepatu", "shoes", "sneakers", "loafer", "boots", "sandal", "heels", "footwear"],
        "atasan": ["kaos", "kemeja", "blouse", "sweater", "hoodie", "polo", "tshirt", "shirt", "kaus", "baju"],
        "bawahan": ["celana", "rok", "pants", "jeans", "shorts", "skirt", "jogger", "cargo"],
        "outer": ["jaket", "jacket", "blazer", "cardigan", "coat", "vest", "flannel", "denim"],
        "aksesoris": ["tas", "tote", "kalung", "gelang", "anting", "jam", "topi", "belt", "cap", "beanie"],
    }
    query_lower = query.lower()
    for cat, keywords in category_keywords.items():
        for kw in keywords:
            if kw in query_lower:
                return cat
    return "lainnya"


def product_finder_node(state: FashionState) -> dict:
    """Node: Product Finder Agent — fetch produk sesuai budget per kategori."""
    items_to_search = state.get("items_to_search", [])
    total_budget = state.get("budget", 500_000)
    budget_result = state.get("budget_result", "")

    print(f"\n=== PRODUCT FINDER ===")
    print(f"items_to_search: {items_to_search}")
    print(f"total_budget: Rp{total_budget:,.0f}")

    if not items_to_search:
        print("WARNING: items_to_search kosong!")
        return {"product_results": []}

    # Parse alokasi budget per kategori dari output Budget Agent
    budget_allocation = parse_budget_allocation(budget_result, total_budget)
    print(f"budget_allocation: { {k: f'Rp{v:,.0f}' for k, v in budget_allocation.items()} }")

    all_products = []
    for i, query in enumerate(items_to_search):
        if i > 0:
            time.sleep(2)  # Delay antar request

        category = get_category(query)
        max_price = budget_allocation.get(category, total_budget * 0.35)

        print(f"\nSearching: '{query}' | kategori: {category} | max_price: Rp{max_price:,.0f}")

        results = search_google_shopping(query, max_price=max_price, max_results=1)

        print(f"Results: {[(p['nama'][:35], p['harga']) for p in results]}")

        # Skip produk error/timeout dari display tapi tetap track
        valid = [p for p in results if "error" not in p]
        all_products.extend(valid if valid else results)

    return {"product_results": all_products}