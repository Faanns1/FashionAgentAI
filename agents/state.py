from __future__ import annotations
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class FashionState(TypedDict):
    # ===== Raw Input =====
    user_prompt: str

    # ===== Parsed oleh Planner =====
    occasion: str
    style: str
    gender: str
    umur: int
    budget: float
    wardrobe_items: list[str]       # baju yang udah dipunya
    extra_notes: str                # info tambahan dari prompt

    # ===== Agent Outputs =====
    occasion_result: str
    wardrobe_result: str
    budget_result: str
    trend_result: str
    recommendation_result: str
    items_to_search: list[str]      # item yang perlu dicari di API
    product_results: list[dict]     # hasil dari Google Shopping API
    explanation_result: str
    preview_image_path: str         # path gambar kolase

    # ===== Final =====
    final_output: str

    # ===== Feedback =====
    session_id: str
    feedback_history: list[dict]

    # ===== LangGraph =====
    messages: Annotated[list, add_messages]
