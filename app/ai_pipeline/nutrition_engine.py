"""
Scientific Rule-Based Nutrition Recommendation Engine
Replaces ML model with evidence-based nutritional logic
"""

from typing import List, Any, Dict
import math

class NutritionEngine:
    """
    Evidence-based nutrition recommendation engine using scientific guidelines
    """
    
    # Nutritional thresholds based on scientific guidelines
    THRESHOLDS = {
        "HIGH_PROTEIN": 15,      # g/100g - good protein source
        "MODERATE_PROTEIN": 8,   # g/100g - decent protein
        "LOW_PROTEIN": 5,        # g/100g - low protein
        
        "HIGH_SUGAR": 10,        # g/100g - high sugar (WHO guidelines)
        "MODERATE_SUGAR": 5,     # g/100g - moderate sugar
        
        "HIGH_FAT": 20,          # g/100g - high fat
        "MODERATE_FAT": 10,      # g/100g - moderate fat
        "LOW_FAT": 3,            # g/100g - low fat
        
        "HIGH_CALORIES": 400,    # kcal/100g - energy dense
        "MODERATE_CALORIES": 200,# kcal/100g - moderate energy
        "LOW_CALORIES": 50,      # kcal/100g - low energy
        
        "FIBER_GOOD": 3,         # g/100g - good fiber content
        "SATURATED_FAT_LIMIT": 5 # g/100g - saturated fat limit
    }
    
    # Goal-specific scoring weights
    GOAL_WEIGHTS = {
        "muscle_gain": {
            "protein_weight": 0.35,
            "calories_weight": 0.25,
            "sugar_penalty": 0.20,
            "fat_weight": 0.15,
            "carbs_weight": 0.05
        },
        "weight_loss": {
            "protein_weight": 0.30,
            "calories_weight": 0.30,  # Higher weight for calorie control
            "sugar_penalty": 0.25,
            "fat_weight": 0.10,
            "carbs_weight": 0.05
        },
        "maintenance": {
            "protein_weight": 0.25,
            "calories_weight": 0.20,
            "sugar_penalty": 0.15,
            "fat_weight": 0.20,
            "carbs_weight": 0.20
        },
        "general_health": {
            "protein_weight": 0.25,
            "calories_weight": 0.15,
            "sugar_penalty": 0.30,  # Higher sugar penalty for health
            "fat_weight": 0.15,
            "carbs_weight": 0.15
        }
    }
    
    def calculate_nutrition_score(self, food_features: Dict, user_features: Dict, user_goals: List[Any]) -> Dict:
        """
        Calculate nutritional score using evidence-based algorithms
        
        Args:
            food_features: Nutrition data per 100g
            user_features: User profile data
            user_goals: User's nutritional goals
            
        Returns:
            Dict with score, recommendation, and reasoning
        """
        
        # Extract nutritional values
        calories = food_features.get('calories', 0)
        protein = food_features.get('protein', 0)
        fat = food_features.get('fat', 0)
        sugar = food_features.get('sugar', 0)
        carbs = food_features.get('carbohydrates', 0)
        
        # Extract user data
        age = user_features.get('age', 30)
        activity_level = user_features.get('activity_level', 2)
        bmi = user_features.get('bmi', 25.0)
        
        # Determine primary goal (default to general_health)
        primary_goal = "general_health"
        goal_weights = self.GOAL_WEIGHTS[primary_goal]
        
        if user_goals:
            goal = user_goals[0]
            # Map goal to our categories (you'll need to adjust based on your goal schema)
            if hasattr(goal, 'goal_type'):
                goal_type = goal.goal_type.lower()
                if "muscle" in goal_type or "gain" in goal_type:
                    primary_goal = "muscle_gain"
                elif "loss" in goal_type or "weight" in goal_type:
                    primary_goal = "weight_loss"
                elif "maintain" in goal_type:
                    primary_goal = "maintenance"
            
            goal_weights = self.GOAL_WEIGHTS[primary_goal]
        
        # Calculate component scores (0-100 scale)
        protein_score = self._calculate_protein_score(protein, primary_goal)
        calorie_score = self._calculate_calorie_score(calories, primary_goal, activity_level)
        sugar_score = self._calculate_sugar_score(sugar, primary_goal)
        fat_score = self._calculate_fat_score(fat, age, primary_goal)
        carb_score = self._calculate_carb_score(carbs, primary_goal, activity_level)
        
        # Apply goal-specific weights
        weighted_score = (
            protein_score * goal_weights["protein_weight"] +
            calorie_score * goal_weights["calories_weight"] +
            sugar_score * goal_weights["sugar_penalty"] +
            fat_score * goal_weights["fat_weight"] +
            carb_score * goal_weights["carbs_weight"]
        )
        
        # Age and BMI adjustments
        age_adjustment = self._calculate_age_adjustment(age, protein, fat, sugar)
        bmi_adjustment = self._calculate_bmi_adjustment(bmi, calories, fat)
        
        final_score = min(100, max(0, weighted_score + age_adjustment + bmi_adjustment))
        
        # Generate recommendation
        is_recommended = final_score >= 60  # 60+ is recommended
        
        # Build detailed reasoning
        reasoning = self._build_reasoning(
            protein_score, calorie_score, sugar_score, fat_score, carb_score,
            primary_goal, age, activity_level, final_score
        )
        
        return {
            "score": round(final_score, 1),
            "recommended": is_recommended,
            "confidence": min(0.95, 0.60 + (final_score / 100) * 0.35),  # 60-95% confidence range
            "reasoning": reasoning,
            "nutritional_breakdown": {
                "protein_score": round(protein_score, 1),
                "calorie_score": round(calorie_score, 1),
                "sugar_score": round(sugar_score, 1),
                "fat_score": round(fat_score, 1),
                "carb_score": round(carb_score, 1)
            },
            "nutritional_details": {
                "calories_per_100g": calories,
                "protein_g": protein,
                "fat_g": fat,
                "sugar_g": sugar,
                "carbs_g": carbs
            }
        }
    
    def _calculate_protein_score(self, protein: float, goal: str) -> float:
        """Calculate protein quality score"""
        if goal == "muscle_gain":
            if protein >= self.THRESHOLDS["HIGH_PROTEIN"]:
                return 100
            elif protein >= self.THRESHOLDS["MODERATE_PROTEIN"]:
                return 80 + (protein - 8) * 2  # Scale up to 100
            else:
                return max(0, protein * 8)  # Linear scale
        else:
            if protein >= self.THRESHOLDS["MODERATE_PROTEIN"]:
                return 90
            elif protein >= self.THRESHOLDS["LOW_PROTEIN"]:
                return 70
            else:
                return max(0, protein * 14)  # More lenient for non-muscle goals
    
    def _calculate_calorie_score(self, calories: float, goal: str, activity_level: int) -> float:
        """Calculate calorie appropriateness score"""
        if goal == "weight_loss":
            if calories <= 150:
                return 100
            elif calories <= 250:
                return 80
            elif calories <= self.THRESHOLDS["HIGH_CALORIES"]:
                return max(0, 100 - (calories - 150) * 0.3)
            else:
                return 20  # Very high calorie penalty
        elif goal == "muscle_gain":
            # Allow higher calories for muscle building
            if calories >= 200:
                return min(100, 60 + (calories - 200) * 0.2)
            else:
                return max(0, calories * 0.5)
        else:
            # Maintenance/general health - moderate calories preferred
            if 100 <= calories <= 300:
                return 90
            elif calories < 100:
                return max(0, calories)
            else:
                return max(0, 100 - (calories - 300) * 0.2)
    
    def _calculate_sugar_score(self, sugar: float, goal: str) -> float:
        """Calculate sugar content score (lower is better)"""
        # Sugar is always a penalty, but more strict for health-focused goals
        sugar_penalty_factor = 2.0 if goal == "general_health" else 1.5
        
        if sugar <= 2:
            return 100  # Excellent - very low sugar
        elif sugar <= self.THRESHOLDS["MODERATE_SUGAR"]:
            return 80  # Good
        elif sugar <= self.THRESHOLDS["HIGH_SUGAR"]:
            return max(0, 60 - (sugar - 5) * 4)  # Moderate penalty
        else:
            return max(0, 40 - (sugar - 10) * sugar_penalty_factor)  # Heavy penalty
    
    def _calculate_fat_score(self, fat: float, age: int, goal: str) -> float:
        """Calculate fat content score"""
        # Age consideration: older adults more sensitive to high fat
        age_factor = 1.2 if age > 50 else 1.0
        
        if goal == "weight_loss":
            # Lower fat preferred for weight loss
            if fat <= self.THRESHOLDS["LOW_FAT"]:
                return 100
            elif fat <= self.THRESHOLDS["MODERATE_FAT"]:
                return 80
            else:
                return max(0, 60 - (fat - 10) * age_factor)
        else:
            # More flexible for other goals
            if fat <= self.THRESHOLDS["MODERATE_FAT"]:
                return 90
            elif fat <= self.THRESHOLDS["HIGH_FAT"]:
                return max(0, 70 - (fat - 10) * age_factor * 0.8)
            else:
                return max(0, 40 - (fat - 20) * age_factor)
    
    def _calculate_carb_score(self, carbs: float, goal: str, activity_level: int) -> float:
        """Calculate carbohydrate score"""
        # Activity level consideration
        activity_bonus = activity_level * 5
        
        if goal == "muscle_gain":
            # Higher carbs okay for muscle building
            return min(100, 60 + activity_bonus + min(carbs * 0.3, 30))
        elif goal == "weight_loss":
            # Lower carbs preferred
            if carbs <= 20:
                return 80 + activity_bonus
            else:
                return max(0, 60 - (carbs - 20) * 0.5 + activity_bonus)
        else:
            # Balanced approach
            if 20 <= carbs <= 40:
                return 85 + activity_bonus
            else:
                return max(0, 70 - abs(carbs - 30) * 0.5 + activity_bonus)
    
    def _calculate_age_adjustment(self, age: int, protein: float, fat: float, sugar: float) -> float:
        """Age-specific nutritional adjustments"""
        adjustment = 0
        
        if age < 25:
            # Younger adults need more protein for growth
            if protein < self.THRESHOLDS["MODERATE_PROTEIN"]:
                adjustment -= 5
        elif age > 50:
            # Older adults: reduce fat and sugar concerns
            if fat > self.THRESHOLDS["MODERATE_FAT"]:
                adjustment -= 3
            if sugar > self.THRESHOLDS["MODERATE_SUGAR"]:
                adjustment -= 2
        
        return adjustment
    
    def _calculate_bmi_adjustment(self, bmi: float, calories: float, fat: float) -> float:
        """BMI-specific adjustments"""
        adjustment = 0
        
        if bmi > 30:  # Obese
            if calories > self.THRESHOLDS["MODERATE_CALORIES"]:
                adjustment -= 8
            if fat > self.THRESHOLDS["MODERATE_FAT"]:
                adjustment -= 5
        elif bmi < 18.5:  # Underweight
            if calories < self.THRESHOLDS["MODERATE_CALORIES"]:
                adjustment += 5
        
        return adjustment
    
    def _build_reasoning(self, protein_score: float, calorie_score: float, sugar_score: float, 
                        fat_score: float, carb_score: float, goal: str, age: int, 
                        activity_level: int, final_score: float) -> str:
        """Build natural language reasoning"""
        reasons = []
        
        # Primary factors
        if protein_score >= 80:
            reasons.append("excellent protein content")
        elif protein_score <= 40:
            reasons.append("low protein content")
        
        if calorie_score >= 80:
            reasons.append("appropriate calorie density")
        elif calorie_score <= 40:
            reasons.append("inappropriate calorie density")
        
        if sugar_score >= 80:
            reasons.append("low sugar content")
        elif sugar_score <= 40:
            reasons.append("high sugar content")
        
        if fat_score >= 80:
            reasons.append("healthy fat profile")
        elif fat_score <= 40:
            reasons.append("high fat content")
        
        # Goal-specific context
        goal_context = {
            "muscle_gain": "supports muscle building goals",
            "weight_loss": "supports weight management goals", 
            "maintenance": "maintains healthy nutrition balance",
            "general_health": "promotes overall health"
        }
        
        reasons.append(goal_context.get(goal, "provides balanced nutrition"))
        
        # Age consideration
        if age > 50 and (fat_score < 60 or sugar_score < 60):
            reasons.append("may require moderation for older adults")
        elif age < 25 and protein_score < 60:
            reasons.append("may need more protein for younger adults")
        
        # Activity consideration
        if activity_level >= 3 and calorie_score < 60:
            reasons.append("may not provide enough energy for active lifestyle")
        
        reasoning = f"This food scores {final_score:.1f}/100 and {', '.join(reasons)}."
        return reasoning

# Global instance
nutrition_engine = NutritionEngine()

def classify_food(food_features: Dict, user_features: Dict, user_goals: List[Any]) -> Dict:
    """
    Main classification function - replaces random forest with rule-based engine
    """
    return nutrition_engine.calculate_nutrition_score(food_features, user_features, user_goals)
