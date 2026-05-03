import logging
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from app.agent.tools import (
    get_user_profile,
    search_exercise_history,
    search_diet_history,
    get_recovery_status,
    calculate_recommended_calories,
    generate_exercise_plan,
    generate_diet_recommendation,
    call_llm_with_tools
)
from app.agent.prompts import (
    USER_PROFILE_PROMPT,
    EXERCISE_HISTORY_PROMPT,
    DIET_HISTORY_PROMPT,
    RECOVERY_STATUS_PROMPT,
    format_recommendation_response
)

logger = logging.getLogger(__name__)


def router(state: Dict[str, Any]) -> Dict[str, str]:
    """Route the user query to appropriate handler"""
    messages = state.get("messages", [])
    if not messages:
        return {"next_node": "quick_answer"}

    last_message = messages[-1]
    content = last_message.content.lower() if hasattr(last_message, 'content') else str(last_message).lower()

    # Simple intent detection
    if any(keyword in content for keyword in ["运动", "跑步", "训练", "锻炼", "exercise", "workout"]):
        route = "exercise_recommendation"
    elif any(keyword in content for keyword in ["饮食", "吃", "食物", "diet", "food", "营养"]):
        route = "diet_recommendation"
    elif any(keyword in content for keyword in ["恢复", "休息", "疲劳", "recovery", "rest"]):
        route = "recovery_recommendation"
    elif any(keyword in content for keyword in ["计划", "建议", "推荐", "plan", "recommend"]):
        route = "generate_recommendation"
    else:
        route = "general_conversation"

    logger.info(f"[Router] user_id={state.get('user_id')} -> route={route}, content={content[:50]}")
    # Directly set next_node in state
    state["next_node"] = route
    return {"next_node": route}


def get_user_profile_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch user profile"""
    user_id = state.get("user_id")
    logger.info(f"[GetProfile] user_id={user_id}")
    try:
        profile = get_user_profile.invoke({"user_id": user_id})
        logger.info(f"[GetProfile] user_id={user_id} profile_keys={list(profile.keys())}")
        return {"profile": profile}
    except Exception as e:
        logger.error(f"[GetProfile] user_id={user_id} error={e}")
        raise


def search_history_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Search user's exercise and diet history using RAG"""
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_message = messages[-1].content if messages else ""

    logger.info(f"[SearchHistory] user_id={user_id} query={last_message[:50]}")
    try:
        exercise_history = search_exercise_history.invoke({"user_id": user_id, "query": last_message, "n_results": 5})
        diet_history = search_diet_history.invoke({"user_id": user_id, "query": last_message, "n_results": 5})
        logger.info(f"[SearchHistory] user_id={user_id} exercise_count={len(exercise_history)} diet_count={len(diet_history)}")
        return {
            "exercise_history": exercise_history,
            "diet_history": diet_history
        }
    except Exception as e:
        logger.error(f"[SearchHistory] user_id={user_id} error={e}")
        raise


def generate_recommendation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive recommendation based on user data using LLM with tool calling"""
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_message = messages[-1].content if messages else ""

    logger.info(f"[GenerateRecommendation] user_id={user_id}")

    try:
        # Use LLM with tools to generate personalized recommendation
        llm_recommendation = call_llm_with_tools(user_id, last_message)

        if "error" not in llm_recommendation:
            recommendations = {
                "exercise": llm_recommendation,
                "diet": {},
                "recovery": {},
            }
            response = format_recommendation_response({
                "exercise_type": llm_recommendation.get("type", "N/A"),
                "duration": llm_recommendation.get("duration", "N/A"),
                "intensity": llm_recommendation.get("intensity", "N/A"),
                "reason": llm_recommendation.get("reason", "N/A"),
                "diet": "根据您的情况推荐",
                "sleep_hours": 8,
                "water_intake": 2.5,
                "stretching": "运动后建议拉伸"
            })
        else:
            # Fallback to rule-based recommendation
            recovery = get_recovery_status.invoke({"user_id": user_id})
            calories = calculate_recommended_calories.invoke({"user_id": user_id})
            if "error" in calories:
                calories = {"recommended_calories": 2000, "bmr": 1500, "tdee": 2325, "message": "默认推荐值"}

            recommended_intensity = recovery.get("recommended_intensity", 5)
            exercise_plan = generate_exercise_plan.invoke({"user_id": user_id, "intensity": recommended_intensity})
            diet_plan = generate_diet_recommendation.invoke({"user_id": user_id})

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
                "exercise_type": exercise_plan["exercise_type"],
                "duration": exercise_plan["duration"],
                "intensity": exercise_plan["intensity"],
                "reason": exercise_plan["reason"],
                "diet": f"每日建议摄入{calories.get('recommended_calories', 2000)}卡路里",
                "sleep_hours": 8,
                "water_intake": 2.5,
                "stretching": "建议睡前做15分钟拉伸"
            })

        logger.info(f"[GenerateRecommendation] user_id={user_id} recommendations_generated")
        return {
            "response": response,
            "recommendations": recommendations,
            "sources": []
        }
    except Exception as e:
        logger.error(f"[GenerateRecommendation] user_id={user_id} error={e}")
        raise


def quick_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Handle quick questions without deep search"""
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_message = messages[-1].content if messages else ""

    logger.info(f"[QuickAnswer] user_id={user_id} query={last_message[:50]}")

    profile = get_user_profile.invoke({"user_id": user_id})
    response = f"您好{profile.get('username', '')}！我是您的运动健康顾问。根据您的问题，我会尽量给您准确的建议。如果您想了解运动或饮食建议，请告诉我您的具体需求。"

    return {"response": response}


def update_profile_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Update user profile/preferences"""
    user_id = state.get("user_id")
    logger.info(f"[UpdateProfile] user_id={user_id}")
    return {"response": "偏好更新功能开发中..."}