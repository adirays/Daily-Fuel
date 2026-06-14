"""
Integrated Food Recognition with Google Vision API
Uses Google Vision API for accurate food recognition
"""

from PIL import Image
import numpy as np
from typing import Dict, List
import colorsys
import math
import random
import io
import json
import os

# Initialize availability flags
GOOGLE_VISION_AVAILABLE = False

# Try to import Google Vision (optional dependency)
try:
    from google.cloud import vision
    from google.oauth2 import service_account
    GOOGLE_VISION_AVAILABLE = True
    print("✅ Google Cloud Vision imports successful")
except ImportError as e:
    print(f"❌ Google Cloud Vision import failed: {e}")
    print("🔄 Using fallback recognition system")
except Exception as e:
    print(f"❌ Unexpected error importing Google Vision: {e}")
    GOOGLE_VISION_AVAILABLE = False

class IntegratedFoodRecognizer:
    """
    Food recognition using Google Vision API with fallback to color recognition
    """
    
    def __init__(self):
        # Google Vision setup (only if available)
        self.vision_client = None
        print(f"🔍 GOOGLE_VISION_AVAILABLE = {GOOGLE_VISION_AVAILABLE}")
        
        if GOOGLE_VISION_AVAILABLE:
            try:
                # Check if credentials file exists
                credentials_path = "analog-reef-470415-q6-b8ddae1e11b3.json"
                print(f"🔍 Looking for credentials at: {credentials_path}")
                print(f"🔍 File exists: {os.path.exists(credentials_path)}")
                
                if os.path.exists(credentials_path):
                    print("✅ Credentials file found, initializing Google Vision...")
                    credentials = service_account.Credentials.from_service_account_file(credentials_path)
                    self.vision_client = vision.ImageAnnotatorClient(credentials=credentials)
                    print("✅ Google Vision API initialized successfully")
                else:
                    print("❌ Google Vision credentials not found, using fallback")
                        
            except Exception as e:
                print(f"❌ Failed to initialize Google Vision: {str(e)}")
                print("🔄 Using fallback recognition")
        else:
            print("❌ Google Vision not available (imports failed), using fallback")
        
        # Expanded nutrition database with more common foods
        self.nutrition_db = {
            "apple": {
                "calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2, "sugar": 10, "fiber": 2.4,
                "serving_size": "1 medium apple (150g)"
            },
            "banana": {
                "calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3, "sugar": 12, "fiber": 2.6,
                "serving_size": "1 medium banana (120g)"
            },
            "orange": {
                "calories": 49, "protein": 0.9, "carbs": 13, "fat": 0.1, "sugar": 9, "fiber": 2.8,
                "serving_size": "1 medium orange (130g)"
            },
            "chicken": {
                "calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "sugar": 0, "fiber": 0,
                "serving_size": "100g cooked breast"
            },
            "beef": {
                "calories": 250, "protein": 26, "carbs": 0, "fat": 17, "sugar": 0, "fiber": 0,
                "serving_size": "100g cooked steak"
            },
            "rice": {
                "calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "sugar": 0.1, "fiber": 0.4,
                "serving_size": "1 cup cooked (150g)"
            },
            "bread": {
                "calories": 265, "protein": 9.4, "carbs": 49, "fat": 3.2, "sugar": 5.7, "fiber": 2.7,
                "serving_size": "2 slices (60g)"
            },
            "pizza": {
                "calories": 266, "protein": 11, "carbs": 33, "fat": 10, "sugar": 3.6, "fiber": 2.3,
                "serving_size": "1 slice (100g)"
            },
            "pasta": {
                "calories": 157, "protein": 5.8, "carbs": 31, "fat": 0.9, "sugar": 0.6, "fiber": 1.8,
                "serving_size": "1 cup cooked (140g)"
            },
            "salad": {
                "calories": 25, "protein": 1.5, "carbs": 4.5, "fat": 0.2, "sugar": 2.5, "fiber": 2.1,
                "serving_size": "1 cup mixed greens (50g)"
            },
            "yogurt": {
                "calories": 61, "protein": 3.5, "carbs": 4.7, "fat": 3.3, "sugar": 4.7, "fiber": 0,
                "serving_size": "100g plain yogurt"
            },
            "eggs": {
                "calories": 155, "protein": 13, "carbs": 1.1, "fat": 11, "sugar": 0.6, "fiber": 0,
                "serving_size": "2 large eggs (100g)"
            },
            "fish": {
                "calories": 146, "protein": 25, "carbs": 0, "fat": 5.2, "sugar": 0, "fiber": 0,
                "serving_size": "100g salmon"
            },
            "potatoes": {
                "calories": 77, "protein": 2, "carbs": 17, "fat": 0.1, "sugar": 0.8, "fiber": 2.2,
                "serving_size": "1 medium potato (173g)"
            },
            "tomato": {
                "calories": 18, "protein": 0.9, "carbs": 3.9, "fat": 0.2, "sugar": 2.6, "fiber": 1.2,
                "serving_size": "1 medium tomato (123g)"
            },
            # Add common Indian/International foods
            "samosa": {
                "calories": 262, "protein": 3.5, "carbs": 27, "fat": 16, "sugar": 1.2, "fiber": 2.1,
                "serving_size": "1 medium samosa (40g)"
            },
            "burger": {
                "calories": 295, "protein": 12, "carbs": 30, "fat": 15, "sugar": 6, "fiber": 1.5,
                "serving_size": "1 medium burger (150g)"
            },
            "sandwich": {
                "calories": 250, "protein": 11, "carbs": 30, "fat": 8, "sugar": 4, "fiber": 2,
                "serving_size": "1 sandwich (100g)"
            },
            "noodles": {
                "calories": 138, "protein": 5.8, "carbs": 25, "fat": 2, "sugar": 0.5, "fiber": 1.2,
                "serving_size": "1 cup cooked (140g)"
            },
            "curry": {
                "calories": 112, "protein": 3.2, "carbs": 12, "fat": 6, "sugar": 2.5, "fiber": 2.8,
                "serving_size": "1 cup (200g)"
            },
            "soup": {
                "calories": 54, "protein": 2.1, "carbs": 8, "fat": 1.8, "sugar": 1.2, "fiber": 1.5,
                "serving_size": "1 cup (240g)"
            }
        }
        
        # Expanded food name mapping for better Google Vision matching
        self.food_mapping = {
            "Granny Smith": "apple",
            "golden delicious": "apple",
            "plantain": "banana",
            "chicken breast": "chicken",
            "fried chicken": "chicken",
            "hamburger": "beef",
            "ground beef": "beef",
            "brown rice": "rice",
            "white rice": "rice",
            "whole wheat bread": "bread",
            "white bread": "bread",
            "cheese pizza": "pizza",
            "pepperoni pizza": "pizza",
            "spaghetti": "pasta",
            "macaroni": "pasta",
            "lettuce": "salad",
            "mixed greens": "salad",
            "greek yogurt": "yogurt",
            "plain yogurt": "yogurt",
            "scrambled eggs": "eggs",
            "boiled eggs": "eggs",
            "salmon": "fish",
            "tuna": "fish",
            "sweet potato": "potatoes",
            "russet potato": "potatoes",
            "cherry tomato": "tomato",
            "roma tomato": "tomato",
            # Add Indian/International food mappings
            "samosa": "samosa",
            "cheeseburger": "burger",
            "hamburger": "burger",
            "veggie burger": "burger",
            "club sandwich": "sandwich",
            "grilled cheese": "sandwich",
            "chicken sandwich": "sandwich",
            "ramen": "noodles",
            "udon": "noodles",
            "chicken curry": "curry",
            "vegetable curry": "curry",
            "tomato soup": "soup",
            "chicken soup": "soup",
            "vegetable soup": "soup"
        }
    
    def identify_food_from_image(self, image_file) -> Dict:
        """
        Identify food using Google Vision API or fallback to color recognition
        Always returns nutrition data for auto-fill
        """
        
        print(f"🔍 Starting food identification for image: {getattr(image_file, 'filename', 'unknown')}")
        print(f"🔍 GOOGLE_VISION_AVAILABLE = {GOOGLE_VISION_AVAILABLE}")
        print(f"🔍 self.vision_client is not None = {self.vision_client is not None}")
        
        # Try Google Vision API first (if available)
        if GOOGLE_VISION_AVAILABLE and self.vision_client:
            print("✅ Google Vision conditions met, attempting to use it...")
            try:
                result = self._identify_with_google_vision(image_file)
                print(f"🔍 Google Vision result: {result}")
                if result["success"]:
                    print(f"✅ Google Vision SUCCESS: {result['food_identified']} (confidence: {result['confidence']})")
                    return result
                else:
                    print(f"❌ Google Vision returned no result: {result.get('error', 'unknown error')}")
            except Exception as e:
                print(f"❌ Google Vision FAILED with exception: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ Google Vision conditions NOT met: GOOGLE_VISION_AVAILABLE={GOOGLE_VISION_AVAILABLE}, vision_client_exists={self.vision_client is not None}")
        
        # Fallback to color-based recognition
        print("🔄 Using color-based fallback recognition")
        return self._identify_with_color_recognition(image_file)
    
    def _identify_with_google_vision(self, image_file) -> Dict:
        """Identify food using Google Vision API"""
        
        try:
            # ✅ CORRECTED: Read raw bytes directly from UploadFile
            # This avoids PIL conversion which can corrupt images
            content = image_file.file.read()  # Synchronous read
            
            if not content:
                return {"success": False, "error": "Empty image file"}
            
            # Create Vision API image directly from uploaded bytes
            vision_image = vision.Image(content=content)
            
            # Get labels (food identification)
            label_response = self.vision_client.label_detection(image=vision_image)
            labels = label_response.label_annotations
            
            if hasattr(label_response, 'error') and label_response.error.message:
                raise Exception(f"Vision API Error: {label_response.error.message}")
            
            # Extract food labels
            food_labels = [label.description.lower() for label in labels[:10]]  # Top 10 labels
            print(f"🔍 Google Vision labels: {food_labels[:5]}")  # Debug: show top 5 labels
            
            # Find best food match
            best_match = self._find_food_from_labels(food_labels)
            
            if best_match:
                return self._create_success_response(best_match["food"], best_match["confidence"], "Google Vision API")
            else:
                return {"success": False, "error": "No recognizable food found in image"}
                
        except Exception as e:
            print(f"❌ Google Vision API error: {e}")
            return {"success": False, "error": str(e)}
    
    def _identify_with_color_recognition(self, image_file) -> Dict:
        """Improved fallback color-based food recognition"""
        
        try:
            # Analyze image colors
            image = Image.open(image_file.file)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            dominant_colors = self._get_dominant_colors(image)
            
            # Try to match food patterns
            matched_food = self._find_food_from_colors(dominant_colors)
            
            if matched_food:
                return self._create_success_response(matched_food["food"], matched_food["confidence"], "Color recognition")
            else:
                # Always provide a food result - never fail
                # Pick a reasonable default based on image analysis
                default_food = self._get_best_default_food(dominant_colors)
                return self._create_success_response(default_food, 0.3, "Smart fallback")
                
        except Exception as e:
            print(f"❌ Color recognition error: {e}")
            # Ultimate fallback
            return self._create_success_response("chicken", 0.3, "Default fallback")
    
    def _find_food_from_labels(self, labels: List[str]) -> Dict:
        """Find food match from Vision API labels with better matching"""
        
        print(f"🔍 Searching for food in labels: {labels}")
        
        # Look for direct matches in nutrition database
        for label in labels:
            label_lower = label.lower()
            print(f"🔍 Checking label: '{label_lower}'")
            
            # Direct match
            if label_lower in self.nutrition_db:
                print(f"✅ Direct match found: {label_lower}")
                return {"food": label_lower, "confidence": 0.9}
            
            # Mapped match
            if label_lower in self.food_mapping:
                mapped_food = self.food_mapping[label_lower]
                print(f"🔍 Mapped '{label_lower}' to '{mapped_food}'")
                if mapped_food in self.nutrition_db:
                    print(f"✅ Mapped match found: {mapped_food}")
                    return {"food": mapped_food, "confidence": 0.8}
            
            # Partial match with better scoring
            for db_food in self.nutrition_db.keys():
                # Exact substring match
                if db_food in label_lower or label_lower in db_food:
                    confidence = 0.7 if len(db_food) > 3 else 0.5  # Shorter words get lower confidence
                    print(f"✅ Partial match found: '{label_lower}' contains '{db_food}'")
                    return {"food": db_food, "confidence": confidence}
                
                # Word-by-word matching for compound foods
                label_words = label_lower.split()
                for word in label_words:
                    if word in db_food and len(word) > 3:  # Only meaningful words
                        print(f"✅ Word match found: '{word}' in '{db_food}'")
                        return {"food": db_food, "confidence": 0.6}
        
        print("❌ No food matches found in any labels")
        return None
    
    def _find_food_from_colors(self, dominant_colors: list) -> Dict:
        """Find food match from color patterns"""
        
        color_patterns = {
            "red_fruit": {
                "colors": [(200, 20, 20), (255, 80, 80)],
                "foods": ["apple"],
                "confidence": 0.8
            },
            "yellow_fruit": {
                "colors": [(220, 200, 50), (255, 255, 100)],
                "foods": ["banana"],
                "confidence": 0.85
            },
            "orange_fruit": {
                "colors": [(255, 140, 0), (255, 165, 0)],
                "foods": ["orange"],
                "confidence": 0.8
            },
            "brown_meat": {
                "colors": [(150, 100, 80), (180, 130, 100)],
                "foods": ["chicken", "beef"],
                "confidence": 0.6
            },
            "white_grain": {
                "colors": [(240, 230, 200), (220, 210, 180)],
                "foods": ["rice"],
                "confidence": 0.65
            },
            "golden_bread": {
                "colors": [(200, 150, 100), (180, 130, 80)],
                "foods": ["bread"],
                "confidence": 0.7
            },
            "green_vegetable": {
                "colors": [(50, 150, 50), (80, 180, 80)],
                "foods": ["salad"],
                "confidence": 0.75
            },
            "red_vegetable": {
                "colors": [(200, 50, 50), (220, 80, 80)],
                "foods": ["tomato"],
                "confidence": 0.8
            }
        }
        
        best_match = None
        best_score = 0
        
        for pattern_name, pattern in color_patterns.items():
            score = 0
            
            # Color similarity scoring
            for img_color in dominant_colors:
                for pattern_color in pattern["colors"]:
                    distance = math.sqrt(
                        (img_color[0] - pattern_color[0])**2 +
                        (img_color[1] - pattern_color[1])**2 +
                        (img_color[2] - pattern_color[2])**2
                    )
                    
                    if distance < 60:  # Similarity threshold
                        score += pattern["confidence"]
                        break
            
            if score > best_score and score > 0.4:
                best_score = score
                food_name = random.choice(pattern["foods"])
                best_match = {
                    "food": food_name,
                    "confidence": min(score, 1.0)
                }
        
        return best_match
    
    def _get_dominant_colors(self, image: Image.Image, num_colors: int = 3) -> list:
        """Extract dominant colors from image"""
        # Resize for faster processing
        image = image.resize((100, 100))
        pixels = list(image.getdata())
        
        # Count color frequencies
        color_counts = {}
        for pixel in pixels:
            # Round to nearest 20 for grouping
            rounded = tuple((c // 20) * 20 for c in pixel[:3])
            color_counts[rounded] = color_counts.get(rounded, 0) + 1
        
        # Return most common colors
        sorted_colors = sorted(color_counts.items(), key=lambda x: x[1], reverse=True)
        return [color for color, count in sorted_colors[:num_colors]]
    
    def _get_best_default_food(self, dominant_colors: list) -> str:
        """Get the best default food based on color analysis"""
        if not dominant_colors:
            return "chicken"
            
        # Analyze the dominant color to suggest appropriate food
        r, g, b = dominant_colors[0]  # Most dominant color
        
        # Greenish foods
        if g > r and g > b and g > 100:
            return "salad"
        # Reddish foods  
        elif r > g and r > b and r > 100:
            return "tomato"
        # Yellowish foods
        elif r > 100 and g > 100 and abs(r - g) < 50:
            return "banana"
        # Brownish foods (meats)
        elif r > 80 and g > 60 and b < 80:
            return "chicken"
        # Default
        else:
            return "rice"
    
    def _create_success_response(self, food_name: str, confidence: float, method: str) -> Dict:
        """Create successful response with nutrition data"""
        
        nutrition = self.nutrition_db[food_name]
        
        return {
            "success": True,
            "food_identified": food_name.title(),
            "confidence": round(confidence, 2),
            "confidence_level": "High" if confidence > 0.7 else "Medium",
            "recognition_method": method,
            
            "nutrition_per_100g": {
                "calories": nutrition["calories"],
                "protein_g": nutrition["protein"],
                "carbs_g": nutrition["carbs"],
                "fat_g": nutrition["fat"],
                "sugar_g": nutrition["sugar"],
                "fiber_g": nutrition["fiber"]
            },
            
            "serving_size": nutrition["serving_size"],
            
            "ready_to_log": {
                "food_name": food_name.title(),
                "calories": nutrition["calories"],
                "protein": nutrition["protein"],
                "carbs": nutrition["carbs"],
                "fats": nutrition["fat"],
                "quantity": 100
            }
        }

# Global instance
food_recognizer = IntegratedFoodRecognizer()

def identify_food_from_image(image_file):
    """Integrated food identification with Google Vision + fallback"""
    return food_recognizer.identify_food_from_image(image_file)
