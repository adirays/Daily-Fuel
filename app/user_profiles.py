from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import crud, schemas
from .database import get_db

router = APIRouter(prefix="/profiles", tags=["User Profiles"])

# ---------- Create a user profile ----------
@router.post("/", response_model=schemas.UserProfile)
def create_profile(profile: schemas.UserProfileCreate, db: Session = Depends(get_db)):
    return crud.create_user_profile(db=db, profile=profile)

# ---------- Get all user profiles ----------
@router.get("/", response_model=List[schemas.UserProfile])
def get_profiles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_user_profiles(db=db, skip=skip, limit=limit)

# ---------- Get single user profile by ID ----------
@router.get("/{user_id}", response_model=schemas.UserProfile)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    profile = crud.get_user_profile(db=db, user_id=user_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"User profile {user_id} not found")
    return profile

# ---------- Update user profile by ID ----------
@router.put("/{user_id}", response_model=schemas.UserProfile)
def update_profile(user_id: int, profile: schemas.UserProfileCreate, db: Session = Depends(get_db)):
    return crud.update_user_profile(db=db, user_id=user_id, profile=profile)
