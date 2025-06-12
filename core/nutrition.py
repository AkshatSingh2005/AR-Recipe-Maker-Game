import requests
import numpy as np
import cv2

# Ingredient flags
UNHEALTHY_INGREDIENTS = ['palm oil', 'high-fructose corn syrup', 'hydrogenated oil']
ALLERGENS = ['gluten', 'milk', 'soy', 'egg', 'nuts', 'peanuts', 'wheat']
SUSPICIOUS_ADDITIVES = ['e102', 'e110', 'e120', 'e124', 'e250', 'e621']

def analyze_ingredients(ingredient_text):
    ingredients = ingredient_text.lower().replace("(", "").replace(")", "").replace(".", "").split(",")
    flagged = {"unhealthy": [], "allergens": [], "suspicious": [], "natural": []}
    for ing in ingredients:
        ing = ing.strip()
        if any(x in ing for x in UNHEALTHY_INGREDIENTS):
            flagged["unhealthy"].append(ing)
        elif any(x in ing for x in ALLERGENS):
            flagged["allergens"].append(ing)
        elif any(x in ing for x in SUSPICIOUS_ADDITIVES):
            flagged["suspicious"].append(ing)
        elif ing != '':
            flagged["natural"].append(ing)
    return flagged

def calculate_health_score(ingredient_analysis):
    score = 100
    score -= len(ingredient_analysis.get("unhealthy", [])) * 30
    score -= len(ingredient_analysis.get("allergens", [])) * 20
    score -= len(ingredient_analysis.get("suspicious", [])) * 10
    return max(0, min(score, 100))

def get_nutrition_from_api(barcode):
    try:
        res = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json", timeout=5)
        data = res.json()
        if data.get('status') != 1:
            return {"name": "Product not found", "calories": "N/A", "protein": "N/A", "fat": "N/A",
                    "ingredients": "N/A", "ingredient_analysis": {}}

        product = data['product']
        name = product.get('product_name', 'Unknown Product')
        nutriments = product.get('nutriments', {})
        calories = nutriments.get('energy-kcal_100g', 'N/A')
        protein = nutriments.get('proteins_100g', 'N/A')
        fat = nutriments.get('fat_100g', 'N/A')
        ingredients_text = product.get('ingredients_text', 'N/A')
        ingredient_analysis = analyze_ingredients(ingredients_text)

        return {
            "name": name,
            "calories": f"{calories} kcal",
            "protein": f"{protein} g",
            "fat": f"{fat} g",
            "ingredients": ingredients_text,
            "ingredient_analysis": ingredient_analysis
        }

    except:
        return {"name": "Error fetching data", "calories": "N/A", "protein": "N/A", "fat": "N/A",
                "ingredients": "N/A", "ingredient_analysis": {}}

def draw_circular_meter(frame, box_points, score):
    pts = np.array([(point.x, point.y) for point in box_points], np.int32)
    x, y, w, h = cv2.boundingRect(pts)
    center = (x + w // 2, y + h // 2)
    radius = max(w, h) // 2 + 15

    if score > 75:
        color = (0, 255, 0)
    elif score > 50:
        color = (0, 255, 255)
    elif score > 25:
        color = (0, 165, 255)
    else:
        color = (0, 0, 255)

    thickness = 6
    start_angle = -90
    end_angle = int((score / 100) * 360) - 90

    cv2.circle(frame, center, radius, (50, 50, 50), thickness)
    cv2.ellipse(frame, center, (radius, radius), 0, start_angle, end_angle, color, thickness)
    cv2.putText(frame, f"{score}%", (center[0] - 25, center[1] + 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

def safe_float(val):
    try:
        return float(str(val).split()[0])
    except:
        return 0.0