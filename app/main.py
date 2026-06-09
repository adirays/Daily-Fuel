import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging for Uvicorn access logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.access")
logger.setLevel(logging.INFO)

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import crud, schemas, utils
from .database import get_db, engine, Base
from .user_profiles import router as profiles_router
from app.ai.ai_routes import router as ai_router
from app.services.food_search import search_food_by_name
from typing import Optional
from app.schemas import DailyLogUpdate, UserGoalUpdate
# from app.routers import chat

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Nutrition API")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(profiles_router)
app.include_router(ai_router)
# app.include_router(chat.router)

# Food endpoints
@app.post("/foods/", response_model=schemas.Food)
def create_food(food: schemas.FoodCreate, db: Session = Depends(get_db)):
    return crud.create_food(db=db, food=food)

@app.get("/foods/", response_model=list[schemas.Food])
def read_foods(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_foods(db=db, skip=skip, limit=limit)

# Daily Logs
@app.post("/logs/", response_model=schemas.DailyLog)
def create_log(log: schemas.DailyLogCreate, db: Session = Depends(get_db)):
    print(f"DEBUG: Creating log - user_id: {log.user_id}, food_id: {log.food_id}, quantity: {log.quantity}, date: {log.date}")
    try:
        result = crud.create_daily_log(db=db, log=log)
        print(f"DEBUG: Log created successfully - id: {result.id}")
        return result
    except ValueError as e:
        print(f"DEBUG: ValueError in create_log: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"DEBUG: Unexpected error in create_log: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/logs/", response_model=list[schemas.DailyLog])
def read_logs(user_id: int, log_date: Optional[str] = None, db: Session = Depends(get_db)):
    if log_date:
        return crud.get_logs_by_date_and_user(db=db, user_id=user_id, date=log_date)
    return crud.get_logs_by_user(db=db, user_id=user_id)

@app.put("/logs/{log_id}", response_model=schemas.DailyLog)
def update_log(log_id: int, log_update: schemas.DailyLogUpdate, db: Session = Depends(get_db)):
    return crud.update_daily_log(db=db, log_id=log_id, log_update=log_update)

@app.delete("/logs/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)):
    return crud.delete_daily_log(db, log_id=log_id)

# Totals
@app.get("/totals/{user_id}/{log_date}", response_model=schemas.DailyTotals)
def get_daily_totals(user_id: int, log_date: str, db: Session = Depends(get_db)):
    # Get actual consumed totals for the specific date
    totals = crud.get_daily_totals_by_user(db, user_id, log_date)
    return schemas.DailyTotals(date=log_date, **totals)

@app.get("/search-food/{food_name}", response_model=dict)
def search_food(food_name: str):
    return search_food_by_name(food_name)

# Goals
@app.post("/goals/", response_model=schemas.UserGoal)
def set_goal(goal: schemas.UserGoalCreate, db: Session = Depends(get_db)):
    return crud.set_goal(db=db, goal=goal)

@app.get("/goals/", response_model=list[schemas.UserGoal])
def get_goals(db: Session = Depends(get_db)):
    return crud.get_goals(db=db)

@app.get("/goals/{user_id}", response_model=list[schemas.UserGoal])
def get_user_goals(user_id: int, db: Session = Depends(get_db)):
    return crud.get_user_goals(db=db, user_id=user_id)

@app.put("/goals/{goal_id}", response_model=schemas.UserGoal)
def update_goal(goal_id: int, goal: schemas.UserGoalUpdate, db: Session = Depends(get_db)):
    return crud.update_goal(db=db, goal_id=goal_id, goal=goal)

@app.get("/goals/all/", response_model=list[schemas.UserGoal])
def get_all_goals(db: Session = Depends(get_db)):
    return crud.get_goals(db=db)
