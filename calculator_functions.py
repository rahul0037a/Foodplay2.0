import pandas as pd

def bmr(gender: str, weight: float, height: float, age: int, is_athlete: bool = False) -> int:
    """
    Calculate Basal Metabolic Rate (BMR).
    Uses a specialized formula for athletes.
    """
    sex_value = 0 if gender.lower() == "m" else 1  # Male=0, Female=1
    
    if is_athlete:
        return int(21.2 * weight + 6.7 * height - 2.9 * age - 95 * sex_value - 764)
    
    # Standard Mifflin-St Jeor Equation
    if gender.lower() == "m":
        return int(10 * weight + 6.25 * height - 5 * age + 5)
    elif gender.lower() == "f":
        return int(10 * weight + 6.25 * height - 5 * age - 161)
    
    raise ValueError("Gender must be 'm' or 'f'.")

def get_activity_multiplier(sport: str, role: str) -> float:
    """
    Returns the activity multiplier based on the sport and role.
    """
    sport_role_multipliers = {
        "Cricket": {
            "Batsman": 1.88,
            "Bowler (Fast)": 2.1,
            "Bowler (Spin)": 1.9,
            "Wicketkeeper": 2.1,
            "Fielder": 1.75,
        },
        "Football": {
            "Goalkeeper": 1.7,
            "Defender": 2.1,
            "Midfielder": 2.45,
            "Forward/Striker": 2.35,
        },
        "Badminton": {
            "Singles": 2.45,
            "Doubles": 2.15,
        },
        "Tennis": {
            "Singles": 2.35,
            "Doubles": 2.15,
        },
        "Athletics": {
            "Sprinter": 2.6,
            "Middle-Distance": 2.45,
            "Long-Distance": 2.7,
            "Field Events": 2.15,
        },
        "Casual Gym": {"General": 1.4},
        "Sedentary": {"General": 1.2},
    }
    return sport_role_multipliers.get(sport, {}).get(role, 1.2)  # Default multiplier if not found

def tdee(bmr: int, sport: str, role: str) -> int:
    """
    Calculate Total Daily Energy Expenditure (TDEE) using the activity multiplier.
    """
    activity_multiplier = get_activity_multiplier(sport, role)
    return int(bmr * activity_multiplier)

sport_protein_multiplier = {
    "Cricket - Batsman": 1.2,
    "Cricket - Bowler (Fast)": 1.5,
    "Cricket - Bowler (Spin)": 1.3,
    "Football - Forward/Striker": 1.6,
    "Football - Midfielder": 1.5,
    "Football - Defender": 1.4,
    "Badminton - Singles": 1.5,
    "Badminton - Doubles": 1.3,
    "Tennis - Singles": 1.6,
    "Tennis - Doubles": 1.4,
    "Athletics - Sprinter": 1.7,
    "Athletics - Middle-Distance": 1.6,
    "Athletics - Long-Distance": 1.8,
    "Casual Gym": 1.2,
    "Sedentary": 1.0,
}


def adjust_protein_needs(weight: float, age: int, gender: str, sport: str) -> float:
    """
    Adjusts protein intake based on sport type, age, gender, and weight.
    """
    sport_protein_multiplier = {
        "Cricket - Batsman": 1.2,
        "Cricket - Bowler (Fast)": 1.5,
        "Cricket - Bowler (Spin)": 1.3,
        "Football - Forward/Striker": 1.6,
        "Football - Midfielder": 1.5,
        "Football - Defender": 1.4,
        "Badminton - Singles": 1.5,
        "Badminton - Doubles": 1.3,
        "Tennis - Singles": 1.6,
        "Tennis - Doubles": 1.4,
        "Athletics - Sprinter": 1.7,
        "Athletics - Middle-Distance": 1.6,
        "Athletics - Long-Distance": 1.8,
        "Casual Gym": 1.2,
        "Sedentary": 1.0,
    }
    base_protein = 1.2 * weight  # Minimum requirement
    sport_multiplier = sport_protein_multiplier.get(sport, 1.2)
    
    # Slightly higher for males
    if gender.lower() == "m":
        sport_multiplier *= 1.1  
    
    # Adjust for older age
    if age > 50:
        sport_multiplier *= 0.9  
    
    max_protein = min(sport_multiplier * weight, 2.2 * weight)  # Cap protein intake
    
    return max_protein

def adjust_carbs_fats(tdee: float, sport: str) -> tuple[int, int]:
    """
    Adjusts carbohydrate and fat proportions based on the type of sport and TDEE.
    """
    sport_carb_fat_ratio = {
        "Endurance Sports": {"carb": 0.55, "fat": 0.20},
        "Strength Sports": {"carb": 0.45, "fat": 0.25},
        "Mixed Sports": {"carb": 0.50, "fat": 0.22},
        "Sedentary": {"carb": 0.40, "fat": 0.30},
    }

    if sport in ["Athletics - Long-Distance", "Football - Midfielder"]:
        category = "Endurance Sports"
    elif sport in ["Powerlifting", "Bodybuilding"]:
        category = "Strength Sports"
    elif sport in ["Football - Defender", "Cricket - Bowler (Fast)", "Tennis - Singles"]:
        category = "Mixed Sports"
    else:
        category = "Sedentary"

    carb_ratio = sport_carb_fat_ratio[category]["carb"]
    fat_ratio = sport_carb_fat_ratio[category]["fat"]

    carbohydrates = int(carb_ratio * tdee / 4)  # 1g carb = 4 kcal
    fats = int(fat_ratio * tdee / 9)              # 1g fat = 9 kcal

    return carbohydrates, fats

def macros(daily_caloric_intake: float, goal: str, weight: float, sport: str, role: str, diet: str,
           high_cholesterol: bool = False, high_blood_sugar: bool = False, high_blood_pressure: bool = False, heart_rate: float = None
           ) -> tuple[int, int, int, int, int]:
    sport_role_key = f"{sport} - {role}"
    protein_multiplier = sport_protein_multiplier.get(sport_role_key, 1.2)
    protein = min(max(protein_multiplier * weight, 1.0 * weight), 2.2 * weight)
    if diet == "vegetarian":
        protein = max(protein * 0.9, 1.0 * weight)
    elif diet == "eggetarian":
        protein = max(protein, 1.2 * weight)
    protein_calories = protein * 4

    fat_ratio = 0.25
    fat_calories = fat_ratio * daily_caloric_intake
    fats = fat_calories / 9

    remaining_calories = daily_caloric_intake - (protein_calories + fat_calories)
    carbohydrates = remaining_calories / 4

    protein = int(protein)
    carbohydrates = max(50, int(carbohydrates))
    fats = max(30, int(fats))
    fibre = int(0.014 * daily_caloric_intake)
    saturated_fats = int(0.10 * daily_caloric_intake / 9)

    # Adjustments based on health conditions
    if high_cholesterol:
        fats = int(fats * 0.9)           # Reduce fats by 10%
        saturated_fats = int(saturated_fats * 0.8)  # Reduce saturated fats by 20%
    if high_blood_sugar:
        carbohydrates = int(carbohydrates * 0.9)    # Reduce carbohydrates by 10%
        fibre = int(fibre * 1.1)                      # Increase fibre by 10%
    if high_blood_pressure:
        fats = int(fats * 0.95)         # Slight reduction in fats (or any other desired adjustment)
    if heart_rate is not None and heart_rate > 80:  # Arbitrary threshold for elevated resting heart rate
        fats = int(fats * 0.95)         # Further tighten fat recommendations

    return protein, carbohydrates, fats, fibre, saturated_fats

    return protein, carbohydrates, fats, fibre, saturated_fats

def nutrient_bounds(age: int, gender: str, high_cholesterol: bool = False, high_blood_sugar: bool = False, high_blood_pressure: bool = False, heart_rate: float = None) -> dict:
    bounds = {
        "Protein_RDA": 50, "Protein_UL": 200,
        "Carbohydrates_RDA": 130, "Carbohydrates_UL": 400,
        "Fats_RDA": 70, "Fats_UL": 100,
        "Fibre_RDA": 30, "Fibre_UL": 60,
        "Saturated Fats_RDA": 20, "Saturated Fats_UL": 30,
    }
    if high_cholesterol:
        bounds["Fats_UL"] = 0.9 * bounds["Fats_UL"]
        bounds["Saturated Fats_UL"] = 0.8 * bounds["Saturated Fats_UL"]
    if high_blood_sugar:
        bounds["Carbohydrates_UL"] = 0.9 * bounds["Carbohydrates_UL"]
    if high_blood_pressure:
        bounds["Sodium_UL"] = 1500  # Example value in mg/day (ensure your food data has a 'Sodium' column)
    if heart_rate is not None and heart_rate > 80:
        bounds["Fats_UL"] = 0.95 * bounds["Fats_UL"]
    return bounds
