"""
Planner Agent — Parsing prompt bebas user ke komponen terstruktur.
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import FashionState
from agents.llm import get_llm
from config import DEFAULT_BUDGET

SYSTEM_PROMPT = """Kamu adalah Fashion Planner Agent.
Tugasmu HANYA mem-parsing prompt user menjadi komponen terstruktur.
Kamu TIDAK memberikan rekomendasi.

Ekstrak informasi berikut dari prompt user. Jika tidak disebutkan, isi "tidak disebutkan".

WAJIB respond dalam format JSON SAJA (tanpa markdown, tanpa backtick):
{
    "occasion": "jenis acara (kuliah/nongkrong/kerja/nikahan/date/dll)",
    "style": "gaya fashion (skena/old money/streetwear/casual/minimalist/korean/dll)",
    "gender": "pria/wanita/tidak disebutkan",
    "umur": 0,
    "budget": 0,
    "wardrobe_items": ["item1", "item2"],
    "extra_notes": "info tambahan yang relevan"
}

Rules:
- wardrobe_items = pakaian yang USER SUDAH PUNYA (disebutkan di prompt)
- Jika user bilang "rekomendasikan outfit kemeja putih celana jeans", itu BISA berarti dia sudah punya ATAU mau direkomendasikan item tersebut. Perhatikan konteks kalimat.
- Jika ada kata "punya", "ada", "milik" → masuk wardrobe_items
- Jika ada kata "rekomendasikan", "carikan", "cari" → BUKAN wardrobe, tapi preferensi
- budget = 0 jika tidak disebutkan
- umur = 0 jika tidak disebutkan
- Jika gender tidak disebutkan, tentukan dari konteks. Jika tidak ada konteks sama sekali, default "pria"
- Jika user bilang "cowok/laki/mas/bang" → pria
- Jika user bilang "cewek/perempuan/mbak/sis" → wanita"""


def planner_node(state: FashionState) -> dict:
    llm = get_llm()

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Parse prompt berikut:\n\n{state['user_prompt']}"),
    ]

    response = llm.invoke(messages)

    try:
        # Bersihkan response dari markdown formatting jika ada
        text = response.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {
            "occasion": "tidak disebutkan",
            "style": "casual",
            "gender": "tidak disebutkan",
            "umur": 0,
            "budget": 0,
            "wardrobe_items": [],
            "extra_notes": response.content,
        }

    budget = parsed.get("budget", 0)
    if budget == 0 or budget == "tidak disebutkan":
        budget = DEFAULT_BUDGET

    return {
        "occasion": parsed.get("occasion", "tidak disebutkan"),
        "style": parsed.get("style", "casual"),
        "gender": parsed.get("gender", "tidak disebutkan"),
        "umur": parsed.get("umur", 0),
        "budget": float(budget),
        "wardrobe_items": parsed.get("wardrobe_items", []),
        "extra_notes": parsed.get("extra_notes", ""),
    }
