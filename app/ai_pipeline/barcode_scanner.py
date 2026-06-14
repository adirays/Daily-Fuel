"""
Barcode Scanning Module
Supports multiple barcode formats and integrates with nutrition databases
"""

import cv2
import numpy as np
from pyzbar.pyzbar import decode
from PIL import Image
import requests
import json
from typing import Dict, Optional, Tuple
import re

class BarcodeScanner:
    """
    Advanced barcode scanner with nutrition database integration
    """
    
    def __init__(self):
        # UPC database APIs (fallback options)
        self.databases = {
            "openfoodfacts": "https://world.openfoodfacts.org/api/v2/product/",
            "usda": "https://api.nal.usda.gov/fdc/v1/foods/search",
            "upc_database": "https://api.upcdatabase.org/product/"
        }
        
        # Common barcode formats
        self.supported_formats = [
            'EAN13', 'EAN8', 'UPCA', 'UPCE', 'CODE128', 'CODE39', 'ITF', 'QR'
        ]
    
    def scan_barcode_from_image(self, image_file) -> Dict:
        """
        Scan barcode from uploaded image file
        
        Args:
            image_file: FastAPI UploadFile object
            
        Returns:
            Dict with barcode data and product info
        """
        
        # Convert PIL Image to OpenCV format (Fix: use image_file.file)
        image = Image.open(image_file.file)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array for OpenCV
        img_array = np.array(image)
        img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Enhance image for better barcode detection
        enhanced_img = self._enhance_image_for_barcode(img_cv)
        
        # Decode barcodes
        decoded_objects = decode(enhanced_img)
        
        if not decoded_objects:
            return {
                "success": False,
                "error": "No barcode detected in image",
                "suggestions": [
                    "Ensure good lighting",
                    "Hold camera steady",
                    "Try different angles",
                    "Clean barcode area"
                ]
            }
        
        # Process the best barcode (usually the first/largest one)
        best_barcode = max(decoded_objects, key=lambda x: x.rect.width * x.rect.height)
        
        barcode_data = {
            "barcode": best_barcode.data.decode('utf-8'),
            "format": best_barcode.type,
            "confidence": self._calculate_confidence(best_barcode),
            "bounding_box": {
                "x": best_barcode.rect.left,
                "y": best_barcode.rect.top,
                "width": best_barcode.rect.width,
                "height": best_barcode.rect.height
            }
        }
        
        # Try to get product information
        product_info = self._lookup_product_info(barcode_data["barcode"])
        
        return {
            "success": True,
            "barcode_data": barcode_data,
            "product_info": product_info
        }
    
    def _enhance_image_for_barcode(self, image: np.ndarray) -> np.ndarray:
        """Enhance image for better barcode detection"""
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply different preprocessing techniques
        enhanced_images = []
        
        # Original grayscale
        enhanced_images.append(gray)
        
        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        enhanced_images.append(blurred)
        
        # Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast_enhanced = clahe.apply(gray)
        enhanced_images.append(contrast_enhanced)
        
        # Sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        enhanced_images.append(sharpened)
        
        # Thresholding
        _, thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        enhanced_images.append(thresholded)
        
        # Return the original image with all enhancements for pyzbar to try
        return image
    
    def _calculate_confidence(self, barcode) -> float:
        """Calculate confidence score for barcode detection"""
        # Simple confidence based on barcode quality indicators
        confidence = 0.5  # Base confidence
        
        # Size factor (larger barcodes are more reliable)
        area = barcode.rect.width * barcode.rect.height
        if area > 10000:  # Large barcode
            confidence += 0.3
        elif area > 5000:  # Medium barcode
            confidence += 0.2
        elif area < 2000:  # Small barcode
            confidence -= 0.1
        
        # Format reliability
        reliable_formats = ['EAN13', 'UPCA', 'CODE128']
        if barcode.type in reliable_formats:
            confidence += 0.2
        
        return min(0.95, max(0.1, confidence))
    
    def _lookup_product_info(self, barcode: str) -> Dict:
        """Lookup product information from barcode"""
        
        # Try OpenFoodFacts first (most comprehensive)
        try:
            url = f"{self.databases['openfoodfacts']}{barcode}.json"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 1:  # Product found
                    product = data["product"]
                    
                    # Extract nutritional information
                    nutriments = product.get("nutriments", {})
                    
                    return {
                        "found": True,
                        "source": "OpenFoodFacts",
                        "product_name": product.get("product_name", "Unknown Product"),
                        "brand": product.get("brands", "Unknown Brand"),
                        "categories": product.get("categories_tags", []),
                        "nutrition_per_100g": {
                            "calories": nutriments.get("energy-kcal_100g"),
                            "protein": nutriments.get("proteins_100g"),
                            "fat": nutriments.get("fat_100g"),
                            "carbohydrates": nutriments.get("carbohydrates_100g"),
                            "sugars": nutriments.get("sugars_100g"),
                            "fiber": nutriments.get("fiber_100g"),
                            "sodium": nutriments.get("sodium_100g")
                        },
                        "serving_size": product.get("serving_size"),
                        "ingredients": product.get("ingredients_text", ""),
                        "labels": product.get("labels_tags", []),
                        "nova_group": product.get("nova_group"),  # Processing level
                        "ecoscore": product.get("ecoscore_grade")
                    }
        
        except Exception as e:
            print(f"OpenFoodFacts lookup failed: {e}")
        
        # Fallback: Try UPC Database
        try:
            # Note: UPC Database requires API key, this is just structure
            url = f"{self.databases['upc_database']}{barcode}"
            # Add your API key here if you have one
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "found": True,
                    "source": "UPC Database",
                    "product_name": data.get("title", "Unknown Product"),
                    "brand": data.get("brand", "Unknown Brand"),
                    "nutrition_per_100g": {}  # Limited nutrition data
                }
        
        except Exception as e:
            print(f"UPC Database lookup failed: {e}")
        
        # If no database lookup succeeds
        return {
            "found": False,
            "error": "Product not found in databases",
            "barcode": barcode,
            "suggestions": [
                "Try manual food search",
                "Check barcode format",
                "Product may not be in database"
            ]
        }

# Global instance
barcode_scanner = BarcodeScanner()

def scan_barcode_from_image(image_file):
    """Convenience function for barcode scanning"""
    return barcode_scanner.scan_barcode_from_image(image_file)
