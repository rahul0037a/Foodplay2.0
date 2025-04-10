#!/usr/bin/env python3
import pandas as pd

def classify_foods(input_csv: str, output_csv: str = "labeled_food_data.csv"):
    """
    Reads a CSV file with columns: 
      [calories_calculated_for, basic_unit_measure, fats, carbs, protien, calories]
    Classifies each food as 'Healthy' or 'Not Healthy' based on numeric criteria,
    then saves the updated data (with a new 'Health_Label' column) to output_csv.
    
    Example criteria (adjust as needed):
      - calories <= 400
      - protien >= 10
      - fats <= 15
      (No strict carbs limit here, but you can add one.)

    Parameters:
    -----------
    input_csv : str
        Path to the original categorized_food_data.csv
    output_csv : str
        Path to save the updated CSV with health labels
    """

    # Load the CSV into a DataFrame
    df = pd.read_csv(input_csv)

    # Convert relevant columns to numeric in case they are strings
    df["fats"] = pd.to_numeric(df["fats"], errors="coerce")
    df["carbs"] = pd.to_numeric(df["carbs"], errors="coerce")
    df["protein"] = pd.to_numeric(df["protein"], errors="coerce")
    df["calories"] = pd.to_numeric(df["calories"], errors="coerce")

    # Define your basic thresholds (adjust as you see fit)
    MAX_CALORIES = 400
    MIN_PROTEIN = 10
    MAX_FAT = 15

    # Classification function for a single row
    def is_healthy(row):
        cals = row["calories"] if pd.notnull(row["calories"]) else 999999
        protein = row["protein"] if pd.notnull(row["protein"]) else 0
        fat = row["fats"] if pd.notnull(row["fats"]) else 999999

        if (cals <= MAX_CALORIES) and (protein >= MIN_PROTEIN) and (fat <= MAX_FAT):
            return "Healthy"
        else:
            return "Not Healthy"

    # Apply classification across the DataFrame
    df["Health_Label"] = df.apply(is_healthy, axis=1)

    # Save the updated DataFrame to a new CSV file
    df.to_csv(output_csv, index=False)
    print(f"[INFO] Classification complete. Updated file saved to: {output_csv}")

if __name__ == "__main__":
    # Modify paths as needed:
    input_csv_path = "categorized_food_data.csv"
    output_csv_path = "labeled_food_data.csv"

    classify_foods(input_csv_path, output_csv_path)
