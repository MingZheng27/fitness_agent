import logging
from typing import Dict, Any, List
from datetime import datetime
from app.storage import mysql_client, chroma_client
from app.api.schemas import ExerciseType
import json

logger = logging.getLogger(__name__)

EXERCISE_TYPE_MAP = {
    1: "running",
    2: "swimming",
    3: "hiking",
    4: "cycling",
    5: "strength_training",
    6: "yoga",
    7: "basketball",
    8: "football",
    9: "tennis",
    10: "badminton",
    11: "walking",
    12: "skipping",
    13: "dance",
    99: "other"
}


class LongTermMemory:
    def write_exercise_record(self, user_id: str, record: Dict[str, Any]):
        try:
            content = self._format_exercise_content(record)
            exercise_type_val = record.get("exercise_type")
            if isinstance(exercise_type_val, int):
                exercise_type_val = EXERCISE_TYPE_MAP.get(exercise_type_val, exercise_type_val)

            doc = {
                "id": record["id"],
                "user_id": user_id,
                "content": content,
                "metadata": {
                    "type": "exercise",
                    "date": record["date"],
                    "exercise_type": exercise_type_val,
                    "intensity": record.get("intensity"),
                    "recovery_status": record.get("recovery_status", "normal")
                }
            }
            chroma_client.add_document(user_id, doc)
            logger.info(f"[LongTermMemory] exercise record written user_id={user_id} record_id={record['id']}")
        except Exception as e:
            logger.error(f"[LongTermMemory] write_exercise_record failed user_id={user_id} error={e}")
            raise

    def write_diet_record(self, user_id: str, record: Dict[str, Any]):
        try:
            content = self._format_diet_content(record)
            doc = {
                "id": record["id"],
                "user_id": user_id,
                "content": content,
                "metadata": {
                    "type": "diet",
                    "date": record["date"],
                    "meal_type": record["meal_type"]
                }
            }
            chroma_client.add_document(user_id, doc)
            logger.info(f"[LongTermMemory] diet record written user_id={user_id} record_id={record['id']}")
        except Exception as e:
            logger.error(f"[LongTermMemory] write_diet_record failed user_id={user_id} error={e}")
            raise

    def search_exercise_history(self, user_id: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        results = chroma_client.search(user_id, query, n_results)
        filtered = [r for r in results.get("documents", [[]])[0] if "exercise" in str(results.get("metadatas", [[]])[0])]
        return filtered

    def search_diet_history(self, user_id: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        results = chroma_client.search(user_id, query, n_results)
        filtered = [r for r in results.get("documents", [[]])[0] if "diet" in str(results.get("metadatas", [[]])[0])]
        return filtered

    def _format_exercise_content(self, record: Dict[str, Any]) -> str:
        exercise_type = record.get("exercise_type")
        if isinstance(exercise_type, int):
            exercise_type = EXERCISE_TYPE_MAP.get(exercise_type, f"type_{exercise_type}")
        return f"运动记录：{record['date']}完成了{exercise_type}，持续{record.get('duration_minutes', '未知')}分钟，强度{record.get('intensity', '未知')}/10，消耗{record.get('calories_burned', '未知')}卡路里，恢复状态{record.get('recovery_status', 'normal')}。备注：{record.get('notes', '无')}"

    def _format_diet_content(self, record: Dict[str, Any]) -> str:
        foods = record.get("foods", [])
        foods_str = ", ".join([f"{f['name']}{f['portion']}" for f in foods])
        nutrients = record.get("nutrients", {})
        return f"饮食记录：{record['date']}{record['meal_type']}吃了{foods_str}，总热量{record.get('calories', '未知')}卡，蛋白质{nutrients.get('protein', '未知')}g，碳水{nutrients.get('carbs', '未知')}g，脂肪{nutrients.get('fat', '未知')}g"


long_term_memory = LongTermMemory()