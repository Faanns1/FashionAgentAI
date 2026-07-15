"""
Wardrobe Analyst Agent — Analisis pakaian yang dimiliki user, tentukan yang kurang.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import FashionState
from agents.llm import get_llm

SYSTEM_PROMPT = """Kamu adalah Wardrobe Analyst Agent.
Tugasmu menganalisis pakaian yang SUDAH DIMILIKI user dan menentukan apa yang KURANG.

Langkah-langkah:
1. Kategorikan setiap item: Atasan / Bawahan / Sepatu / Aksesoris / Outer
2. Cek apakah outfit sudah lengkap (minimal: atasan + bawahan + sepatu)
3. Tentukan item apa yang KURANG dan perlu dicari/dibeli
4. Jika wardrobe kosong (user ga sebut), rekomendasikan outfit LENGKAP

PENTING — Pertimbangkan UMUR user:
- Anak-anak (< 13 tahun): rekomendasikan pakaian anak, bukan dewasa. Contoh: kaos anak, celana pendek anak, sepatu anak.
- Remaja (13-17 tahun): pakaian remaja yang age-appropriate.
- Dewasa: pakaian dewasa sesuai style.

Format output:
SUDAH PUNYA:
- [kategori]: [item] ✅

BELUM PUNYA (PERLU DICARI):
- [kategori]: [saran item] ❌

Jawab dalam Bahasa Indonesia."""

def wardrobe_node(state: FashionState) -> dict:
    llm = get_llm()

    wardrobe = state.get("wardrobe_items", [])
    if wardrobe:
        wardrobe_text = "\n".join(f"- {item}" for item in wardrobe)
    else:
        wardrobe_text = "(Tidak ada — user tidak menyebutkan pakaian yang dimiliki)"

    prompt = (
        f"Pakaian yang dimiliki user:\n{wardrobe_text}\n\n"
        f"Occasion: {state['occasion']}\n"
        f"Style: {state['style']}\n"
        f"Gender: {state['gender']}\n\n"
        f"Analisis dan tentukan apa yang kurang."
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    return {"wardrobe_result": response.content}
