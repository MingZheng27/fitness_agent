import logging
from typing import Dict, Any, List, Optional
from app.storage import mysql_client, chroma_client
from app.memory.long_term import long_term_memory
from app.config import get_settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from app.agent.prompts import AGENT_SYSTEM_PROMPT
import json

logger = logging.getLogger(__name__)


def get_llm():
    """Get or create LLM client (singleton)"""
    if not hasattr(get_llm, '_llm'):
        settings = get_settings()
        get_llm._llm = ChatOpenAI(
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            temperature=settings.llm_temperature
        )
        logger.info(f"[LLM] Initialized with model={settings.llm_model}, base_url={settings.llm_base_url}")
    return get_llm._llm


def fetch_user_profile(user_id: str) -> Dict[str, Any]:
    logger.info(f"[Tool] get_user_profile called for user_id={user_id}")
    try:
        user = mysql_client.get_user(user_id)
        if not user:
            logger.warning(f"[Tool] get_user_profile: user not found user_id={user_id}")
            return {"error": "用户不存在"}

        preferences = mysql_client.get_user_preferences(user_id)
        stats = mysql_client.get_user_stats(user_id)

        fitness_goals = user.get("fitness_goals", "[]")
        if isinstance(fitness_goals, str):
            fitness_goals = json.loads(fitness_goals)

        constraints = user.get("constraints", "{}")
        if isinstance(constraints, str):
            constraints = json.loads(constraints)

        exercise_prefs = {}
        diet_prefs = {}
        if preferences:
            ep = preferences.get("exercise_preferences", "{}")
            if isinstance(ep, str):
                exercise_prefs = json.loads(ep) if ep else {}
            else:
                exercise_prefs = ep or {}

            dp = preferences.get("diet_preferences", "{}")
            if isinstance(dp, str):
                diet_prefs = json.loads(dp) if dp else {}
            else:
                diet_prefs = dp or {}

        result = {
            "user_id": user_id,
            "username": user.get("username", ""),
            "age": user.get("age", 0),
            "gender": user.get("gender", ""),
            "height": user.get("height", 0),
            "weight": user.get("weight", 0),
            "fitness_goals": fitness_goals,
            "constraints": constraints,
            "exercise_preferences": exercise_prefs,
            "diet_preferences": diet_prefs,
            "stats": stats
        }
        logger.info(f"[Tool] get_user_profile success user_id={user_id}")
        return result
    except Exception as e:
        logger.error(f"[Tool] get_user_profile error user_id={user_id} error={e}")
        raise


@tool
def get_user_profile(user_id: str) -> Dict[str, Any]:
    """获取用户基本信息和偏好，包括年龄、性别、身高、体重、健身目标、运动偏好、饮食偏好等"""
    return fetch_user_profile(user_id)


def fetch_exercise_history(user_id: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    logger.info(f"[Tool] search_exercise_history called user_id={user_id} query={query[:50]}")
    try:
        results = long_term_memory.search_exercise_history(user_id, query, n_results)
        logger.info(f"[Tool] search_exercise_history success user_id={user_id} results_count={len(results)}")
        return results
    except Exception as e:
        logger.error(f"[Tool] search_exercise_history error user_id={user_id} error={e}")
        raise


@tool
def search_exercise_history(user_id: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """搜索用户的历史运动记录，返回与查询相关的运动记录"""
    return fetch_exercise_history(user_id, query, n_results)


def fetch_diet_history(user_id: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    logger.info(f"[Tool] search_diet_history called user_id={user_id} query={query[:50]}")
    try:
        results = long_term_memory.search_diet_history(user_id, query, n_results)
        logger.info(f"[Tool] search_diet_history success user_id={user_id} results_count={len(results)}")
        return results
    except Exception as e:
        logger.error(f"[Tool] search_diet_history error user_id={user_id} error={e}")
        raise


@tool
def search_diet_history(user_id: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """搜索用户的历史饮食记录，返回与查询相关的饮食记录"""
    return fetch_diet_history(user_id, query, n_results)


def fetch_recovery_status(user_id: str) -> Dict[str, Any]:
    logger.info(f"[Tool] get_recovery_status called user_id={user_id}")
    try:
        records = mysql_client.get_exercise_records(user_id, limit=3)
        if not records:
            logger.info(f"[Tool] get_recovery_status: no records user_id={user_id}")
            return {"status": "unknown", "message": "暂无运动记录"}

        latest = records[0]
        avg_intensity = sum(r.get("intensity", 5) for r in records) / len(records)

        if avg_intensity >= 7:
            recovery_status = "需要休息"
            recommended_intensity = 3
        elif avg_intensity >= 5:
            recovery_status = "轻度疲劳"
            recommended_intensity = 5
        else:
            recovery_status = "状态良好"
            recommended_intensity = 7

        result = {
            "status": recovery_status,
            "recent_exercise": latest.get("exercise_type"),
            "avg_intensity": round(avg_intensity, 1),
            "recommended_intensity": recommended_intensity,
            "message": f"基于最近{len(records)}次运动记录分析，您的恢复状态为{recovery_status}，建议运动强度{recommended_intensity}/10"
        }
        logger.info(f"[Tool] get_recovery_status success user_id={user_id} status={recovery_status}")
        return result
    except Exception as e:
        logger.error(f"[Tool] get_recovery_status error user_id={user_id} error={e}")
        raise


@tool
def get_recovery_status(user_id: str) -> Dict[str, Any]:
    """获取用户当前的恢复状态，基于最近几次运动记录分析"""
    return fetch_recovery_status(user_id)


def fetch_recommended_calories(user_id: str) -> Dict[str, Any]:
    logger.info(f"[Tool] calculate_recommended_calories called user_id={user_id}")
    try:
        user = mysql_client.get_user(user_id)
        if not user:
            logger.warning(f"[Tool] calculate_recommended_calories: user not found user_id={user_id}")
            return {"error": "用户不存在"}

        weight = float(user.get("weight", 70))
        height = float(user.get("height", 170))
        age = int(user.get("age", 30))
        gender = user.get("gender", "male")

        if gender == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        tdee = bmr * 1.55

        fitness_goals = json.loads(user.get("fitness_goals", "[]"))
        if "weight_loss" in fitness_goals:
            target_calories = tdee - 500
        elif "muscle_gain" in fitness_goals:
            target_calories = tdee + 300
        else:
            target_calories = tdee

        result = {
            "bmr": round(bmr, 0),
            "tdee": round(tdee, 0),
            "recommended_calories": round(target_calories, 0),
            "message": f"根据您的身体数据，每日建议摄入{round(target_calories, 0)}卡路里以达到您的健身目标"
        }
        logger.info(f"[Tool] calculate_recommended_calories success user_id={user_id} recommended_calories={target_calories}")
        return result
    except Exception as e:
        logger.error(f"[Tool] calculate_recommended_calories error user_id={user_id} error={e}")
        raise


@tool
def calculate_recommended_calories(user_id: str) -> Dict[str, Any]:
    """根据用户的身体数据（体重、身高、年龄、性别）和健身目标，计算每日推荐的卡路里摄入量"""
    return fetch_recommended_calories(user_id)


def build_exercise_plan(user_id: str, intensity: int = 5, duration: int = 30) -> Dict[str, Any]:
    logger.info(f"[Tool] generate_exercise_plan called user_id={user_id} intensity={intensity}")
    try:
        recovery = fetch_recovery_status(user_id)

        exercise_types = {
            1: {"type": "walking", "duration": 20, "intensity": 1, "reason": "极轻度活动，促进血液循环"},
            2: {"type": "yoga", "duration": 30, "intensity": 2, "reason": "柔韧性训练，帮助恢复"},
            3: {"type": "hiking", "duration": 30, "intensity": 3, "reason": "低强度有氧，促进恢复"},
            4: {"type": "cycling", "duration": 40, "intensity": 4, "reason": "中等有氧，增强心肺功能"},
            5: {"type": "swimming", "duration": 45, "intensity": 5, "reason": "全身运动，强度适中"},
            6: {"type": "running", "duration": 30, "intensity": 6, "reason": "提升耐力，消耗热量"},
            7: {"type": "basketball", "duration": 45, "intensity": 7, "reason": "高强度训练，全面锻炼"},
            8: {"type": "strength_training", "duration": 50, "intensity": 8, "reason": "力量训练，增肌塑形"},
            9: {"type": "strength_training", "duration": 60, "intensity": 9, "reason": "高强度力量训练"},
            10: {"type": "hiit", "duration": 25, "intensity": 10, "reason": "极限挑战，燃烧脂肪"}
        }

        plan = exercise_types.get(intensity, exercise_types[5])

        result = {
            "exercise_type": plan["type"],
            "duration": plan["duration"],
            "intensity": plan["intensity"],
            "reason": plan["reason"],
            "recovery_advice": recovery.get("message", "")
        }
        logger.info(f"[Tool] generate_exercise_plan success user_id={user_id} type={plan['type']}")
        return result
    except Exception as e:
        logger.error(f"[Tool] generate_exercise_plan error user_id={user_id} error={e}")
        raise


@tool
def generate_exercise_plan(user_id: str, intensity: int = 5, duration: int = 30) -> Dict[str, Any]:
    """根据指定的运动强度和时长生成运动计划，包含运动类型、时长、强度和原因"""
    return build_exercise_plan(user_id, intensity, duration)


def build_diet_recommendation(user_id: str, meal_type: str = "general") -> Dict[str, Any]:
    logger.info(f"[Tool] generate_diet_recommendation called user_id={user_id} meal_type={meal_type}")
    try:
        calories_info = fetch_recommended_calories(user_id)
        target = calories_info.get("recommended_calories", 2000)

        recommendations = {
            "breakfast": {
                "suggestions": ["燕麦+香蕉+牛奶", "全麦面包+鸡蛋+水果", "酸奶+坚果+浆果"],
                "calories": int(target * 0.25),
                "reason": "早餐是一天中最重要的一餐，补充夜间消耗的能量"
            },
            "lunch": {
                "suggestions": ["鸡胸肉+糙米+蔬菜", "鱼肉+藜麦+沙拉", "牛肉+红薯+绿叶菜"],
                "calories": int(target * 0.35),
                "reason": "午餐提供下午工作/运动的能量"
            },
            "dinner": {
                "suggestions": ["鱼类+蔬菜沙拉", "豆腐+糙米+蔬菜", "鸡胸肉+西兰花"],
                "calories": int(target * 0.30),
                "reason": "晚餐以轻食为主，帮助消化和恢复"
            },
            "snacks": {
                "suggestions": ["坚果+水果", "酸奶", "蛋白棒"],
                "calories": int(target * 0.10),
                "reason": "健康零食补充营养，避免过度饥饿"
            }
        }

        if meal_type == "general":
            result = {
                "total_calories": target,
                "meals": recommendations
            }
        else:
            result = {
                "calories": recommendations.get(meal_type, {}).get("calories", 0),
                "suggestions": recommendations.get(meal_type, {}).get("suggestions", []),
                "reason": recommendations.get(meal_type, {}).get("reason", "")
            }
        logger.info(f"[Tool] generate_diet_recommendation success user_id={user_id} total_calories={target}")
        return result
    except Exception as e:
        logger.error(f"[Tool] generate_diet_recommendation error user_id={user_id} error={e}")
        raise


@tool
def generate_diet_recommendation(user_id: str, meal_type: str = "general") -> Dict[str, Any]:
    """根据用户的目标卡路里生成饮食建议，可以指定某一餐或返回全天的饮食建议"""
    return build_diet_recommendation(user_id, meal_type)


# Available tools list for binding to LLM
AVAILABLE_TOOLS = [
    get_user_profile,
    search_exercise_history,
    search_diet_history,
    get_recovery_status,
    calculate_recommended_calories,
    generate_exercise_plan,
    generate_diet_recommendation,
]


def call_llm_with_tools(
    user_id: str,
    user_message: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """使用工具调用模式调用LLM，LLM会根据需要调用工具获取信息后生成最终建议"""
    settings = get_settings()
    max_iterations = settings.llm_max_iterations

    logger.info(f"[LLM] call_llm_with_tools user_id={user_id} max_iterations={max_iterations}")

    llm = get_llm()
    llm_with_tools = llm.bind_tools(AVAILABLE_TOOLS)

    messages = [SystemMessage(content=AGENT_SYSTEM_PROMPT)]

    if conversation_history:
        for msg in conversation_history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg.get("content", "")))

    messages.append(HumanMessage(content=f"用户ID: {user_id}\n用户问题: {user_message}"))

    iteration = 0
    tool_results = {}

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"[LLM] iteration={iteration}/{max_iterations} user_id={user_id}")
        response = llm_with_tools.invoke(messages)

        if not hasattr(response, "tool_calls") or not response.tool_calls:
            content = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"[LLM] no tool calls, response content={content[:100] if content else 'empty'}")
            if content:
                try:
                    import re
                    json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                        logger.info(f"[LLM] parsed JSON result user_id={user_id}")
                        return result
                except Exception as e:
                    logger.error(f"[LLM] JSON parse error user_id={user_id} error={e}")
            logger.warning(f"[LLM] no valid JSON in response user_id={user_id}")
            return {"error": "无法生成有效建议", "raw_response": content}

        for tool_call in response.tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            logger.info(f"[LLM] tool_call iteration={iteration} tool_name={tool_name} args={tool_args}")

            if tool_name not in tool_results:
                try:
                    result = execute_tool(tool_name, tool_args)
                    tool_results[tool_name] = result
                    messages.append(AIMessage(content=f"tool_call: {tool_call}"))
                    messages.append(AIMessage(content=f"tool_result: {json.dumps(result, ensure_ascii=False)}"))
                    logger.info(f"[LLM] tool executed successfully tool_name={tool_name}")
                except Exception as e:
                    error_msg = f"工具执行失败: {str(e)}"
                    logger.error(f"[LLM] tool execution failed tool_name={tool_name} error={e}")
                    messages.append(AIMessage(content=error_msg))
                    return {"error": error_msg}
            else:
                logger.info(f"[LLM] reusing cached tool result tool_name={tool_name}")
                messages.append(AIMessage(content=f"tool_result: {json.dumps(tool_results[tool_name], ensure_ascii=False)}"))

    logger.warning(f"[LLM] max iterations reached user_id={user_id}")
    return {"error": "达到最大迭代次数"}


def execute_tool(tool_name: str, args: Dict[str, Any]) -> Any:
    """Execute a tool by name with given arguments"""
    logger.info(f"[Execute] tool_name={tool_name} args={args}")
    tool_map = {
        "get_user_profile": get_user_profile,
        "search_exercise_history": search_exercise_history,
        "search_diet_history": search_diet_history,
        "get_recovery_status": get_recovery_status,
        "calculate_recommended_calories": calculate_recommended_calories,
        "generate_exercise_plan": generate_exercise_plan,
        "generate_diet_recommendation": generate_diet_recommendation,
    }

    tool = tool_map.get(tool_name)
    if not tool:
        logger.error(f"[Execute] unknown tool: {tool_name}")
        return {"error": f"未知工具: {tool_name}"}

    result = tool.invoke(args)
    logger.info(f"[Execute] tool executed: {tool_name}")
    return result
