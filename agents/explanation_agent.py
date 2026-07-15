"""
Explanation Agent — Jelasin rekomendasi outfit ke user.
Output final: teks + info produk + link.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from agents.state import FashionState
from agents.llm import get_llm

SYSTEM_PROMPT = """Kamu adalah Fashion Explanation Expert.
Tugasmu menjelaskan rekomendasi outfit dengan bahasa Indonesia yang santai dan menarik.

Format output:

🎯 RINGKASAN
[Satu paragraf kenapa outfit ini cocok]

👕 OUTFIT LENGKAP
[List setiap item — yang sudah dipunya tandai ✅, yang baru tandai 🛒]

💡 TIPS STYLING
[2-3 tips mix-and-match]

Gunakan bahasa santai kayak ngobrol sama teman. Jangan terlalu formal."""


def explanation_node(state: FashionState) -> dict:
    llm = get_llm()

    # Format product info untuk context
    products_text = ""
    for p in state.get("product_results", []):
        if "error" not in p:
            products_text += (
                f"- {p['nama']} | {p['harga']} | Rating: {p['rating']} | "
                f"Toko: {p['toko']}\n"
            )

    prompt = (
        f"User prompt: {state['user_prompt']}\n\n"
        f"=== REKOMENDASI OUTFIT ===\n{state['recommendation_result']}\n\n"
        f"=== PRODUK DARI GOOGLE SHOPPING ===\n{products_text}\n\n"
        f"=== WARDROBE USER ===\n{state['wardrobe_result']}\n\n"
        f"=== TREND ===\n{state['trend_result']}\n\n"
        f"Jelaskan outfit ini ke user. Sertakan produk yang ditemukan."
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)

    # Build final output dengan produk + link
    product_section = "\n\n🛒 **PRODUK YANG DITEMUKAN:**\n"
    for p in state.get("product_results", []):
        if "error" not in p and p.get("link"):
            product_section += (
                f"- **{p['nama']}** — {p['harga']} — ⭐{p['rating']} — "
                f"[Beli di {p['toko']}]({p['link']})\n"
            )

    final = response.content + product_section

    return {
        "explanation_result": response.content,
        "final_output": final,
    }
