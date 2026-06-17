
import requests
import time
from functools import lru_cache

# Simple in-memory cache
_cache = {}
_CACHE_DURATION = 300  # 5 minutes

@lru_cache(maxsize=100)
def search_food_by_name(food_name: str):
    """
    Searches for food with intelligent sorting and caching.
    Prioritizes: exact matches > starts with > contains > others
    """
    
    # Check cache first
    cache_key = food_name.lower().strip()
    current_time = time.time()
    
    if cache_key in _cache:
        cached_data, timestamp = _cache[cache_key]
        if current_time - timestamp < _CACHE_DURATION:
            return cached_data
    
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": food_name,
        "search_simple": 1,
        "action": "process", 
        "json": 1,
        "page_size": 20,  # Limit results for speed
        "sort_by": "popularity"  # Better sorting than last_modified
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)  # 5 second timeout
        response.raise_for_status()
        
        data = response.json()
        products = data.get("products", [])
        
        # Intelligent scoring and sorting
        scored_products = []
        search_lower = food_name.lower().strip()
        
        for product in products:
            product_name = product.get("product_name", "").lower().strip()
            if not product_name:
                continue
                
            # Calculate relevance score
            score = 0
            
            # Exact match = highest score
            if product_name == search_lower:
                score = 100
            # Starts with search term
            elif product_name.startswith(search_lower):
                score = 80
            # Contains search term as whole word
            elif f" {search_lower} " in f" {product_name} ":
                score = 60
            # Contains search term anywhere
            elif search_lower in product_name:
                score = 40
            # Partial word matches
            else:
                words = search_lower.split()
                matches = sum(1 for word in words if word in product_name)
                if matches > 0:
                    score = 20 + (matches * 5)
                else:
                    score = 10
            
            # Boost score for common food items
            if any(term in product_name for term in ['rice', 'chicken', 'beef', 'fish', 'eggs', 'milk', 'bread', 'pasta']):
                score += 5
                
            # Penalize branded or processed foods
            if any(term in product_name for term in ['ben\'s', 'brand', 'processed', 'instant', 'ready']):
                score -= 10
            
            # Ensure serving_size exists
            product["serving_size"] = product.get("serving_size", "100g")
            
            scored_products.append((score, product))
        
        # Sort by score (highest first) and take top 10
        scored_products.sort(key=lambda x: x[0], reverse=True)
        data["products"] = [product for score, product in scored_products[:10]]
        
        # Cache the result
        _cache[cache_key] = (data, current_time)
        
        return data
        
    except requests.exceptions.RequestException:
        # Return cached data if available, even if expired
        if cache_key in _cache:
            return _cache[cache_key][0]
        return {"products": []}
    except Exception as e:
        print(f"Food search error: {e}")
        return {"products": []}
