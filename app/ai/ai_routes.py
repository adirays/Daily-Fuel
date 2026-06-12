from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List, Dict, Any
from app.schemas import FactOut, ChatRequest, ClassifyRequest, NutritionResult
from app.ai.retriever import retrieve_facts
from app.ai_pipeline.nutrition_engine import classify_food
from app.ai_pipeline.llm_integration import get_llm_explanation, chat_with_llm
from app.ai_pipeline.enhanced_image_recognition import identify_food_from_image
from app.ai_pipeline.barcode_scanner import scan_barcode_from_image
from app.ai_pipeline.sugar_analysis import analyze_sugar_composition
from app.crud import get_user_profile, get_user_goals
from app.database import get_db
from sqlalchemy.orm import Session
from app.services.food_search import search_food_by_name
import logging
from app.ai_pipeline.enhanced_image_recognition import food_recognizer
import os

router = APIRouter(prefix="/ai", tags=["AI"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ACTIVITY_LEVEL_MAPPING = {
    "low": 1,
    "medium": 2,
    "high": 3,
}

@router.get("/get-nutrition-facts/", response_model=List[FactOut])
def get_nutrition_facts(q: str, k: int = 3):
    results = retrieve_facts(query=q, k=k)
    # results already have keys: score, fact, meta
    return results

@router.post("/classify/")
def classify_food_endpoint(request: ClassifyRequest, db: Session = Depends(get_db)):
    print(f"DEBUG: Starting classification for user {request.user_id}, food {request.food_name}")
    
    user_profile = get_user_profile(db, user_id=request.user_id)
    print(f"DEBUG: User profile retrieved: {user_profile is not None}")
    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")
    print(f"DEBUG: User profile data: age={user_profile.age}, weight={user_profile.weight_kg}")

    user_goals = get_user_goals(db, user_id=request.user_id)
    print(f"DEBUG: User goals count: {len(user_goals) if user_goals else 0}")
    
    if user_goals:
        first_goal = user_goals[0]
        print(f"DEBUG: First goal values: cal={first_goal.calories_goal}, prot={first_goal.protein_goal}")
        required_goal_attrs = ['calories_goal', 'protein_goal', 'carbs_goal', 'fats_goal']
        for attr in required_goal_attrs:
            if getattr(first_goal, attr) is None:
                print(f"DEBUG: Goal validation failed - {attr} is None")
                raise HTTPException(status_code=400, detail=f"Incomplete user goal data: '{attr}' is missing.")
        print(f"DEBUG: Goal validation passed")

    # Try external API first, fallback to our database
    food_data = search_food_by_name(request.food_name)
    print(f"DEBUG: External food search result: {bool(food_data)}")
    
    if not food_data or not food_data.get("products"):
        print(f"DEBUG: External search failed, trying built-in database")
        # Fallback to our built-in nutrition database
        food_key = request.food_name.lower().replace(' ', '_')
        if food_key in food_recognizer.nutrition_database:
            nutrition = food_recognizer.nutrition_database[food_key]
            print(f"DEBUG: Found {request.food_name} in built-in database")
            
            # Create mock product data from our database
            food_data = {
                "products": [{
                    "nutriments": {
                        "energy-kcal_100g": nutrition["calories"],
                        "proteins_100g": nutrition["protein"],
                        "fat_100g": nutrition["fat"],
                        "sugars_100g": nutrition["sugar"],
                        "carbohydrates_100g": nutrition["carbs"],
                        "fiber_100g": nutrition["fiber"]
                    }
                }]
            }
        else:
            raise HTTPException(status_code=404, detail="Food not found")
    
    print(f"DEBUG: Food found: {len(food_data.get('products', []))} products")

    product = food_data["products"][0]
    nutriments = product.get("nutriments", {})
    print(f"DEBUG: Food nutriments: {nutriments}")

    food_features = {
        "calories": nutriments.get("energy-kcal_100g", 0),
        "protein": nutriments.get("proteins_100g", 0),
        "fat": nutriments.get("fat_100g", 0),
        "sugar": nutriments.get("sugars_100g", 0),
        "carbohydrates": nutriments.get("carbohydrates_100g", 0),
    }

    user_features = {
        "age": user_profile.age,
        "bmi": user_profile.weight_kg / ((user_profile.height_cm / 100) ** 2),
        "activity_level": ACTIVITY_LEVEL_MAPPING.get(user_profile.activity_level.lower(), 1),
    }

    print(f"DEBUG: About to call classify_food()")
    classification = classify_food(food_features, user_features, user_goals)
    return classification

@router.post("/generate-explanation/")
def generate_explanation_endpoint(classification: Dict[str, Any], rag_output: str):
    explanation = get_llm_explanation(classification, rag_output)
    return {"explanation": explanation}

@router.post("/chat/")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """AI chat endpoint with Ollama integration."""
    
    try:
        logger.info(f"Chat request: user {request.user_id}, query '{request.query}'")
        
        # Import here to avoid circular imports
        from app.ai.llm_integration import chat_with_ai
        
        response = chat_with_ai(db, request.user_id, request.query)
        return {"response": response}
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Chat service temporarily unavailable")

@router.post("/identify-food/")
async def identify_food(file: UploadFile = File(...)):
    """Enhanced food identification with complete nutrition data"""
    try:
        print(f"🚀 API Route: Processing file: {file.filename}")
        
        from app.ai_pipeline.enhanced_image_recognition import IntegratedFoodRecognizer
        # Create fresh instance to avoid global instance issues
        fresh_recognizer = IntegratedFoodRecognizer()
        
        print(f"🔍 Fresh recognizer created")
        print(f"🔍 GOOGLE_VISION_AVAILABLE: {fresh_recognizer.__class__.__name__}")
        print(f"🔍 Vision client: {fresh_recognizer.vision_client is not None}")
        
        result = fresh_recognizer.identify_food_from_image(file)
        print(f"🎯 Final result: {result.get('recognition_method', 'unknown')}")
        return result
    except Exception as e:
        print(f"❌ API Route Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Recognition failed: {str(e)}")

@router.post("/scan-barcode/")
async def scan_barcode(file: UploadFile = File(...)):
    """Scan barcode from image and lookup nutritional information"""
    try:
        result = scan_barcode_from_image(file)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-sugar/")
def analyze_sugar(food_name: str, total_sugar: float, nutritional_data: Dict = None):
    """Analyze sugar composition (natural vs. added sugars)"""
    try:
        result = analyze_sugar_composition(food_name, total_sugar, nutritional_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/nutrition-analysis/")
def comprehensive_nutrition_analysis(request: ClassifyRequest, db: Session = Depends(get_db)):
    """Complete nutrition analysis including sugar differentiation"""
    try:
        # Get basic classification (existing logic)
        classification = classify_food_endpoint(request, db)
        
        # Add sugar analysis if sugar data is available
        if "nutritional_details" in classification and "sugar_g" in classification["nutritional_details"]:
            sugar_analysis = analyze_sugar_composition(
                request.food_name,
                classification["nutritional_details"]["sugar_g"],
                classification["nutritional_details"]
            )
            classification["sugar_analysis"] = sugar_analysis
            
            # Enhance reasoning with sugar insights
            if sugar_analysis["dominant_type"] == "added" and sugar_analysis["added_sugar_g"] > 10:
                classification["reasoning"] += f" High added sugar content ({sugar_analysis['added_sugar_g']}g/100g) is concerning."
            elif sugar_analysis["dominant_type"] == "natural":
                classification["reasoning"] += f" Sugars are primarily natural ({sugar_analysis['natural_sugar_g']}g/100g)."
        
        return classification
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/test-google-vision/")
def test_google_vision_status():
    """Test if Google Vision API is properly configured"""
    from app.ai_pipeline.enhanced_image_recognition import GOOGLE_VISION_AVAILABLE, food_recognizer
    
    return {
        "google_vision_available": GOOGLE_VISION_AVAILABLE,
        "vision_client_initialized": food_recognizer.vision_client is not None,
        "credentials_file_exists": os.path.exists("analog-reef-470415-q6-b8ddae1e11b3.json")
    }
