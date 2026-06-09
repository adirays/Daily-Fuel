from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

# ---------- User Profiles ----------
class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    age = Column(Integer)
    weight_kg = Column(Float)
    height_cm = Column(Float)
    gender = Column(String)
    activity_level = Column(String)
    goal = Column(String, nullable=True)
    allergies = Column(String, nullable=True)
    intolerances = Column(String, nullable=True)
    health_conditions = Column(String, nullable=True)
    fitness_goal = Column(String, nullable=True)
    target_calories = Column(Float, nullable=True)
    target_protein = Column(Float, nullable=True)
    target_carbs = Column(Float, nullable=True)
    target_fats = Column(Float, nullable=True)

# ---------- Foods ----------
class Food(Base):
    __tablename__ = "foods"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fats = Column(Float)
    barcode = Column(String, nullable=True)
    serving_size = Column(String, nullable=True)

# ---------- Daily Logs ----------
class DailyLog(Base):
    __tablename__ = "daily_logs"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    quantity = Column(Float)
    food_id = Column(Integer, ForeignKey("foods.id"))
    user_id = Column(Integer, ForeignKey("user_profiles.id"))
    food = relationship("Food")

# ---------- User Goals ----------
class UserGoal(Base):
    __tablename__ = "user_goals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"))
    calories_goal = Column(Float)
    protein_goal = Column(Float)
    carbs_goal = Column(Float)
    fats_goal = Column(Float)
