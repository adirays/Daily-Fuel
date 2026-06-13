
import argparse
import json
import time
import requests
import sqlite3
import os

# Define the canonical nutrient keys
CANONICAL_NUTRIENTS = {
    "energy-kcal_100g": "calories_100g",
    "proteins_100g": "protein_100g",
    "carbohydrates_100g": "carbs_100g",
    "fat_100g": "fat_100g",
}

def get_food_data(food_name: str, max_retries: int = 3, delay: int = 1):
    """
    Fetches food data from the Open Food Facts API for a given food name.
    """
    search_url = f"https://world.openfoodfacts.org/cgi/search.pl"
    params = {
        "search_terms": food_name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 5 
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(search_url, params=params, headers={"User-Agent": "MyNutritionApp/1.0"})
            response.raise_for_status()
            data = response.json()
            if data.get("products"):
                return data["products"][0] # Return the first product
            else:
                return None
        except requests.exceptions.RequestException as e:
            print(f"API request failed for {food_name}: {e}. Retrying in {delay}s...")
            time.sleep(delay)
    return None

def normalize_data(product: dict) -> dict | None:
    """
    Normalizes the product data from Open Food Facts into a canonical format.
    """
    nutriments = product.get("nutriments", {})
    
    # Ensure all required nutrients are present
    if not all(key in nutriments for key in CANONICAL_NUTRIENTS):
        return None

    normalized = {
        "name": product.get("product_name", "Unknown"),
        "barcode": product.get("code", "N/A"),
        "url": product.get("url", ""),
    }
    
    for key, new_key in CANONICAL_NUTRIENTS.items():
        try:
            normalized[new_key] = float(nutriments.get(key, 0))
        except (ValueError, TypeError):
            normalized[new_key] = 0.0

    return normalized

def create_fact_text(normalized_data: dict) -> str:
    """
    Creates a single-line fact text from the normalized data.
    """
    return (
        f'{normalized_data["name"]} — ' 
        f'{normalized_data["calories_100g"]:.0f} kcal/100g, ' 
        f'{normalized_data["protein_100g"]:.1f} g protein/100g'
    )

def seed_data(seed_terms: list[str]):
    """
    Fetches and caches data for a list of seed terms.
    """
    if not os.path.exists("data"):
        os.makedirs("data")

    # Cache to JSONL file
    with open("data/nutrition_facts.jsonl", "w") as f:
        for term in seed_terms:
            product = get_food_data(term)
            if product:
                normalized = normalize_data(product)
                if normalized:
                    fact_text = create_fact_text(normalized)
                    f.write(json.dumps({"fact_text": fact_text, "meta": normalized}) + "\n")
                    print(f"Cached: {fact_text}")

    # Cache to SQLite
    conn = sqlite3.connect("data/app.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY,
            name TEXT,
            barcode TEXT,
            url TEXT,
            calories_100g REAL,
            protein_100g REAL,
            carbs_100g REAL,
            fat_100g REAL
        )
    ''')
    
    with open("data/nutrition_facts.jsonl", "r") as f:
        for line in f:
            data = json.loads(line)
            meta = data["meta"]
            c.execute(
                "INSERT INTO foods (name, barcode, url, calories_100g, protein_100g, carbs_100g, fat_100g) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    meta["name"],
                    meta["barcode"],
                    meta["url"],
                    meta["calories_100g"],
                    meta["protein_100g"],
                    meta["carbs_100g"],
                    meta["fat_100g"],
                ),
            )
    conn.commit()
    conn.close()
    print("Database seeding complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch data from Open Food Facts and prepopulate the database.")
    parser.add_argument("--seed", type=str, help='Comma-separated list of food items to seed (e.g., "paneer,apple,banana").')
    args = parser.parse_args()

    if args.seed:
        seed_terms = [term.strip() for term in args.seed.split(",")]
        seed_data(seed_terms)
