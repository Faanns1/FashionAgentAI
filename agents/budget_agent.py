"""
Budget Agent — Alokasi budget untuk item yang perlu dibeli.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import FashionState
from agents.llm import get_llm

SYSTEM_PROMPT = """Kamu adalah Budget Optimizer Agent.
Tugasmu mengalokasikan budget user untuk item yang PERLU DIBELI saja.

Rules:
1. Hanya alokasikan untuk item yang belum dimiliki user
2. Prioritas: Sepatu > Atasan > Bawahan > Outer > Aksesoris
3. Alokasi HARUS realistis untuk pasar Indonesia:
- Kaos/atasan casual: Rp50.000 - Rp200.000
- Hoodie/sweater: Rp100.000 - Rp300.000
- Celana jeans/cargo: Rp100.000 - Rp300.000
- Sepatu sneakers: Rp100.000 - Rp400.000
- Jaket/outer: Rp100.000 - Rp400.000
- Aksesoris: Rp20.000 - Rp100.000
4. Jangan alokasikan terlalu kecil — minimal 15% per item utama
5. Total HARUS sama dengan budget user

Format output:
TOTAL BUDGET: Rp[jumlah]
ALOKASI:
- [item]: Rp[jumlah] ([persentase]%)

Jawab dalam Bahasa Indonesia."""


def budget_node(state: FashionState) -> dict:
    llm = get_llm()

    prompt = (
        f"Budget: Rp{state['budget']:,.0f}\n\n"
        f"Hasil analisis wardrobe:\n{state['wardrobe_result']}\n\n"
        f"Alokasikan budget untuk item yang perlu dibeli."
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    return {"budget_result": response.content}
