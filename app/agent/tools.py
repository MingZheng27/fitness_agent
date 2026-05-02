from typing import Dict, Any, List
from app.storage import mysql_client, chroma_client
from app.memory.long_term import long_term_memory
import json


def get_user_profile(user_id: str) -> Dict[str, Any]:
    user = mysql_client.get_user(user_id)
    if not user:
        return {"error": "用户不存在"}

    preferences = mysql_client.get_user_preferences(user_id)
    stats = mysql_client.get_user_stats(user_id)

    # Parse JSON fields
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

    return {
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


def search_exercise_history(user_id: str, query: str, n_results: int = 5) -> List[str]:
    results = long_term_memory.search_exercise_history(user_id, query, n_results)
    return results


def search_diet_history(user_id: str, query: str, n_results: int = 5) -> List[str]:
    results = long_term_memory.search_diet_history(user_id, query, n_results)
    return results


def get_recovery_status(user_id: str) -> Dict[str, Any]:
    records = mysql_client.get_exercise_records(user_id, limit=3)
    if not records:
        return {"status": "unknown", "message": "暂无运动记录"}

    latest = records[0]
    avg_intensity = sum(r.get("intensity", 5) for r in records) / len(records)

    # Simple recovery estimation based on recent activity
    if avg_intensity >= 7:
        recovery_status = "需要休息"
        recommended_intensity = 3
    elif avg_intensity >= 5:
        recovery_status = "轻度疲劳"
        recommended_intensity = 5
    else:
        recovery_status = "状态良好"
        recommended_intensity = 7

    return {
        "status": recovery_status,
        "recent_exercise": latest.get("exercise_type"),
        "avg_intensity": round(avg_intensity, 1),
        "recommended_intensity": recommended_intensity,
        "message": f"基于最近{len(records)}次运动记录分析，您的恢复状态为{recovery_status}，建议运动强度{recommended_intensity}/10"
    }


def calculate_recommended_calories(user_id: str) -> Dict[str, Any]:
    user = mysql_client.get_user(user_id)
    if not user:
        return {"error": "用户不存在"}

    weight = float(user.get("weight", 70))
    height = float(user.get("height", 170))
    age = int(user.get("age", 30))
    gender = user.get("gender", "male")

    # Basic BMR calculation (Mifflin-St Jeor)
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # Assuming light activity (1.55 multiplier for most people)
    tdee = bmr * 1.55

    # For fitness goals
    fitness_goals = json.loads(user.get("fitness_goals", "[]"))
    if "weight_loss" in fitness_goals:
        target_calories = tdee - 500  # 500 calorie deficit
    elif "muscle_gain" in fitness_goals:
        target_calories = tdee + 300  # 300 calorie surplus
    else:
        target_calories = tdee

    return {
        "bmr": round(bmr, 0),
        "tdee": round(tdee, 0),
        "recommended_calories": round(target_calories, 0),
        "message": f"根据您的身体数据，每日建议摄入{round(target_calories, 0)}卡路里以达到您的健身目标"
    }


def generate_exercise_plan(user_id: str, intensity: int = 5, duration: int = 30) -> Dict[str, Any]:
    recovery = get_recovery_status(user_id)

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

    return {
        "exercise_type": plan["type"],
        "duration": plan["duration"],
        "intensity": plan["intensity"],
        "reason": plan["reason"],
        "recovery_advice": recovery.get("message", "")
    }


def generate_diet_recommendation(user_id: str, meal_type: str = "general") -> Dict[str, Any]:
    calories_info = calculate_recommended_calories(user_id)
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
        return {
            "total_calories": target,
            "meals": recommendations
        }
    else:
        return {
            "calories": recommendations.get(meal_type, {}).get("calories", 0),
            "suggestions": recommendations.get(meal_type, {}).get("suggestions", []),
            "reason": recommendations.get(meal_type, {}).get("reason", "")
        }