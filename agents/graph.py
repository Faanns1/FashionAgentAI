"""
LangGraph Orchestrator — StateGraph menghubungkan semua agent + tool.

Flow:
    planner → [occasion, wardrobe, trend] (parallel)
           → budget (setelah wardrobe)
           → recommendation → product_finder → explanation → preview_composer

Graph:
                      ┌── occasion ──┐
    planner (parse) ──┼── wardrobe ──┼── budget ──┐
                      └── trend ─────┘            │
                                                  ▼
                      recommendation → product_finder → explanation → preview_composer
"""

from langgraph.graph import StateGraph, START, END

from agents.state import FashionState
from agents.planner import planner_node
from agents.occasion_agent import occasion_node
from agents.wardrobe_agent import wardrobe_node
from agents.budget_agent import budget_node
from agents.trend_agent import trend_node
from agents.recommendation_agent import recommendation_node
from agents.product_finder import product_finder_node
from agents.explanation_agent import explanation_node
from tools.preview_composer import preview_composer_node


def build_graph():
    """Bangun dan compile StateGraph."""
    graph = StateGraph(FashionState)

    # ===== Nodes =====
    graph.add_node("planner", planner_node)
    graph.add_node("occasion", occasion_node)
    graph.add_node("wardrobe", wardrobe_node)
    graph.add_node("budget", budget_node)
    graph.add_node("trend", trend_node)
    graph.add_node("recommendation", recommendation_node)
    graph.add_node("product_finder", product_finder_node)
    graph.add_node("explanation", explanation_node)
    graph.add_node("preview_composer", preview_composer_node)

    # ===== Edges =====

    # START → Planner
    graph.add_edge(START, "planner")

    # Planner → 3 agent paralel
    graph.add_edge("planner", "occasion")
    graph.add_edge("planner", "wardrobe")
    graph.add_edge("planner", "trend")

    # Wardrobe → Budget (budget perlu tau item yang kurang dulu)
    graph.add_edge("wardrobe", "budget")

    # 3 analysis + budget → Recommendation (fan-in)
    graph.add_edge("occasion", "recommendation")
    graph.add_edge("budget", "recommendation")
    graph.add_edge("trend", "recommendation")

    # Sequential: Recommendation → Product Finder → Explanation → Preview
    graph.add_edge("recommendation", "product_finder")
    graph.add_edge("product_finder", "explanation")
    graph.add_edge("explanation", "preview_composer")

    # Preview → END
    graph.add_edge("preview_composer", END)

    return graph.compile()


def run_recommendation(user_prompt: str, session_id: str = "default") -> dict:
    """
    Entry point — jalankan seluruh pipeline.

    Returns:
        dict dengan final_output, product_results, preview_image_path
    """
    graph = build_graph()

    initial_state: FashionState = {
        "user_prompt": user_prompt,
        "session_id": session_id,
        "occasion": "",
        "style": "",
        "gender": "",
        "umur": 0,
        "budget": 0,
        "wardrobe_items": [],
        "extra_notes": "",
        "occasion_result": "",
        "wardrobe_result": "",
        "budget_result": "",
        "trend_result": "",
        "recommendation_result": "",
        "items_to_search": [],
        "product_results": [],
        "explanation_result": "",
        "preview_image_path": "",
        "final_output": "",
        "feedback_history": [],
        "messages": [],
    }

    result = graph.invoke(initial_state)
    return result


def run_recommendation_stream(user_prompt: str, session_id: str = "default"):
    """Streaming version — yield setiap step."""
    graph = build_graph()

    initial_state: FashionState = {
        "user_prompt": user_prompt,
        "session_id": session_id,
        "occasion": "",
        "style": "",
        "gender": "",
        "umur": 0,
        "budget": 0,
        "wardrobe_items": [],
        "extra_notes": "",
        "occasion_result": "",
        "wardrobe_result": "",
        "budget_result": "",
        "trend_result": "",
        "recommendation_result": "",
        "items_to_search": [],
        "product_results": [],
        "explanation_result": "",
        "preview_image_path": "",
        "final_output": "",
        "feedback_history": [],
        "messages": [],
    }

    for event in graph.stream(initial_state, stream_mode="updates"):
        for node_name, node_output in event.items():
            yield node_name, node_output
