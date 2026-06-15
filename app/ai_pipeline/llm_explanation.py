from app.schemas import UserProfile, Food

def generate_explanation(
    user: UserProfile,
    food: Food,
    recommendation: str,
    nutrition_facts: str,
    query: str
) -> str:
    """
    This function generates a personalized, conversational explanation for the food recommendation.
    """
    if recommendation == "recommend":
        response = f"Yes, based on your goal of {user.fitness_goal}, {food.name} seems like a good choice. "
        response += f"Here's why: it has {food.calories} calories and {food.protein}g of protein per serving. "
        response += f"This aligns well with your goals. Just be mindful of your portion sizes!"
    else:
        response = f"Given your goal of {user.fitness_goal}, you might want to reconsider {food.name}. "
        response += f"It has {food.calories} calories and {food.protein}g of protein per serving. "
        response += f"There might be better options to help you achieve your goals."

    response += f"\n\nHere are some more nutrition facts: {nutrition_facts}"
    return response