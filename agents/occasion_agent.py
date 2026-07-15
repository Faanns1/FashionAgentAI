"""
Occasion Agent — Klasifikasi acara dan tentukan dress code.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import FashionState
from agents.llm import get_llm

SYSTEM_PROMPT = """Kamu adalah Occasion Analyst Agent.
Tugasmu menganalisis jenis acara dan menentukan dress code yang sesuai.

Untuk setiap occasion, tentukan:
1. Level formalitas (formal / semi-formal / casual / santai)
2. Item yang WAJIB ada
3. Item yang HARUS dihindari
4. Warna yang cocok untuk acara tersebut
5. Tips khusus untuk acara tersebut

PENTING — Pertimbangkan UMUR user:
- Anak-anak (< 13 tahun): outfit harus nyaman, playful, sesuai usia. JANGAN rekomendasikan pakaian dewasa.
- Remaja (13-17 tahun): boleh trendy tapi tetap age-appropriate.
- Dewasa muda (18-30 tahun): bebas eksplorasi style.
- Dewasa (30+ tahun): lebih mature dan refined.

Jawab dalam Bahasa Indonesia, singkat dan terstruktur."""


def occasion_node(state: FashionState) -> dict:
    llm = get_llm()

    prompt = (
        f"Analisis dress code untuk acara: {state['occasion']}\n"
        f"Gender: {state['gender']}\n"
        f"Style preferensi: {state['style']}"
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    return {"occasion_result": response.content}
