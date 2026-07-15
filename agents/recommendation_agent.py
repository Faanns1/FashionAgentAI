"""
Recommendation Agent — Gabungkan semua hasil, susun outfit, tentukan item yang dicari.
"""

import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import FashionState
from agents.llm import get_llm

SYSTEM_PROMPT = """Kamu adalah Fashion Recommendation Agent.
Tugasmu menggabungkan SEMUA hasil analisis dan menyusun outfit lengkap.

Langkah:
1. Gabungkan item yang sudah dipunya user + saran dari trend
2. Tentukan item yang PERLU DICARI di toko online
3. Pastikan outfit konsisten (style, warna, occasion)
4. Pastikan total budget tidak terlampaui

OUTPUT WAJIB dalam format JSON seperti ini:
{
    "outfit_plan": "Deskripsi outfit lengkap dalam bahasa Indonesia",
    "owned_items": ["item yang sudah dipunya user"],
    "items_to_search": ["query1", "query2", "query3"],
    "style_notes": "Catatan styling"
}

RULES WAJIB untuk items_to_search:
- Max 4 query, masing-masing 3-5 kata
- WAJIB sertakan style user di setiap query
- WAJIB sertakan gender di setiap query
- JANGAN query generic seperti "kaos pria", "celana pria", "sepatu pria"

Contoh query berdasarkan style:
- skena     : "kaos band oversized pria", "cargo pants pria hitam", "sneakers chunky pria", "jaket flannel pria"
- old money : "kemeja linen pria beige", "celana chino pria cream", "loafer pria coklat", "knit vest pria"
- streetwear: "hoodie oversized pria", "jogger pants pria hitam", "sneakers pria putih", "bucket hat pria"
- casual    : "kaos polos pria", "jeans slim pria biru", "sneakers pria putih"
- elegant   : "dress brukat wanita", "heels wanita hitam", "blazer formal wanita"
- korean    : "sweater knit pria", "wide pants pria beige", "sneakers retro pria"
- minimalist: "kaos polos premium pria", "celana chino pria", "sneakers putih pria"
- formal    : "kemeja formal pria putih", "celana bahan pria hitam", "sepatu pantofel pria"

Untuk anak-anak (umur < 13):
- Tambah kata "anak" di query
- Contoh: "kaos anak laki laki", "celana jeans anak laki", "sepatu sneakers anak"

Gunakan bahasa Indonesia."""


def extract_json_from_text(text: str) -> dict | None:
    """Coba extract JSON dari text meskipun ada teks tambahan."""
    # Coba parse langsung
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Coba cari JSON block dengan regex
    pattern = r'\{[^{}]*"items_to_search"[^{}]*\}'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Coba cari apapun yang diawali { dan diakhiri }
    pattern2 = r'\{.*\}'
    match2 = re.search(pattern2, text, re.DOTALL)
    if match2:
        try:
            return json.loads(match2.group())
        except json.JSONDecodeError:
            pass

    return None


def fallback_items_to_search(state: FashionState) -> list[str]:
    gender = state.get("gender", "pria")
    style = state.get("style", "casual")
    umur = state.get("umur", 20)

    # Anak-anak 6-12 tahun (bukan bayi)
    if umur and umur < 13:
        if gender == "pria":
            return [
                "kaos anak laki laki",
                "celana jeans anak laki",
                "sepatu sneakers anak laki",
            ]
        else:
            return [
                "kaos anak perempuan",
                "rok anak perempuan",
                "sepatu anak perempuan",
            ]
    

    style_map = {
        "old money": ["kemeja linen", "celana chino", "loafer"],
        "skena": ["kaos oversized graphic", "cargo pants", "sneakers chunky"],
        "streetwear": ["hoodie oversized", "jogger pants", "sneakers"],
        "casual": ["kaos polos", "jeans slim", "sneakers"],
        "elegant": ["dress elegant", "heels", "blazer formal"],
        "formal": ["kemeja formal", "celana bahan", "sepatu formal"],
        "minimalist": ["kaos polos premium", "celana chino", "sneakers putih"],
        "korean": ["sweater knit", "wide pants", "sneakers retro"],
    }

    base_items = style_map.get(style.lower(), ["kaos", "celana panjang", "sepatu"])
    return [f"{item} {gender}" for item in base_items[:3]]


def recommendation_node(state: FashionState) -> dict:
    llm = get_llm()

    prompt = (
        f"=== OCCASION ANALYSIS ===\n{state['occasion_result']}\n\n"
        f"=== WARDROBE ANALYSIS ===\n{state['wardrobe_result']}\n\n"
        f"=== BUDGET ANALYSIS ===\n{state['budget_result']}\n\n"
        f"=== TREND ANALYSIS ===\n{state['trend_result']}\n\n"
        f"=== USER INFO ===\n"
        f"STYLE: {state['style']} (WAJIB tercermin di setiap query!)\n"
        f"Occasion: {state['occasion']}\n"
        f"Gender: {state['gender']}\n"
        f"Umur: {state.get('umur', 0)}\n"
        f"Budget: Rp{state['budget']:,.0f}\n\n"
        f"Susun outfit SESUAI STYLE '{state['style']}' dan output HANYA JSON."
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)

    # Bersihkan response
    text = response.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    # Coba parse JSON dengan berbagai cara
    parsed = extract_json_from_text(text)

    if parsed:
        items_to_search = parsed.get("items_to_search", [])
        recommendation_text = parsed.get("outfit_plan", text)

        # Validasi items_to_search tidak kosong
        if not items_to_search:
            items_to_search = fallback_items_to_search(state)
    else:
        # Fallback total — generate manual
        items_to_search = fallback_items_to_search(state)
        recommendation_text = text

    # Pastikan max 4 item
    items_to_search = items_to_search[:4]

    return {
        "recommendation_result": recommendation_text,
        "items_to_search": items_to_search,
    }