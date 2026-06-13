import requests
import json
from sqlalchemy.orm import Session
from app.crud import get_user_profile, get_user_goals, get_logs_by_user
from datetime import date, datetime, timedelta

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3:mini"

def build_user_context(db: Session, user_id: int) -> str:
    """Build comprehensive user context including detailed food logs."""
    
    context_parts = []
    
    # User profile
    user_profile = get_user_profile(db, user_id)
    if user_profile:
        context_parts.append(f"""USER PROFILE:
- Name: {user_profile.name or 'Not specified'}
- Age: {user_profile.age or 'Not specified'}
- Gender: {user_profile.gender or 'Not specified'}
- Weight: {user_profile.weight_kg or 'Not specified'} kg
- Height: {user_profile.height_cm or 'Not specified'} cm
- Activity Level: {user_profile.activity_level or 'Not specified'}
- Main Goal: {user_profile.goal or 'Not specified'}
- Fitness Goal: {user_profile.fitness_goal or 'Not specified'}
- Allergies: {user_profile.allergies or 'None'}
- Health Conditions: {user_profile.health_conditions or 'None'}""")
    
    # Current goals
    user_goals = get_user_goals(db, user_id)
    if user_goals:
        goal = user_goals[0]
        context_parts.append(f"""CURRENT NUTRITION GOALS:
- Daily Calories: {goal.calories_goal or 'Not set'} kcal
- Daily Protein: {goal.protein_goal or 'Not set'}g
- Daily Carbs: {goal.carbs_goal or 'Not set'}g
- Daily Fats: {goal.fats_goal or 'Not set'}g""")
    
    # Recent food logs (last 7 days, more detailed)
    seven_days_ago = datetime.now().date() - timedelta(days=7)
    recent_logs = get_logs_by_user(db, user_id, limit=20)  # Get more logs
    if recent_logs:
        context_parts.append("RECENT FOOD LOGS (Last 7 days):")
        recent_entries = []
        for log in recent_logs:
            if log.food and log.date >= seven_days_ago:
                food_name = log.food.name
                quantity = log.quantity
                calories = log.food.calories * quantity if log.food.calories else 0
                protein = log.food.protein * quantity if log.food.protein else 0
                carbs = log.food.carbs * quantity if log.food.carbs else 0
                fats = log.food.fats * quantity if log.food.fats else 0
                
                entry = f"- {log.date}: {quantity}x {food_name} ({calories:.0f} kcal, {protein:.1f}g protein, {carbs:.1f}g carbs, {fats:.1f}g fats)"
                recent_entries.append(entry)
        
        if recent_entries:
            context_parts.append("\n".join(recent_entries[:10]))  # Show last 10 entries
        else:
            context_parts.append("- No recent logs in the last 7 days")
    
    return "\n\n".join(context_parts)

def query_ollama(prompt: str) -> str:
    """Query Ollama with settings optimized for longer, comprehensive responses."""
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,     # Balanced creativity
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": 300,     # Much longer responses (was 50)
            "num_ctx": 2048,        # Larger context window (was 512)
            "repeat_penalty": 1.1,
            "repeat_last_n": 64
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=20)  # Longer timeout
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "").strip()
        
    except requests.exceptions.ConnectionError:
        return "AI assistant is currently unavailable. Please try again later."
    except requests.exceptions.Timeout:
        return "The response is taking longer than expected. Could you try rephrasing your question?"
    except Exception as e:
        print(f"Ollama error: {e}")
        return "I'm having trouble processing your request right now. Please try again."

def is_greeting_only(text: str) -> bool:
    """Check if input is just a greeting with no real question."""
    greetings = {
        "hi", "hello", "hey", "sup", "yo", "hiya", "greetings", "good morning", 
        "good afternoon", "good evening", "howdy", "aloha", "bonjour", "hola",
        "hi there", "hey there", "hello there", "what's up", "whats up", "wassup"
    }
    
    text_clean = text.lower().strip()
    
    # Exact greeting matches
    if text_clean in greetings:
        return True
    
    # Very short phrases that are just greetings
    if len(text_clean.split()) <= 2 and any(greet in text_clean for greet in ["hi", "hey", "hello", "sup"]):
        return True
    
    return False

def chat_with_ai(db: Session, user_id: int, user_input: str) -> str:
    """Enhanced chat function with comprehensive responses and detailed context."""
    
    # Clean input
    user_input_clean = user_input.lower().strip()
    
    # Only give short responses for pure greetings
    if is_greeting_only(user_input):
        user_profile = get_user_profile(db, user_id)
        user_name = user_profile.name if user_profile else "there"
        return f"Hello {user_name}! I'm your nutrition assistant. I can help you with meal planning, understanding your nutrition goals, tracking your progress, and answering any questions about healthy eating. What would you like to know?"
    
    # Check for very basic single words that aren't questions
    basic_words = {"ok", "okay", "yes", "no", "sure", "maybe", "thanks", "thank you", "bye", "goodbye"}
    if user_input_clean in basic_words or (len(user_input_clean.split()) == 1 and user_input_clean in basic_words):
        if "thanks" in user_input_clean or "thank" in user_input_clean:
            return "You're welcome! I'm here whenever you need nutrition advice or help with your goals."
        elif "bye" in user_input_clean or "goodbye" in user_input_clean:
            return "Goodbye! Remember to stay hydrated, eat balanced meals, and track your nutrition. Take care!"
        else:
            return "Great! How else can I help you with your nutrition today?"
    
    try:
        # Get comprehensive user context
        user_context = build_user_context(db, user_id)
        
        # Get user name for personalization
        user_profile = get_user_profile(db, user_id)
        user_name = user_profile.name if user_profile else "there"
        
        # Create comprehensive prompt that encourages detailed responses
        prompt = f"""You are a knowledgeable nutrition assistant helping {user_name} with their health and wellness goals.

{user_context}

User's Question: {user_input}

Please provide a comprehensive, helpful response that:
- References their personal profile, goals, and recent eating habits when relevant
- Gives specific, actionable nutrition advice
- Explains concepts clearly with examples
- Considers their individual needs and preferences
- Suggests concrete next steps or follow-up questions

Be thorough but conversational. Include relevant nutritional information, portion suggestions, or meal ideas based on their recent logs and goals.

Response:"""

        # Get comprehensive Ollama response
        response = query_ollama(prompt)
        
        # Validate and clean response
        if response and len(response.strip()) >= 10:  # Minimum length for meaningful responses
            # Don't truncate - allow full responses
            return response
        
        # Fallback for failed responses
        return f"I understand you're asking about nutrition. Based on your goals and recent eating patterns, I'd recommend focusing on balanced meals with adequate protein. Could you tell me more specifically what aspect of nutrition you'd like help with?"
        
    except Exception as e:
        print(f"Chat error: {e}")
        return "I'm having some technical difficulties right now, but I'd still love to help with your nutrition questions. Could you try rephrasing your question?"
