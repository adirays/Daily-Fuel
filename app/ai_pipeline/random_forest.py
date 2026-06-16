
from typing import List, Any

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import os

def train_model():
    # Updated training data with realistic nutrition values
    data = {
        'calories': [52, 250, 150, 400, 300, 180, 95, 350, 220, 450],  # Apple, burger, etc.
        'protein': [0.3, 20, 8, 25, 15, 12, 5, 18, 10, 30],
        'fat': [0.2, 15, 5, 20, 12, 8, 3, 14, 7, 25],
        'sugar': [10, 5, 8, 15, 20, 12, 6, 18, 9, 25],
        'carbohydrates': [14, 25, 18, 35, 40, 22, 12, 30, 16, 50],
        'age': [25, 35, 45, 30, 40, 28, 55, 32, 38, 42],
        'bmi': [22, 25, 28, 24, 26, 23, 27, 24, 25, 29],
        'activity_level': [2, 1, 3, 2, 1, 2, 1, 3, 2, 1],
        'target_calories': [2000, 2200, 1800, 2500, 1900, 2100, 1700, 2300, 2000, 2400],
        'target_protein': [100, 120, 80, 130, 90, 110, 75, 125, 100, 140],
        'target_carbs': [250, 280, 200, 300, 220, 260, 180, 290, 250, 310],
        'target_fats': [70, 80, 60, 85, 65, 75, 55, 80, 70, 90],
        'recommended': [1, 0, 1, 0, 0, 1, 1, 0, 1, 0]  # More balanced labels
    }
    df = pd.DataFrame(data)

    X = df.drop('recommended', axis=1)
    y = df['recommended']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Ensure the directory exists
    os.makedirs(os.path.dirname('models/rf_model.joblib'), exist_ok=True)
    
    joblib.dump(model, 'models/rf_model.joblib')
    joblib.dump(scaler, 'models/scaler.joblib')

def classify_food(food_features, user_features, user_goals: List[Any]):
    model = joblib.load('models/rf_model.joblib')
    scaler = joblib.load('models/scaler.joblib')

    # Define default nutritional targets
    DEFAULT_TARGETS = {
        "target_calories": 2000.0,
        "target_protein": 100.0,
        "target_carbs": 250.0,
        "target_fats": 70.0,
    }

    # Initialize goal_features with default targets
    goal_features = DEFAULT_TARGETS.copy()

    # If user goals are provided (and validated by the endpoint), override defaults
    if user_goals:
        first_goal = user_goals[0] # Assuming the first goal is the active one
        print(f"DEBUG: first_goal = {first_goal}")  # Add debug
        print(f"DEBUG: goal attrs = {dir(first_goal)}")  # Add debug
        
        goal_features.update({
            "target_calories": float(first_goal.calories_goal or 2000.0),
            "target_protein": float(first_goal.protein_goal or 100.0),
            "target_carbs": float(first_goal.carbs_goal or 250.0),
            "target_fats": float(first_goal.fats_goal or 70.0),
        })
        
        print(f"DEBUG: goal_features after update = {goal_features}")  # Add debug

    features = {**food_features, **user_features, **goal_features}
    print(f"DEBUG: food_features = {food_features}")
    print(f"DEBUG: user_features = {user_features}")  
    print(f"DEBUG: goal_features = {goal_features}")
    print(f"DEBUG: final features dict = {features}")

    df = pd.DataFrame([features])
    print(f"DEBUG: DataFrame columns = {df.columns.tolist()}")
    print(f"DEBUG: DataFrame shape = {df.shape}")

    # Ensure the order of columns is the same as during training
    # This list must match the features used in train_model exactly
    expected_columns = [
        'calories', 'protein', 'fat', 'sugar', 'carbohydrates',
        'age', 'bmi', 'activity_level',
        'target_calories', 'target_protein', 'target_carbs', 'target_fats'
    ]
    df = df[expected_columns]

    scaled_features = scaler.transform(df)
    
    prediction = model.predict(scaled_features)
    probability = model.predict_proba(scaled_features)

    # Calculate nutritional reasoning for LLM explanation
    calories = food_features.get('calories', 0)
    protein = food_features.get('protein', 0)
    fat = food_features.get('fat', 0)
    sugar = food_features.get('sugar', 0)
    carbs = food_features.get('carbohydrates', 0)
    
    # Build reasoning string
    reasoning_parts = []
    
    if protein > 15:
        reasoning_parts.append("high in protein")
    elif protein < 5:
        reasoning_parts.append("low in protein")
    
    if sugar > 10:
        reasoning_parts.append("high in sugar")
    elif sugar < 2:
        reasoning_parts.append("low in sugar")
    
    if fat > 20:
        reasoning_parts.append("high in fat")
    elif fat < 3:
        reasoning_parts.append("low in fat")
    
    if calories > 400:
        reasoning_parts.append("high in calories")
    elif calories < 50:
        reasoning_parts.append("low in calories")
    
    # Age considerations
    age = user_features.get('age', 30)
    if age > 50 and fat > 15:
        reasoning_parts.append("higher fat content may be concerning for older adults")
    elif age < 25 and protein < 8:
        reasoning_parts.append("younger adults may benefit from more protein")
    
    # Activity considerations  
    activity_level = user_features.get('activity_level', 2)
    if activity_level >= 3 and calories < 200:
        reasoning_parts.append("may not provide enough energy for active lifestyle")
    
    reasoning = ", ".join(reasoning_parts) if reasoning_parts else "balanced nutritional profile"

    return {
        "recommended": bool(prediction[0]),
        "confidence": float(max(probability[0])),
        "reasoning": reasoning,
        "nutritional_details": {
            "calories_per_100g": calories,
            "protein_g": protein,
            "fat_g": fat,
            "sugar_g": sugar,
            "carbs_g": carbs
        }
    }

if __name__ == '__main__':
    train_model()
