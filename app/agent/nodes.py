from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from app.agent.tools import (
    get_user_profile,
    search_exercise_history,
    search_diet_history,
    get_recovery_status,
    calculate_recommended_calories,
    generate_exercise_plan,
    generate_diet_recommendation
)
from app.agent.prompts import (
    SYSTEM_PROMPT,
    USER_PROFILE_PROMPT,
    EXERCISE_HISTORY_PROMPT,
    DIET_HISTORY_PROMPT,
    RECOVERY_STATUS_PROMPT,
    format_recommendation_response
)


def router(state: Dict[str, Any]) -> str:
    """Route the user query to appropriate handler"""
    messages = state.get("messages", [])
    if not messages:
        return "quick_answer"

    last_message = messages[-1]
    content = last_message.content.lower() if hasattr(last_message, 'content') else str(last_message).lower()

    # Simple intent detection
    if any(keyword in content for keyword in ["运动", "跑步", "训练", "锻炼", "exercise", "workout"]):
        return "exercise_recommendation"
    elif any(keyword in content for keyword in ["饮食", "吃", "食物", "diet", "food", "营养"]):
        return "diet_recommendation"
    elif any(keyword in content for keyword in ["恢复", "休息", "疲劳", "recovery", "rest"]):
        return "recovery_recommendation"
    elif any(keyword in content for keyword in ["计划", "建议", "推荐", "plan", "recommend"]):
        return "generate_recommendation"
    else:
        return "general_conversation"


def get_user_profile_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch user profile"""
    user_id = state.get("user_id")
    profile = get_user_profile(user_id)
    return {"profile": profile}


def search_history_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Search user's exercise and diet history using RAG"""
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_message = messages[-1].content if messages else ""

    # Search relevant history
    exercise_history = search_exercise_history(user_id, last_message, n_results=5)
    diet_history = search_diet_history(user_id, last_message, n_results=5)

    return {
        "exercise_history": exercise_history,
        "diet_history": diet_history
    }


def generate_recommendation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive recommendation based on user data"""
    user_id = state.get("user_id")
    profile = state.get("profile", {})
    exercise_history = state.get("exercise_history", [])
    diet_history = state.get("diet_history", [])

    # Get recovery status
    recovery = get_recovery_status(user_id)

    # Calculate recommended calories
    calories = calculate_recommended_calories(user_id)

    # Generate exercise plan based on recovery status
    recommended_intensity = recovery.get("recommended_intensity", 5)
    exercise_plan = generate_exercise_plan(user_id, recommended_intensity)

    # Generate diet recommendation
    diet_plan = generate_diet_recommendation(user_id)

    recommendations = {
        "exercise": exercise_plan,
        "diet": diet_plan,
        "recovery": {
            "status": recovery.get("status", "unknown"),
            "message": recovery.get("message", ""),
            "sleep_hours": 8,
            "water_intake": 2.5,
            "stretching": "建议睡前做15分钟拉伸"
        },
        "calories": calories
    }

    response = format_recommendation_response({
        "exercise_type": exercise_plan["type"],
        "duration": exercise_plan["duration"],
        "intensity": exercise_plan["intensity"],
        "reason": exercise_plan["reason"],
        "diet": f"每日建议摄入{calories.get('recommended_calories', 2000)}卡路里",
        "sleep_hours": 8,
        "water_intake": 2.5,
        "stretching": "建议睡前做15分钟拉伸"
    })

    return {
        "response": response,
        "recommendations": recommendations,
        "sources": exercise_history + diet_history
    }


def quick_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Handle quick questions without deep search"""
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_message = messages[-1].content if messages else ""

    profile = get_user_profile(user_id)

    response = f"您好{profile.get('username', '')}！我是您的运动健康顾问。根据您的问题，我会尽量给您准确的建议。如果您想了解运动或饮食建议，请告诉我您的具体需求。"

    return {"response": response}


def update_profile_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Update user profile/preferences"""
    return {"response": "偏好更新功能开发中..."}