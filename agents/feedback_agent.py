"""
Feedback Agent — Catat feedback user (like/dislike), analisis pola preferensi.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from agents.llm import get_llm
from database.db_setup import init_db, UserPreference


def save_feedback(session_id: str, feedback_type: str, outfit_style: str,
                  outfit_items: str, reason: str = ""):
    """Simpan feedback ke database."""
    _, Session = init_db()
    session = Session()
    try:
        pref = UserPreference(
            session_id=session_id,
            feedback_type=feedback_type,
            outfit_style=outfit_style,
            outfit_items=outfit_items,
            reason=reason,
        )
        session.add(pref)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error saving feedback: {e}")
        return False
    finally:
        session.close()


def get_user_preferences(session_id: str) -> str:
    """Ambil ringkasan preferensi user dari feedback history."""
    _, Session = init_db()
    session = Session()
    try:
        feedbacks = (
            session.query(UserPreference)
            .filter_by(session_id=session_id)
            .order_by(UserPreference.tanggal.desc())
            .limit(20)
            .all()
        )

        if not feedbacks:
            return ""

        likes = [f.outfit_items for f in feedbacks if f.feedback_type == "like"]
        dislikes = [f.outfit_items for f in feedbacks if f.feedback_type == "dislike"]

        summary = ""
        if likes:
            summary += f"User SUKA: {', '.join(likes[:5])}\n"
        if dislikes:
            summary += f"User TIDAK SUKA: {', '.join(dislikes[:5])}\n"

        return summary
    finally:
        session.close()


def analyze_preferences(session_id: str) -> str:
    """Analisis pola preferensi user menggunakan LLM."""
    prefs = get_user_preferences(session_id)
    if not prefs:
        return "Belum ada data feedback."

    llm = get_llm()
    messages = [
        {"role": "system", "content": "Analisis pola preferensi fashion user berdasarkan feedback berikut. Singkat dan actionable."},
        {"role": "user", "content": prefs},
    ]

    response = llm.invoke(messages)
    return response.content
