import os
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify, render_template
from whitenoise import WhiteNoise
from scipy.optimize import linprog
from flask_cors import CORS

# Custom modules – ensure these are available in your project
import calculator_functions as cf
import helper_functions as hf

app = Flask(__name__)

app.wsgi_app = WhiteNoise(app.wsgi_app, root="static/", prefix="static/")
CORS(app)
# Load or create food items data (used for optimization)
# food_items_path = "food_items.csv"
# if os.path.exists(food_items_path):
#     food_items = pd.read_csv(food_items_path)
# else:
#     food_items = pd.DataFrame(columns=["food_name", "Price"])

# ---------------------------------------
# API Credentials (if needed)
# ---------------------------------------
APP_ID = 'YOUR_APP_ID'
CLIENT_ID = 'YOUR_CLIENT_ID'
API_KEY = 'YOUR_API_KEY'
API_BASE_URL = 'https://gateway.apyflux.com/search'
# ---------------------------------------

@app.route("/get_sport_macros", methods=["GET"])
def get_sport_macros():
    """
    Returns sport roles along with calculated macronutrients and TDEE.
    Uses default values: weight = 70 kg, age = 25, gender = 'm', and BMR = 1800 kcal.
    """
    weight = 70   # default weight in kg
    age = 25      # default age
    gender = "m"  # default gender
    bmr_default = 1800  # example BMR value for calculations

    results = []
    sport_roles = {
        "Cricket": ["Batsman", "Bowler (Fast)", "Bowler (Spin)", "Wicketkeeper", "Fielder"],
        "Football": ["Goalkeeper", "Defender", "Midfielder", "Forward/Striker"],
        "Badminton": ["Singles", "Doubles"],
        "Tennis": ["Singles", "Doubles"],
        "Athletics": ["Sprinter", "Middle-Distance", "Long-Distance", "Field Events"],
        "Casual Gym": ["General"],
        "Sedentary": ["General"]
    }
    
    for sport, roles in sport_roles.items():
        for role in roles:
            # Calculate TDEE using the sport and role
            tdee_val = cf.tdee(bmr_default, sport, role)
            # Calculate macronutrients (using "maintaining" as the goal and "non-vegetarian" diet)
            protein, carbs, fats, fiber, sat_fats = cf.macros(
                tdee_val, "maintaining", weight, sport, role, "non-vegetarian"
            )
            results.append({
                "sport_role": f"{sport} - {role}",
                "protein": protein,
                "carbs": carbs,
                "fats": fats,
                "tdee": tdee_val
            })
    return jsonify(results)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/food_options")
def food_options():
    if not food_items.empty:
        return jsonify(food_items["food_name"].tolist())
    return jsonify({"error": "food_name items database is unavailable"}), 500

@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        data = request.json
        gender = data["gender"]
        weight = int(data["weight"])
        height = int(data["height"])
        age = int(data["age"])
        sport = data["sport"]
        role = data["role"]
        diet = data["diet"]  # Dietary preference
        is_athlete = data.get("is_athlete", "no").lower() == "yes"
        goal = data["goal"]
        session_times = data.get("session_times", [])

        # Capture new health-related flags
        high_cholesterol = data.get("high_cholesterol", "no").lower() == "yes"
        high_blood_sugar = data.get("high_blood_sugar", "no").lower() == "yes"
        high_blood_pressure = data.get("high_blood_pressure", "no").lower() == "yes"
        heart_rate = data.get("heart_rate")
        heart_rate = float(heart_rate) if heart_rate else None

        if age < 19 or age > 55:
            return jsonify({"error": "Age must be between 19 and 55"}), 400
        if weight < 30:
            return jsonify({"error": "Consult a Doctor"}), 400

        # Calculate BMR and TDEE
        bmr_val = cf.bmr(gender, weight, height, age, is_athlete)
        tdee_val = cf.tdee(bmr_val, sport, role)

        daily_caloric_intake = {
            "cutting": 0.85 * tdee_val,
            "bulking": 1.15 * tdee_val,
            "maintaining": tdee_val,
        }.get(goal, tdee_val)

        # Calculate macronutrients with additional health considerations
        protein, carbohydrates, fats, fibre, saturated_fats = cf.macros(
            int(daily_caloric_intake), goal, weight, sport, role, diet,
            high_cholesterol, high_blood_sugar, high_blood_pressure, heart_rate
        )

        result = {
            "bmr": bmr_val,
            "tdee": tdee_val,
            "daily_caloric_intake": int(daily_caloric_intake),
            "protein": protein,
            "carbohydrates": carbohydrates,
            "fats": fats,
            "fibre": fibre,
            "saturated_fats": saturated_fats,
            "diet": diet
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"An internal error has occurred: {str(e)}"}), 400

@app.route("/optimize", methods=["POST"])
def optimize():
    data = request.json
    selected_foods = data["selected_foods"]
    nutrient_goals = data["nutrient_goals"]

    age = int(data["age"])
    if age < 19:
        return jsonify({"error": "Age must be 19 or older"}), 400
    if age > 100:
        return jsonify({"error": "Age must be 100 or younger"}), 400
    gender = data["gender"]

    # Capture new health-related flags
    high_cholesterol = data.get("high_cholesterol", "no").lower() == "yes"
    high_blood_sugar = data.get("high_blood_sugar", "no").lower() == "yes"
    high_blood_pressure = data.get("high_blood_pressure", "no").lower() == "yes"
    heart_rate = data.get("heart_rate")
    heart_rate = float(heart_rate) if heart_rate else None

    selected_food_items = food_items[food_items["food_name"].isin(selected_foods)]
    c = selected_food_items["Price"].values

    A_ub = []
    b_ub = []
    nutrients = ["Protein", "Carbohydrates", "Fats", "Fibre", "Saturated Fats"]

    for nutrient in nutrients:
        column_name = f"{nutrient} (g)"
        if column_name in selected_food_items.columns:
            nutrient_key = nutrient.lower().replace(" ", "_")
            if nutrient_key in nutrient_goals:
                A_ub.extend([
                    -selected_food_items[column_name].values,
                    selected_food_items[column_name].values,
                ])
                b_ub.extend([
                    -nutrient_goals[nutrient_key],
                    nutrient_goals[nutrient_key] * 1.01
                ])

    nutrients_data = hf.create_nutrients_df()
    nutrient_bounds = cf.nutrient_bounds(age, gender, high_cholesterol, high_blood_sugar, high_blood_pressure, heart_rate)

    for nutrient in nutrients_data.columns[1:]:
        if nutrient.endswith("_RDA"):
            base_nutrient = nutrient[:-4]
            if base_nutrient in selected_food_items.columns:
                A_ub.append(-selected_food_items[base_nutrient].values)
                b_ub.append(-nutrient_bounds[nutrient])
        elif nutrient.endswith("_UL"):
            base_nutrient = nutrient[:-3]
            if base_nutrient in selected_food_items.columns:
                A_ub.append(selected_food_items[base_nutrient].values)
                b_ub.append(nutrient_bounds[nutrient])

    A_ub = np.array(A_ub)
    b_ub = np.array(b_ub)
    bounds = [(0, None) for _ in range(len(selected_food_items))]
    result_lp = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")

    if result_lp.success:
        servings = np.round(result_lp.x, 1)
        quantity = np.round(servings * selected_food_items["Serving (g)"], 1)
        total_cost_per_item = np.round(servings * selected_food_items["Price"], 2)

        nutrient_totals = {}
        for nutrient in selected_food_items.columns[3:]:
            nutrient_totals[nutrient] = np.round(
                np.sum(servings * selected_food_items[nutrient]), 1
            )

        result_data = {
            "food_items": selected_food_items["food_name"].tolist(),
            "servings": servings.tolist(),
            "quantity": quantity.tolist(),
            "total_cost": total_cost_per_item.tolist(),
            "nutrient_totals": nutrient_totals,
            "total_cost_sum": np.sum(total_cost_per_item),
        }
        return jsonify({"success": True, "result": result_data})
    else:
        return jsonify({
            "success": False,
            "message": "Optimization failed! No feasible solution found.",
        })

# Helper function for meal suggestions
def get_suggestions_for_category(meal_category, remaining, df, num_options=5):
    group = df[df['meal_category'].str.lower() == meal_category.lower()].copy()
    if group.empty:
        return []
    
    group['cal'] = pd.to_numeric(group['calories'], errors='coerce').round().astype(int)
    group['protein'] = pd.to_numeric(group['protein'], errors='coerce').round(1)
    group['carbs'] = pd.to_numeric(group['carbs'], errors='coerce').round(1)
    group['fats'] = pd.to_numeric(group['fats'], errors='coerce').round(1)
    
    filtered = group[
        (group['cal'] <= remaining['cal']) &
        (group['protein'] <= remaining['protein']) &
        (group['carbs'] <= remaining['carbs']) &
        (group['fats'] <= remaining['fats'])
    ]
    
    items = filtered.to_dict(orient='records')
    
    def score(item):
        score_val = 0
        if remaining['cal'] > 0:
            score_val += 0.5 * (item['cal'] / remaining['cal'])
        if remaining['protein'] > 0:
            score_val += 0.2 * (item['protein'] / remaining['protein'])
        if remaining['carbs'] > 0:
            score_val += 0.15 * (item['carbs'] / remaining['carbs'])
        if remaining['fats'] > 0:
            score_val += 0.15 * (item['fats'] / remaining['fats'])
        return score_val

    items.sort(key=score, reverse=True)
    return items[:num_options]

def get_meal_categories(meal_count: int):
    if meal_count == 3:
        return ["Breakfast", "Lunch", "Dinner"]
    elif meal_count == 4:
        return ["Breakfast", "Lunch", "Afternoon Snack", "Dinner"]
    elif meal_count == 5:
        return ["Breakfast", "Mid-Morning Snack", "Lunch", "Afternoon Snack", "Dinner"]
    return ["Breakfast", "Lunch", "Dinner"]

@app.route("/suggest_meals", methods=["POST"])
def suggest_meals():
    data = request.json

    try:
        daily_calories = float(data.get("daily_caloric_intake"))
        protein_limit = float(data.get("protein"))
        carb_limit = float(data.get("carbohydrates"))
        fat_limit = float(data.get("fats"))
    except Exception as e:
        return jsonify({"error": "Invalid daily limits provided: " + str(e)}), 400

    # Retrieve user-selected meal count and diet
    meal_count = int(data.get("meal_count", 4))
    user_diet = data.get("diet", "non-vegetarian")  # fallback if missing

    # Read your updated food data that now contains Veg_Label, Health_Label, meal_category, etc.
    try:
        df = pd.read_csv("categorized_food_data.csv")  # or "updated_food_data_final.csv"
    except Exception as e:
        return jsonify({"error": "Error reading food data CSV: " + str(e)}), 500

    # ------------------------------------------------
    # FILTER by Veg_Label based on user diet
    # ------------------------------------------------
    # Suppose Veg_Label can be: "Veg", "Egg", "NonVeg"
    if user_diet.lower() == "vegetarian":
        df = df[df["Veg_Label"].str.lower() == "veg"]
    elif user_diet.lower() == "eggetarian":
        df = df[df["Veg_Label"].str.lower().isin(["veg", "egg"])]
    elif user_diet.lower() == "non-vegetarian":
        # Keep all (or specifically include everything that isn't Veg-only if you want)
        # df = df[df["Veg_Label"].str.lower().isin(["veg", "egg", "nonveg"])]
        pass
    # If you want to handle unknown or special labels, do it here

    # Now proceed with the rest of your existing code for meal selection:
    categories = get_meal_categories(meal_count)
    target_cal = daily_calories / meal_count

    recommended_meal_plan = {}
    meal_options = {}
    used_foods = set()
    total_calories_selected = 0

    for cat in categories:
        group = df[df['meal_category'].str.lower() == cat.lower()].copy()
        if group.empty:
            group = df[df['meal_category'].str.lower().isin(["snack", "general"])].copy()
        # Exclude foods already chosen:
        group = group[~group['food_name'].isin(used_foods)]
        if group.empty:
            recommended_meal_plan[cat] = None
            meal_options[cat] = []
            continue

        group['cal'] = pd.to_numeric(group['calories'], errors='coerce').round().astype(int)
        group['diff'] = (group['cal'] - target_cal).abs()
        best_option = group.sort_values('diff').iloc[0].to_dict()
        used_foods.add(best_option["food_name"])
        recommended_meal_plan[cat] = best_option
        meal_options[cat] = group.sort_values('diff').head(5).to_dict(orient='records')
        total_calories_selected += best_option["cal"]

    # Adjust the last meal’s cals if needed, as you do now
    # ...
    # Return the final JSON result
    result = {
        "meal_options": meal_options,
        "recommended_meal_plan": recommended_meal_plan,
        "Total_Calories": total_calories_selected
    }
    return jsonify(result)

# -----------------------------------------------------------
# NEW ENDPOINT: List all foods tagged as "Healthy" in the CSV
# -----------------------------------------------------------
# @app.route("/list_healthy_foods", methods=["GET"])
# def list_healthy_foods():
#     """
#     Returns all foods (by name) from categorized_food_data.csv
#     that have 'Healthy' in their 'Health_Label' column.
#     """
#     try:
#         df = pd.read_csv("labeled_food_data.csv")
#         # Adjust 'Health_Label' if your CSV uses a different column name
#         df_healthy = df[df["Health_Label"].str.contains("Healthy", case=False, na=False)]
#         if df_healthy.empty:
#             return jsonify({"message": "No healthy foods found."})
#         return jsonify({"healthy_foods": df_healthy["food_name"].tolist()})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
