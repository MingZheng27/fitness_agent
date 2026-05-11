import logging
from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime
import uuid
import json

logger = logging.getLogger(__name__)

from app.api.schemas import (
    UserRegisterRequest, UserRegisterResponse,
    ExerciseRecordRequest, ExerciseRecordResponse,
    DietRecordRequest, DietRecordResponse,
    ChatRequest, ChatResponse,
    UserProfileResponse,
    UpdateUserProfileRequest, UpdateUserProfileResponse,
    UpdatePreferencesRequest, UpdatePreferencesResponse
)
from app.storage import mysql_client, chroma_client
from app.memory.long_term import long_term_memory
from app.memory.short_term import ShortTermMemory
from app.agent.graph import agent_graph
from langchain_core.messages import HumanMessage

router = APIRouter()


@router.post("/user/register", response_model=UserRegisterResponse)
async def register_user(req: UserRegisterRequest):
    try:
        user_id = mysql_client.create_user(
            tenant_id=req.tenant_id,
            username=req.username,
            age=req.age,
            gender=req.gender,
            height=req.height,
            weight=req.weight,
            fitness_goals=req.fitness_goals,
            constraints=req.constraints or {}
        )

        # Initialize ChromaDB collection for user
        chroma_client.get_collection(user_id)

        return UserRegisterResponse(
            user_id=user_id,
            message="用户注册成功",
            created_at=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/exercise/record", response_model=ExerciseRecordResponse)
async def record_exercise(req: ExerciseRecordRequest):
    try:
        record_id = mysql_client.create_exercise_record(
            user_id=req.user_id,
            date=req.date.isoformat(),
            exercise_type=req.exercise_type.value,
            duration_minutes=req.duration_minutes,
            intensity=req.intensity,
            calories_burned=req.calories_burned,
            recovery_status=req.recovery_status or "normal",
            notes=req.notes or ""
        )

        # Also add to ChromaDB for RAG
        record = {
            "id": record_id,
            "user_id": req.user_id,
            "date": req.date.isoformat(),
            "exercise_type": req.exercise_type.value,
            "duration_minutes": req.duration_minutes,
            "intensity": req.intensity,
            "calories_burned": req.calories_burned,
            "recovery_status": req.recovery_status or "normal",
            "notes": req.notes or ""
        }
        long_term_memory.write_exercise_record(req.user_id, record)

        return ExerciseRecordResponse(
            id=record_id,
            user_id=req.user_id,
            date=req.date,
            exercise_type=req.exercise_type,
            duration_minutes=req.duration_minutes,
            intensity=req.intensity,
            calories_burned=req.calories_burned,
            recovery_status=req.recovery_status,
            notes=req.notes,
            created_at=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/diet/record", response_model=DietRecordResponse)
async def record_diet(req: DietRecordRequest):
    try:
        foods_json = json.dumps([f.model_dump() for f in req.foods])
        nutrients_json = json.dumps(req.nutrients or {})

        record_id = mysql_client.create_diet_record(
            user_id=req.user_id,
            date=req.date.isoformat(),
            meal_type=req.meal_type.value,
            foods=foods_json,
            calories=req.calories,
            nutrients=nutrients_json
        )

        # Also add to ChromaDB for RAG
        record = {
            "id": record_id,
            "user_id": req.user_id,
            "date": req.date.isoformat(),
            "meal_type": req.meal_type.value,
            "foods": [f.model_dump() for f in req.foods],
            "calories": req.calories,
            "nutrients": req.nutrients or {}
        }
        long_term_memory.write_diet_record(req.user_id, record)

        return DietRecordResponse(
            id=record_id,
            user_id=req.user_id,
            date=req.date,
            meal_type=req.meal_type,
            foods=req.foods,
            calories=req.calories,
            nutrients=req.nutrients,
            created_at=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    conversation_id = req.conversation_id or str(uuid.uuid4())
    logger.info(f"[Chat] user_id={req.user_id} conversation_id={conversation_id} message={req.message[:50]}")

    try:
        # Create short-term memory for this conversation
        short_memory = ShortTermMemory()
        short_memory.add_message("user", req.message)

        # Run agent graph
        from app.config import get_settings
        settings = get_settings()

        result = agent_graph.invoke(
            {
                "user_id": req.user_id,
                "conversation_id": conversation_id,
                "messages": [HumanMessage(content=req.message)],
                "profile": {},
                "exercise_history": [],
                "diet_history": [],
                "recommendations": {},
                "response": "",
                "sources": [],
                "recent_context": {}
            },
            config={"recursion_limit": settings.langgraph_recursion_limit}
        )

        logger.info(f"[Chat] user_id={req.user_id} conversation_id={conversation_id} response_generated")
        return ChatResponse(
            response=result.get("response", "抱歉，我无法处理您的请求"),
            recommendations=result.get("recommendations", {}),
            sources=result.get("sources", []),
            conversation_id=conversation_id
        )
    except Exception as e:
        logger.error(f"[Chat] user_id={req.user_id} conversation_id={conversation_id} error={e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/profile", response_model=UserProfileResponse)
async def get_profile(user_id: str):
    from app.agent.tools import fetch_user_profile
    profile = fetch_user_profile(user_id)

    if "error" in profile:
        raise HTTPException(status_code=404, detail=profile["error"])

    # Get recent records
    exercises = mysql_client.get_exercise_records(user_id, limit=5)
    diets = mysql_client.get_diet_records(user_id, limit=5)

    last_exercise = exercises[0]["date"] if exercises else None
    last_diet = diets[0]["date"] if diets else None

    return UserProfileResponse(
        user_id=profile["user_id"],
        username=profile["username"],
        age=profile["age"],
        gender=profile["gender"],
        height=profile["height"],
        weight=profile["weight"],
        fitness_goals=profile["fitness_goals"],
        constraints=profile.get("constraints", {}),
        exercise_preferences=profile.get("exercise_preferences", {}),
        diet_preferences=profile.get("diet_preferences", {}),
        stats=profile.get("stats", {}),
        recent_summary={
            "last_exercise": last_exercise,
            "last_diet": last_diet,
            "weekly_goal_progress": 0.5
        }
    )


@router.put("/user/profile", response_model=UpdateUserProfileResponse)
async def update_profile(user_id: str, req: UpdateUserProfileRequest):
    try:
        logger.info(f"[UpdateProfile] user_id={user_id}")
        success = mysql_client.update_user(
            user_id=user_id,
            username=req.username,
            age=req.age,
            gender=req.gender,
            height=req.height,
            weight=req.weight,
            fitness_goals=req.fitness_goals,
            constraints=req.constraints
        )

        if not success:
            raise HTTPException(status_code=404, detail="用户不存在或更新失败")

        updated_fields = []
        if req.username is not None:
            updated_fields.append("username")
        if req.age is not None:
            updated_fields.append("age")
        if req.gender is not None:
            updated_fields.append("gender")
        if req.height is not None:
            updated_fields.append("height")
        if req.weight is not None:
            updated_fields.append("weight")
        if req.fitness_goals is not None:
            updated_fields.append("fitness_goals")
        if req.constraints is not None:
            updated_fields.append("constraints")

        return UpdateUserProfileResponse(
            user_id=user_id,
            message="用户画像更新成功",
            updated_fields=updated_fields,
            updated_at=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[UpdateProfile] user_id={user_id} error={e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/user/preferences", response_model=UpdatePreferencesResponse)
async def update_preferences(user_id: str, req: UpdatePreferencesRequest):
    try:
        exercise_prefs = json.dumps(req.exercise_preferences) if req.exercise_preferences else "{}"
        diet_prefs = json.dumps(req.diet_preferences) if req.diet_preferences else "{}"
        fitness_goals = json.dumps(req.fitness_goals) if req.fitness_goals else "[]"
        constraints = json.dumps(req.constraints) if req.constraints else "{}"

        logger.info(f"[UpdatePreferences] user_id={user_id} fields=exercise:{bool(req.exercise_preferences)} diet:{bool(req.diet_preferences)}")

        success = mysql_client.update_user_preferences(
            user_id=user_id,
            exercise_preferences=exercise_prefs,
            diet_preferences=diet_prefs,
            fitness_goals=fitness_goals,
            constraints=constraints
        )

        if not success:
            raise HTTPException(status_code=404, detail="用户不存在或更新失败")

        updated_fields = []
        if req.exercise_preferences:
            updated_fields.append("exercise_preferences")
        if req.diet_preferences:
            updated_fields.append("diet_preferences")
        if req.fitness_goals:
            updated_fields.append("fitness_goals")
        if req.constraints:
            updated_fields.append("constraints")

        logger.info(f"[UpdatePreferences] user_id={user_id} success fields={updated_fields}")
        return UpdatePreferencesResponse(
            user_id=user_id,
            message="用户偏好更新成功",
            updated_fields=updated_fields,
            updated_at=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[UpdatePreferences] user_id={user_id} error={e}")
        raise HTTPException(status_code=400, detail=str(e))
