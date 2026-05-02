from typing import TypedDict, List
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END


class AgentState(TypedDict):
    user_id: str
    conversation_id: str
    messages: List[BaseMessage]
    profile: dict
    exercise_history: List[str]
    diet_history: List[str]
    recommendations: dict
    response: str
    sources: List[str]
    recent_context: dict
    next_node: str


def create_agent_graph():
    from app.agent.nodes import (
        router,
        get_user_profile_node,
        search_history_node,
        generate_recommendation_node,
        quick_answer_node,
        update_profile_node
    )

    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("router", router)
    graph.add_node("get_user_profile", get_user_profile_node)
    graph.add_node("search_history", search_history_node)
    graph.add_node("generate_recommendation", generate_recommendation_node)
    graph.add_node("quick_answer", quick_answer_node)
    graph.add_node("update_profile", update_profile_node)

    # Set entry point
    graph.set_entry_point("router")

    # Router decides the next step - conditional routing
    graph.add_conditional_edges(
        "router",
        lambda x: x.get("next_node", "quick_answer"),
        {
            "exercise_recommendation": "get_user_profile",
            "diet_recommendation": "get_user_profile",
            "recovery_recommendation": "get_user_profile",
            "generate_recommendation": "get_user_profile",
            "general_conversation": "quick_answer",
            "quick_answer": "quick_answer",
            "update_profile": "update_profile"
        }
    )

    # Add edges for recommendation flow
    graph.add_edge("get_user_profile", "search_history")
    graph.add_edge("search_history", "generate_recommendation")
    graph.add_edge("generate_recommendation", END)
    graph.add_edge("quick_answer", END)
    graph.add_edge("update_profile", END)

    return graph.compile()


agent_graph = create_agent_graph()