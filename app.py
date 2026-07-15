"""
FashionAgentAI — Multi-Agent AI Personal Shopper
Streamlit App — Chatbot-style free-form input
"""

import streamlit as st
import uuid

from agents.graph import run_recommendation_stream
from agents.feedback_agent import save_feedback, get_user_preferences
from database.db_setup import init_db

# ===== Init =====
st.set_page_config(page_title="FashionAgentAI", page_icon="👔", layout="wide")
init_db()

# Session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ===== Header =====
st.title("👔 FashionAgentAI")
st.caption("Multi-Agent AI Personal Shopper — Ceritain aja outfit yang kamu mau!")

# ===== Chat History =====
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

        # Tampilkan agent details (expander)
        # if chat.get("agent_outputs"):
        #     st.markdown("---")
        #     st.markdown("### 🤖 Proses Kerja Agent")
        #     for agent_name, agent_data in chat["agent_outputs"].items():
        #         icon = agent_data.get("icon", "⏳")
        #         label = agent_data.get("label", agent_name)
        #         output = agent_data.get("output", "")
        #         if output:
        #             with st.expander(f"{icon} {label}", expanded=False):
        #                 st.markdown(output)

        # Tampilkan gambar produk
        if chat.get("products"):
            st.markdown("---")
            st.markdown("### 🖼️ Produk yang Ditemukan")
            seen_queries = []
            unique_products = []
            for p in chat["products"]:
                q = p.get("query", "")
                if q not in seen_queries:
                    seen_queries.append(q)
                    unique_products.append(p)

            cols = st.columns(min(len(unique_products), 4))
            for i, product in enumerate(unique_products):
                if product.get("gambar") and "error" not in product:
                    with cols[i % len(cols)]:
                        st.image(product["gambar"], width=150)
                        nama_short = product["nama"][:40] + "..." if len(product["nama"]) > 40 else product["nama"]
                        st.caption(f"**{nama_short}**\n{product['harga']}")
                        if product.get("link"):
                            st.link_button("🛒 Beli", product["link"], use_container_width=True)

        # Tampilkan preview kolase
        if chat.get("preview_path"):
            st.markdown("---")
            st.markdown("### 👗 Preview Outfit")
            st.image(chat["preview_path"], use_container_width=True)

        # Feedback buttons
        if chat.get("show_feedback") and not chat.get("feedback_given"):
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 4])
            msg_idx = chat.get("msg_idx")
            with col1:
                if st.button("👍 Suka", key=f"like_{msg_idx}"):
                    save_feedback(
                        st.session_state.session_id, "like",
                        chat.get("style", ""), chat.get("outfit_summary", "")
                    )
                    st.session_state.chat_history[msg_idx]["feedback_given"] = True
                    st.toast("✅ Feedback tersimpan!")
                    st.rerun()
            with col2:
                if st.button("👎 Kurang", key=f"dislike_{msg_idx}"):
                    save_feedback(
                        st.session_state.session_id, "dislike",
                        chat.get("style", ""), chat.get("outfit_summary", "")
                    )
                    st.session_state.chat_history[msg_idx]["feedback_given"] = True
                    st.toast("📝 Feedback tersimpan!")
                    st.rerun()

# ===== Chat Input =====
user_input = st.chat_input("Ceritain outfit yang kamu mau...")

# Kalau ada contoh prompt yang diklik di sidebar, pakai itu sebagai input
if "pending_prompt" in st.session_state:
    user_input = st.session_state.pop("pending_prompt")

if user_input:
    # Tampilkan user message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process dengan agents
    with st.chat_message("assistant"):

        # Agent label mapping
        agent_config = {
            "planner": {
                "icon": "🧠",
                "label": "Planner Agent — Parsing prompt",
                "output_keys": ["occasion", "style", "gender", "umur", "budget", "wardrobe_items"],
            },
            "occasion": {
                "icon": "🎪",
                "label": "Occasion Agent — Analisis acara",
                "output_keys": ["occasion_result"],
            },
            "wardrobe": {
                "icon": "👕",
                "label": "Wardrobe Analyst — Analisis pakaian",
                "output_keys": ["wardrobe_result"],
            },
            "budget": {
                "icon": "💰",
                "label": "Budget Agent — Alokasi budget",
                "output_keys": ["budget_result"],
            },
            "trend": {
                "icon": "🔥",
                "label": "Trend Agent — Tren fashion",
                "output_keys": ["trend_result"],
            },
            "recommendation": {
                "icon": "🎯",
                "label": "Recommendation Agent — Susun outfit",
                "output_keys": ["recommendation_result", "items_to_search"],
            },
            "product_finder": {
                "icon": "🛍️",
                "label": "Product Finder — Cari produk (Google Shopping API)",
                "output_keys": ["product_results"],
            },
            "explanation": {
                "icon": "💬",
                "label": "Explanation Agent — Penjelasan",
                "output_keys": ["explanation_result"],
            },
            "preview_composer": {
                "icon": "🖼️",
                "label": "Preview Composer — Kolase foto (Tool)",
                "output_keys": ["preview_image_path"],
            },
        }

        status_container = st.status("🤖 Agent sedang bekerja...", expanded=True)
        final_output = ""
        product_results = []
        preview_path = ""
        parsed_style = ""
        agent_outputs = {}

        try:
            for node_name, node_output in run_recommendation_stream(
                user_input, st.session_state.session_id
            ):
                config = agent_config.get(node_name, {})
                icon = config.get("icon", "⏳")
                label = config.get("label", node_name)

                status_container.update(label=f"{icon} {label}")
                status_container.write(f"✅ {icon} **{label}** selesai")

                # Format output agent untuk ditampilkan
                agent_display = ""

                if node_name == "planner":
                    agent_display = (
                        f"**Occasion:** {node_output.get('occasion', '-')}\n\n"
                        f"**Style:** {node_output.get('style', '-')}\n\n"
                        f"**Gender:** {node_output.get('gender', '-')}\n\n"
                        f"**Umur:** {node_output.get('umur', '-')}\n\n"
                        f"**Budget:** Rp{node_output.get('budget', 0):,.0f}\n\n"
                        f"**Wardrobe:** {', '.join(node_output.get('wardrobe_items', [])) or 'Tidak disebutkan'}"
                    )
                    parsed_style = node_output.get("style", "")

                elif node_name == "product_finder":
                    products = node_output.get("product_results", [])
                    product_results = products
                    lines = []
                    for p in products:
                        if "error" not in p:
                            lines.append(
                                f"- **{p.get('nama', 'Unknown')[:50]}** — "
                                f"{p.get('harga', 'N/A')} — "
                                f"Toko: {p.get('toko', '-')}"
                            )
                    agent_display = "\n".join(lines) if lines else "Tidak ada produk ditemukan"

                elif node_name == "recommendation":
                    agent_display = node_output.get("recommendation_result", "")
                    items = node_output.get("items_to_search", [])
                    if items:
                        agent_display += "\n\n**Item yang akan dicari di API:**\n"
                        for item in items:
                            agent_display += f"- 🔍 `{item}`\n"

                elif node_name == "preview_composer":
                    path = node_output.get("preview_image_path", "")
                    preview_path = path
                    agent_display = f"Kolase disimpan di: `{path}`" if path else "Tidak ada gambar untuk dikomposisi"

                else:
                    for key in config.get("output_keys", []):
                        val = node_output.get(key, "")
                        if val and isinstance(val, str):
                            agent_display = val
                            break

                # Simpan output agent
                if agent_display:
                    agent_outputs[node_name] = {
                        "icon": icon,
                        "label": label,
                        "output": agent_display,
                    }
                    print("\n" + "=" * 60)
                    print(f"AGENT : {label}")
                    print(agent_display)
                    print("=" * 60)
                # Capture final output
                if "final_output" in node_output and node_output["final_output"]:
                    final_output = node_output["final_output"]

            status_container.update(label="✅ Semua agent selesai!", state="complete", expanded=False)

            # ===== Tampilkan Hasil Final =====
            st.markdown(final_output)

# # ===== Tampilkan Proses Kerja Agent =====
#             st.markdown("---")
#             st.markdown("### 🤖 Proses Kerja Agent")

#             # Urutkan agent sesuai flow yang benar
#             agent_order = [
#                 "planner", "occasion", "wardrobe", "budget",
#                 "trend", "recommendation", "product_finder",
#                 "explanation", "preview_composer"
#             ]
#             for agent_name in agent_order:
#                 if agent_name in agent_outputs:
#                     agent_data = agent_outputs[agent_name]
#                     with st.expander(f"{agent_data['icon']} {agent_data['label']}", expanded=False):
#                         st.markdown(agent_data["output"])

            # ===== Tampilkan Produk =====
            valid_products = [p for p in product_results if p.get("gambar") and "error" not in p]
            if valid_products:
                st.markdown("---")
                st.markdown("### 🖼️ Produk yang Ditemukan")

                seen_queries = []
                unique_products = []
                for p in valid_products:
                    q = p.get("query", "")
                    if q not in seen_queries:
                        seen_queries.append(q)
                        unique_products.append(p)

                cols = st.columns(min(len(unique_products), 4))
                for i, product in enumerate(unique_products):
                    with cols[i % len(cols)]:
                        st.image(product["gambar"], width=150)
                        nama_short = product["nama"][:40] + "..." if len(product["nama"]) > 40 else product["nama"]
                        st.caption(f"**{nama_short}**\n{product['harga']}")
                        if product.get("link"):
                            st.link_button("🛒 Beli", product["link"], use_container_width=True)


            # ===== Simpan ke Chat History =====
            msg_idx = len(st.session_state.chat_history)
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": final_output,
                "agent_outputs": agent_outputs,
                "products": valid_products,
                "preview_path": preview_path,
                "show_feedback": True,
                "feedback_given": False,
                "msg_idx": msg_idx,
                "style": parsed_style,
                "outfit_summary": final_output[:200],
            })

        except Exception as e:
            status_container.update(label="❌ Error!", state="error")
            st.error(f"Error: {e}")
            st.info("Pastikan GROQ_API_KEY dan RAPIDAPI_KEY sudah diset di file .env")


# ===== Sidebar =====
with st.sidebar:
    st.markdown("### 💡 Contoh Prompt")
    examples = [
        "Aku cowok 22 tahun mau ke kuliah, style skena, budget 500rb",
        "Mau nongkrong sama temen, punya hoodie hitam sama cargo pants, cariin sepatu yang cocok budget 300rb",
        "Cewek mau ke nikahan temen, style elegant, budget 1 juta",
        "Rekomendasiin outfit old money buat date, budget 800rb",
        "Aku punya kaos putih sama jeans, mau ke kampus besok, tambahin apa ya?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=f"ex_{hash(ex)}"):
            st.session_state.pending_prompt = ex
            st.rerun()

    st.markdown("---")
    st.markdown("### ℹ️ Info")
    st.caption(f"Session: `{st.session_state.session_id}`")
    st.caption(f"Chat count: {len(st.session_state.chat_history)}")

    prefs = get_user_preferences(st.session_state.session_id)
    if prefs:
        st.markdown("### 🧠 Preferensi Kamu")
        st.caption(prefs)

    if st.button("🗑️ Reset Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.last_result = None
        st.rerun()