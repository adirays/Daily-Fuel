"""
Advanced Sugar Analysis Engine
Differentiates between natural and added sugars using food science and heuristics
"""

import re
from typing import Dict, Tuple, List
from enum import Enum

class SugarType(Enum):
    NATURAL = "natural"
    ADDED = "added"
    MIXED = "mixed"
    UNKNOWN = "unknown"

class SugarAnalyzer:
    """
    Analyzes sugar content to differentiate natural vs. added sugars
    """
    
    # Food categories and their typical natural sugar ratios
    NATURAL_SUGAR_FOODS = {
        # Fruits (very high natural sugar content)
        "fruits": {
            "categories": ["fruit", "berries", "citrus", "apple", "banana", "grape", "orange", "pear"],
            "natural_ratio": 0.95,  # 95% of sugar is natural
            "confidence": 0.9
        },
        
        # Vegetables (generally low sugar, mostly natural)
        "vegetables": {
            "categories": ["vegetable", "carrot", "beet", "corn", "pea", "sweet potato"],
            "natural_ratio": 0.85,
            "confidence": 0.8
        },
        
        # Dairy (lactose is natural milk sugar)
        "dairy": {
            "categories": ["milk", "yogurt", "cheese", "cream", "butter"],
            "natural_ratio": 0.9,
            "confidence": 0.85
        },
        
        # Whole grains (minimal natural sugars)
        "whole_grains": {
            "categories": ["whole wheat", "brown rice", "oats", "quinoa", "barley"],
            "natural_ratio": 0.1,
            "confidence": 0.7
        },
        
        # Nuts and seeds (very low natural sugars)
        "nuts_seeds": {
            "categories": ["nuts", "almond", "walnut", "seed", "chia", "flax"],
            "natural_ratio": 0.05,
            "confidence": 0.9
        },
        
        # Meat and fish (essentially no sugar)
        "protein_foods": {
            "categories": ["chicken", "beef", "fish", "meat", "egg", "tofu"],
            "natural_ratio": 0.0,
            "confidence": 0.95
        }
    }
    
    # Common added sugar indicators in food names
    ADDED_SUGAR_INDICATORS = [
        "sugar", "syrup", "honey", "sweet", "candy", "chocolate", "cake", "cookie",
        "pie", "pastry", "soda", "juice", "drink", "beverage", "sweetened",
        "sucrose", "fructose", "glucose", "maltose", "lactose", "dextrose",
        "brown sugar", "white sugar", "cane sugar", "corn syrup", "high fructose"
    ]
    
    # Foods where sugar is typically mostly added
    PROCESSED_FOOD_CATEGORIES = [
        "cereal", "breakfast cereal", "snack", "chips", "cracker", "pretzel",
        "candy", "chocolate", "ice cream", "frozen dessert", "soda", "soft drink",
        "juice drink", "energy drink", "sports drink", "sweetened beverage"
    ]
    
    def analyze_sugar_composition(self, food_name: str, total_sugar: float, 
                                nutritional_data: Dict = None) -> Dict:
        """
        Analyze sugar composition to estimate natural vs. added sugars
        
        Args:
            food_name: Name of the food
            total_sugar: Total sugar content per 100g
            nutritional_data: Additional nutritional information
            
        Returns:
            Dict with sugar analysis
        """
        
        food_name_lower = food_name.lower().strip()
        
        # Step 1: Determine food category and base natural sugar ratio
        category_info = self._categorize_food(food_name_lower)
        base_ratio = category_info["natural_ratio"]
        confidence = category_info["confidence"]
        
        # Step 2: Adjust ratio based on food name indicators
        name_adjustment = self._analyze_food_name_indicators(food_name_lower)
        adjusted_ratio = min(1.0, max(0.0, base_ratio + name_adjustment))
        
        # Step 3: Consider nutritional context
        if nutritional_data:
            context_adjustment = self._analyze_nutritional_context(nutritional_data, food_name_lower)
            adjusted_ratio = min(1.0, max(0.0, adjusted_ratio + context_adjustment))
            confidence = min(1.0, confidence + 0.1)  # Higher confidence with more data
        
        # Step 4: Calculate sugar amounts
        natural_sugar = total_sugar * adjusted_ratio
        added_sugar = total_sugar * (1 - adjusted_ratio)
        
        # Step 5: Determine dominant sugar type
        if adjusted_ratio >= 0.8:
            sugar_type = SugarType.NATURAL
        elif adjusted_ratio <= 0.2:
            sugar_type = SugarType.ADDED
        else:
            sugar_type = SugarType.MIXED
        
        # Step 6: Health impact assessment
        health_impact = self._assess_sugar_health_impact(
            natural_sugar, added_sugar, total_sugar, sugar_type
        )
        
        return {
            "total_sugar_g": total_sugar,
            "natural_sugar_g": round(natural_sugar, 2),
            "added_sugar_g": round(added_sugar, 2),
            "natural_ratio": round(adjusted_ratio, 3),
            "added_ratio": round(1 - adjusted_ratio, 3),
            "dominant_type": sugar_type.value,
            "confidence": round(confidence, 2),
            "health_impact": health_impact,
            "recommendation": self._generate_sugar_recommendation(
                added_sugar, sugar_type, food_name
            )
        }
    
    def _categorize_food(self, food_name: str) -> Dict:
        """Categorize food and determine natural sugar baseline"""
        
        for category, info in self.NATURAL_SUGAR_FOODS.items():
            if any(keyword in food_name for keyword in info["categories"]):
                return {
                    "category": category,
                    "natural_ratio": info["natural_ratio"],
                    "confidence": info["confidence"]
                }
        
        # Default: assume moderate processing (mixed sugars)
        return {
            "category": "processed",
            "natural_ratio": 0.4,
            "confidence": 0.5
        }
    
    def _analyze_food_name_indicators(self, food_name: str) -> float:
        """Analyze food name for sugar-related indicators"""
        adjustment = 0.0
        
        # Check for added sugar indicators
        added_indicators = sum(1 for indicator in self.ADDED_SUGAR_INDICATORS 
                             if indicator in food_name)
        if added_indicators > 0:
            adjustment -= min(0.3, added_indicators * 0.1)  # Reduce natural ratio
        
        # Check for whole/natural food indicators
        natural_indicators = ["whole", "organic", "natural", "fresh", "raw", "pure"]
        natural_matches = sum(1 for indicator in natural_indicators 
                            if indicator in food_name)
        if natural_matches > 0:
            adjustment += min(0.2, natural_matches * 0.1)  # Increase natural ratio
        
        # Check for processing indicators
        if any(cat in food_name for cat in self.PROCESSED_FOOD_CATEGORIES):
            adjustment -= 0.15  # Likely more added sugars
        
        return adjustment
    
    def _analyze_nutritional_context(self, nutritional_data: Dict, food_name: str) -> float:
        """Use nutritional data to refine sugar analysis"""
        adjustment = 0.0
        
        # High fiber + high sugar often indicates natural sugars (fruits)
        fiber = nutritional_data.get("fiber", 0)
        if fiber > 2 and nutritional_data.get("sugars", 0) > 5:
            adjustment += 0.15
        
        # High protein + high sugar might indicate added sugars (protein bars)
        protein = nutritional_data.get("protein", 0)
        if protein > 10 and nutritional_data.get("sugars", 0) > 15:
            adjustment -= 0.1
        
        # Very low calorie + high sugar likely natural (some fruits)
        calories = nutritional_data.get("calories", 0)
        if calories < 50 and nutritional_data.get("sugars", 0) > 8:
            adjustment += 0.1
        
        return adjustment
    
    def _assess_sugar_health_impact(self, natural_sugar: float, added_sugar: float, 
                                  total_sugar: float, sugar_type: SugarType) -> Dict:
        """Assess health impact of sugar composition"""
        
        # WHO guidelines: <10% of calories from free sugars
        # Approximate: <50g added sugar per day for 2000 calorie diet
        daily_limit = 50  # grams of added sugar
        
        # Calculate concern level
        if added_sugar > 15:  # High added sugar per 100g
            concern_level = "high"
            risk_factors = ["weight gain", "blood sugar spikes", "dental health"]
        elif added_sugar > 5:
            concern_level = "moderate"
            risk_factors = ["moderate blood sugar impact"]
        else:
            concern_level = "low"
            risk_factors = []
        
        # Benefits of natural sugars
        benefits = []
        if natural_sugar > 5 and sugar_type == SugarType.NATURAL:
            benefits.extend(["nutrient dense", "fiber content", "natural antioxidants"])
        
        return {
            "concern_level": concern_level,
            "risk_factors": risk_factors,
            "benefits": benefits,
            "daily_limit_exceeded": added_sugar > (daily_limit / 3)  # Per serving assumption
        }
    
    def _generate_sugar_recommendation(self, added_sugar: float, sugar_type: SugarType, 
                                     food_name: str) -> str:
        """Generate personalized sugar recommendation"""
        
        if sugar_type == SugarType.NATURAL:
            return f"Natural sugars from {food_name} are generally healthy when consumed in moderation."
        elif sugar_type == SugarType.ADDED:
            if added_sugar > 10:
                return f"High added sugar content in {food_name} - consider limiting consumption."
            else:
                return f"Moderate added sugars in {food_name} - enjoy occasionally."
        else:  # MIXED
            return f"Mixed natural and added sugars in {food_name} - check ingredients for added sugars."

# Global instance
sugar_analyzer = SugarAnalyzer()

def analyze_sugar_composition(food_name: str, total_sugar: float, 
                           nutritional_data: Dict = None) -> Dict:
    """Convenience function for sugar analysis"""
    return sugar_analyzer.analyze_sugar_composition(food_name, total_sugar, nutritional_data)
