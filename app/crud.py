from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
# Remove: from fastapi import HTTPException
from . import models, schemas
from .utils import calculate_targets
from datetime import date
from typing import Optional
from pydantic import BaseModel

# ---------- User Profiles ----------
def create_user_profile(db: Session, profile: schemas.UserProfileCreate):
    db_profile = models.UserProfile(
        name=profile.name,
        age=profile.age,
        weight_kg=profile.weight_kg,
        height_cm=profile.height_cm,
        gender=profile.gender,
        activity_level=profile.activity_level,
        goal=profile.goal,
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)

    cals, protein, carbs, fats = calculate_targets(db, db_profile.id)
    db_profile.target_calories = cals
    db_profile.target_protein = protein
    db_profile.target_carbs = carbs
    db_profile.target_fats = fats

    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def get_user_profile(db: Session, user_id: int):
    profile = db.query(models.UserProfile).filter(models.UserProfile.id == user_id).first()
    if not profile:
        raise ValueError(f"User profile {user_id} not found")
    return profile

def get_user_profile_by_id(db: Session, user_id: int):
    return db.query(models.UserProfile).filter(models.UserProfile.id == user_id).first()


def get_user_profiles(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.UserProfile).offset(skip).limit(limit).all()

def update_user_profile(db: Session, user_id: int, profile: schemas.UserProfileCreate):
    db_profile = get_user_profile(db, user_id)
    if not db_profile:
        raise ValueError(f"User profile {user_id} not found")

    for var, value in vars(profile).items():
        setattr(db_profile, var, value) if value else None

    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

# ---------- Foods ----------
def create_food(db: Session, food: schemas.FoodCreate):
    # Explicitly exclude id field to ensure auto-generation
    food_data = food.dict()
    if 'id' in food_data:
        del food_data['id']
    
    db_food = models.Food(**food_data)
    db.add(db_food)
    db.commit()
    db.refresh(db_food)
    
    # Ensure we got a valid ID
    if db_food.id is None or db_food.id == 0:
        db.rollback()
        raise ValueError("Failed to create food - invalid ID generated")
    
    return db_food

def get_foods(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Food).offset(skip).limit(limit).all()

def get_food(db: Session, food_id: int):
    return db.query(models.Food).filter(models.Food.id == food_id).first()

def get_food_by_name(db: Session, food_name: str):
    return db.query(models.Food).filter(models.Food.name == food_name).first()

# ---------- Daily Logs ----------
def create_daily_log(db: Session, log: schemas.DailyLogCreate):
    # Check if food_id exists
    food = db.query(models.Food).filter(models.Food.id == log.food_id).first()
    if not food:
        raise ValueError(f"Food with ID {log.food_id} not found")

    # Check if user_id exists
    user = db.query(models.UserProfile).filter(models.UserProfile.id == log.user_id).first()
    if not user:
        raise ValueError(f"User with ID {log.user_id} not found")

    # Parse the date string to date object
    try:
        log_date = date.fromisoformat(log.date)
    except ValueError:
        raise ValueError(f"Invalid date format: {log.date}. Expected yyyy-MM-dd")

    # Check for duplicate log (same user, food, date)
    existing_log = db.query(models.DailyLog).filter(
        models.DailyLog.user_id == log.user_id,
        models.DailyLog.food_id == log.food_id,
        models.DailyLog.date == log_date
    ).first()
    
    if existing_log:
        # Update quantity instead of creating duplicate
        existing_log.quantity += log.quantity
        db.commit()
        db.refresh(existing_log)
        return existing_log

    db_log = models.DailyLog(
        date=log_date,
        quantity=log.quantity,
        user_id=log.user_id,
        food_id=log.food_id
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_logs_by_date(db: Session, date: str):
    return db.query(models.DailyLog).filter(models.DailyLog.date == date).options(joinedload(models.DailyLog.food)).all()

def get_all_logs(db: Session):
    return db.query(models.DailyLog).options(joinedload(models.DailyLog.food)).all()

def get_logs_by_user(db: Session, user_id: int, limit: int = 5):
    """Retrieve the most recent DailyLog entries for a user."""
    return (
        db.query(models.DailyLog)
        .filter(models.DailyLog.user_id == user_id)
        .order_by(models.DailyLog.date.desc())
        .limit(limit)
        .options(joinedload(models.DailyLog.food))
        .all()
    )

def get_logs_by_date_and_user(db: Session, user_id: int, date: str):
    return db.query(models.DailyLog).filter(
        models.DailyLog.user_id == user_id,
        models.DailyLog.date == date
    ).options(joinedload(models.DailyLog.food)).all()

def get_daily_totals(db: Session, date: str):
    totals = (
        db.query(
            func.sum(models.Food.calories * models.DailyLog.quantity).label("calories"),
            func.sum(models.Food.protein * models.DailyLog.quantity).label("protein"),
            func.sum(models.Food.carbs * models.DailyLog.quantity).label("carbs"),
            func.sum(models.Food.fats * models.DailyLog.quantity).label("fats"),
        )
        .join(models.Food, models.DailyLog.food_id == models.Food.id)
        .filter(models.DailyLog.date == date)
        .first()
    )

    if totals and any(totals):
        return {
            "calories": totals.calories or 0,
            "protein": totals.protein or 0,
            "carbs": totals.carbs or 0,
            "fats": totals.fats or 0,
        }
    else:
        return {
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fats": 0,
        }

def delete_daily_log(db: Session, log_id: int):
    db_log = db.query(models.DailyLog).filter(models.DailyLog.id == log_id).first()
    if not db_log:
        raise ValueError(f"Log with ID {log_id} not found")
    db.delete(db_log)
    db.commit()
    return {"ok": True}

def update_daily_log(db: Session, log_id: int, log_update: schemas.DailyLogUpdate):
    db_log = db.query(models.DailyLog).filter(models.DailyLog.id == log_id).first()
    if not db_log:
        raise ValueError(f"Log with ID {log_id} not found")

    # Update fields if provided
    if log_update.quantity is not None:
        db_log.quantity = log_update.quantity
    if log_update.food_id is not None:
        # Check if food_id exists
        food = db.query(models.Food).filter(models.Food.id == log_update.food_id).first()
        if not food:
            raise ValueError(f"Food with ID {log_update.food_id} not found")
        db_log.food_id = log_update.food_id
    if log_update.date is not None:
        try:
            log_date = date.fromisoformat(log_update.date)
            db_log.date = log_date
        except ValueError:
            raise ValueError(f"Invalid date format: {log_update.date}. Expected yyyy-MM-dd")

    db.commit()
    db.refresh(db_log)
    return db_log

def update_goal(db: Session, goal_id: int, goal: schemas.UserGoalUpdate):
    db_goal = db.query(models.UserGoal).filter(models.UserGoal.id == goal_id).first()
    if not db_goal:
        raise ValueError(f"Goal with ID {goal_id} not found")

    # Update the goal fields
    db_goal.calories_goal = goal.calories_goal
    db_goal.protein_goal = goal.protein_goal
    db_goal.carbs_goal = goal.carbs_goal
    db_goal.fats_goal = goal.fats_goal

    db.commit()
    db.refresh(db_goal)
    return db_goal

# ---------- User Goals ----------
def set_goal(db: Session, goal: schemas.UserGoalCreate):
    db_user = db.query(models.UserProfile).filter(models.UserProfile.id == goal.user_id).first()
    if not db_user:
        raise ValueError(f"User {goal.user_id} not found")
    db_goal = models.UserGoal(**goal.dict())
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

def get_goals(db: Session):
    return db.query(models.UserGoal).all()

def get_user_goals(db: Session, user_id: int):
    db_goals = db.query(models.UserGoal).filter(models.UserGoal.user_id == user_id).all()
    if not db_goals:
        return []
    return db_goals

def get_daily_totals_by_user(db: Session, user_id: int, date: str):
    """Get daily nutrition totals for a specific user and date."""
    
    # Use select_from to avoid join ambiguity
    totals = (
        db.query(
            func.sum(models.Food.calories * models.DailyLog.quantity).label("calories"),
            func.sum(models.Food.protein * models.DailyLog.quantity).label("protein"),
            func.sum(models.Food.carbs * models.DailyLog.quantity).label("carbs"),
            func.sum(models.Food.fats * models.DailyLog.quantity).label("fats"),
        )
        .select_from(models.DailyLog)
        .join(models.Food, models.DailyLog.food_id == models.Food.id)
        .filter(
            models.DailyLog.user_id == user_id,
            models.DailyLog.date == date
        )
        .first()
    )

    if totals and any(totals):
        return {
            "calories": float(totals[0] or 0),
            "protein": float(totals[1] or 0),
            "carbs": float(totals[2] or 0),
            "fats": float(totals[3] or 0),
        }
    
    return {"calories": 0, "protein": 0, "carbs": 0, "fats": 0}
