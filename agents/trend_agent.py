"""
Trend Agent — Analisis tren fashion terkini.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import FashionState
from agents.llm import get_llm

SYSTEM_PROMPT = """Kamu adalah Fashion Trend Analyst Agent.
Tugasmu memberikan insight tren fashion terkini yang RELEVAN.

Yang harus kamu berikan:
1. Item yang sedang trending untuk style tersebut
2. Warna yang sedang populer
3. Material yang sedang in-season
4. Brand/tipe item yang recommended
5. Hal yang sudah TIDAK trending (outdated)

PENTING — Sesuaikan dengan UMUR:
- Anak-anak (< 13 tahun): tren fashion anak, brand anak (H&M Kids, Uniqlo Kids, GAP Kids, dll). JANGAN rekomendasikan brand/item dewasa.
- Remaja (13-17 tahun): tren remaja yang age-appropriate.
- Dewasa: tren dewasa sesuai style.

Jawab dalam Bahasa Indonesia, singkat dan actionable."""


def trend_node(state: FashionState) -> dict:
    llm = get_llm()

    prompt = (
        f"Style: {state['style']}\n"
        f"Occasion: {state['occasion']}\n"
        f"Gender: {state['gender']}\n"
        f"Umur: {state.get('umur', 0)}\n"
        f"Extra notes: {state.get('extra_notes', '')}\n\n"
        f"Berikan analisis tren fashion terkini yang relevan."
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    return {"trend_result": response.content}
