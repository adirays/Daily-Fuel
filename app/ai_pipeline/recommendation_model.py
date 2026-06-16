from app.schemas import UserProfile, Food

def predict_food_recommendation(user: UserProfile, food: Food) -> list:
    """
    Generates a list of ranked recommendations (top 3) based on nutritional heuristics.
    """
    recommendations = []
    # Heuristic 1: Prioritize low-calorie, high-protein foods
    if food.calories < 500 and food.protein > 10:
        recommendations.append({
            'food_id': food.id,
            'recommendation': 'recommend',
            'confidence': 0.85,
            'reason': 'Low calorie, high protein'
        })
    # Heuristic 2: Consider moderate-calorie, balanced macros
    elif 300 < food.calories < 600 and food.protein > 8 and food.fat < 20:
        recommendations.append({
            'food_id': food.id,
            'recommendation': 'recommend',
            'confidence': 0.75,
            'reason': 'Balanced macros'
        })
    # Heuristic 3: Flag high-sugar foods
    if food.sugar > 20:
        recommendations.append({
            'food_id': food.id,
            'recommendation': 'caution',
            'confidence': 0.9,
            'reason': 'High sugar content'
        })
    # Return top 3 recommendations
    return recommendations[:3]
