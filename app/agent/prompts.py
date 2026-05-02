SYSTEM_PROMPT = """你是一个专业的运动健康顾问Agent。你需要根据用户的历史运动记录、饮食记录和偏好，提供个性化的运动和饮食建议。

你有以下工具可用：
- get_user_profile: 获取用户基本信息和偏好
- search_exercise_history: 搜索历史运动记录
- search_diet_history: 搜索历史饮食记录
- get_recovery_status: 获取用户当前恢复状态
- calculate_recommended_calories: 计算推荐每日卡路里摄入
- generate_exercise_plan: 生成运动计划
- generate_diet_recommendation: 生成饮食建议

请根据用户的问题，合理调用工具来生成准确的建议。始终以专业、友好的态度回复用户。
"""

USER_PROFILE_PROMPT = """基于以下用户信息回答：
用户ID: {user_id}
用户名: {username}
年龄: {age}
性别: {gender}
身高: {height}cm
体重: {weight}kg
健身目标: {fitness_goals}
约束条件: {constraints}
运动偏好: {exercise_preferences}
饮食偏好: {diet_preferences}
"""

EXERCISE_HISTORY_PROMPT = """用户的历史运动记录：
{history}
"""

DIET_HISTORY_PROMPT = """用户的历史饮食记录：
{history}
"""

RECOVERY_STATUS_PROMPT = """根据用户的运动记录分析恢复状态：
最近的运动: {recent_exercise}
运动强度: {intensity}
持续时间: {duration}分钟
恢复状态: {recovery_status}
"""

RECOMMENDATION_PROMPT = """基于用户的完整信息，生成个性化建议：
{context}
"""

def format_recommendation_response(data: dict) -> str:
    return f"""
运动建议：
- 类型: {data.get('exercise_type', 'N/A')}
- 时长: {data.get('duration', 'N/A')}分钟
- 强度: {data.get('intensity', 'N/A')}/10
- 原因: {data.get('reason', 'N/A')}

饮食建议：
{data.get('diet', '无特别建议')}

恢复建议：
- 睡眠: {data.get('sleep_hours', 'N/A')}小时
- 饮水: {data.get('water_intake', 'N/A')}升
- 拉伸: {data.get('stretching', 'N/A')}
"""