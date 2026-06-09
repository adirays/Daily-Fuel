from datetime import date
from typing import Optional, List, Any, Dict
from pydantic import BaseModel

# ---------- Food ----------
class FoodBase(BaseModel):
    name: str
    calories: float
    protein: float
    carbs: float
    fats: float

class FoodCreate(FoodBase):
    pass

class Food(FoodBase):
    id: int

    class Config:
        from_attributes = True

# ---------- DailyLog ----------
class DailyLogBase(BaseModel):
    quantity: float
    food_id: int
    user_id: int

class DailyLogCreate(DailyLogBase):
    date: str  # Accept date as string from Flutter

class DailyLogUpdate(BaseModel):
    quantity: Optional[float] = None
    food_id: Optional[int] = None
    date: Optional[str] = None

class DailyLog(DailyLogBase):
    id: int
    date: date  # Database returns date object
    food: Optional[Food] = None

    class Config:
        from_attributes = True

# ---------- Totals ----------
class DailyTotals(BaseModel):
    date: date
    calories: float
    protein: float
    carbs: float
    fats: float

# ---------- Goals ----------  # 🔹 CHANGES: Use *_goal to match DB columns
class UserGoalBase(BaseModel):
    calories_goal: float
    protein_goal: float
    carbs_goal: float
    fats_goal: float

class UserGoalCreate(UserGoalBase):
    user_id: int  # Add this field

class UserGoalUpdate(UserGoalBase):
    pass  # No additional fields needed for updates

class UserGoal(UserGoalBase):
    id: int

    class Config:
        from_attributes = True

# ---------- User Profiles ----------
class UserProfileBase(BaseModel):
    name: str
    age: int
    weight_kg: float
    height_cm: float
    gender: str
    activity_level: str
    goal: Optional[str] = None

class UserProfileCreate(UserProfileBase):
    pass

class UserProfile(UserProfileBase):
    id: int

    class Config:
        from_attributes = True

class UserProfileResponse(UserProfileBase):
    id: int

    class Config:
        from_attributes = True

class FactOut(BaseModel):
    food_name: str
    recommended: bool
    reason: str

class ChatRequest(BaseModel):
    query: str
    user_id: int

class NutritionResult(BaseModel):
    score: float  # 0-100 nutritional score
    recommended: bool
    confidence: float  # 0.6-0.95 confidence level
    reasoning: str
    nutritional_breakdown: Dict[str, float]  # Component scores
    nutritional_details: Dict[str, float]  # Raw nutritional data

class ClassifyRequest(BaseModel):
    food_name: str
    user_id: int
