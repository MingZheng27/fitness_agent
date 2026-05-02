from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


class ExerciseType(int, Enum):
    running = 1
    swimming = 2
    hiking = 3
    cycling = 4
    strength_training = 5
    yoga = 6
    basketball = 7
    football = 8
    tennis = 9
    badminton = 10
    walking = 11
    skipping = 12
    dance = 13
    other = 99


class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"


# User registration
class UserRegisterRequest(BaseModel):
    tenant_id: str
    username: str
    age: int
    gender: str
    height: float
    weight: float
    fitness_goals: List[str]
    constraints: Optional[Dict[str, Any]] = {}


class UserRegisterResponse(BaseModel):
    user_id: str
    message: str
    created_at: datetime


# Exercise record
class ExerciseRecordRequest(BaseModel):
    user_id: str
    date: date
    exercise_type: ExerciseType
    duration_minutes: Optional[int] = None
    intensity: Optional[int] = Field(None, ge=1, le=10)
    calories_burned: Optional[int] = None
    recovery_status: Optional[str] = "normal"
    notes: Optional[str] = None


class ExerciseRecordResponse(BaseModel):
    id: str
    user_id: str
    date: date
    exercise_type: int
    duration_minutes: Optional[int] = None
    intensity: Optional[int] = None
    calories_burned: Optional[int] = None
    recovery_status: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


# Diet record
class FoodItem(BaseModel):
    name: str
    portion: str


class DietRecordRequest(BaseModel):
    user_id: str
    date: date
    meal_type: MealType
    foods: List[FoodItem]
    calories: Optional[int] = None
    nutrients: Optional[Dict[str, float]] = {}


class DietRecordResponse(BaseModel):
    id: str
    user_id: str
    date: date
    meal_type: MealType
    foods: List[FoodItem]
    calories: Optional[int] = None
    nutrients: Optional[Dict[str, float]] = {}
    created_at: datetime


# Chat
class ChatRequest(BaseModel):
    user_id: str
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    recommendations: Optional[Dict[str, Any]] = {}
    sources: List[str] = []
    conversation_id: str


# User profile
class UserProfileResponse(BaseModel):
    user_id: str
    username: str
    age: int
    gender: str
    height: float
    weight: float
    fitness_goals: List[str]
    exercise_preferences: Dict[str, Any] = {}
    diet_preferences: Dict[str, Any] = {}
    stats: Dict[str, Any] = {}
    recent_summary: Dict[str, Any] = {}


# Update preferences
class UpdatePreferencesRequest(BaseModel):
    exercise_preferences: Optional[Dict[str, Any]] = None
    diet_preferences: Optional[Dict[str, Any]] = None
    fitness_goals: Optional[List[str]] = None
    constraints: Optional[Dict[str, Any]] = None


class UpdatePreferencesResponse(BaseModel):
    user_id: str
    message: str
    updated_fields: List[str]
    updated_at: datetime