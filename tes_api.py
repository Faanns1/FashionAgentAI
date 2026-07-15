from config import RAPIDAPI_KEY
import requests

headers = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "real-time-product-search.p.rapidapi.com"
}

queries = ["kaos band skena pria", "hoodie oversized pria hitam", "cargo pants pria"]

for q in queries:
    r = requests.get(
        "https://real-time-product-search.p.rapidapi.com/search",
        headers=headers,
        params={"q": q, "country": "id", "language": "id", "limit": 3},
        timeout=30
    )
    data = r.json()
    products = data.get("data", {}).get("products", [])
    print(f"\nQuery: {q}")
    for p in products:
        print(f"  - {p['product_title'][:50]} | {p['price']}")