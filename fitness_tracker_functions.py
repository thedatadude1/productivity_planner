# Fitness Tracker Functions for Pro Planner
# This file contains all workout and diet tracking functionality

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import base64
from PIL import Image
import io

# AI Workout Logging
def ai_log_workout(user_prompt, user_id, db):
    """Use Gemini AI to log workout from natural language"""
    if not st.session_state.get('GEMINI_AVAILABLE', False):
        return 0, "Google Generative AI not available"

    today_str = datetime.now().strftime("%Y-%m-%d")

    system_prompt = f"""You are a fitness assistant. Parse workout information and return JSON.
    Today's date is {today_str}.

    Return ONLY valid JSON with "workouts" array. Each workout must have:
    - exercise_name: name of exercise
    - exercise_type: (strength/cardio/flexibility/sports)
    - sets: number (or null)
    - reps: number (or null)
    - weight: in lbs (or null)
    - distance: in miles (or null)
    - duration_minutes: total time
    - calories_burned: estimated calories
    - notes: any additional details

    Example: {{"workouts": [{{"exercise_name": "Bench Press", "exercise_type": "strength",
    "sets": 3, "reps": 10, "weight": 185, "distance": null, "duration_minutes": 20,
    "calories_burned": 150, "notes": "Felt strong today"}}]}}
    """

    try:
        # Call Gemini (you'll need to import call_gemini from main file)
        from app_multiuser import call_gemini
        response_text, status = call_gemini(system_prompt, user_prompt)

        if not response_text or status != "success":
            return 0, "Failed to get AI response"

        # Parse JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        workouts_data = json.loads(response_text)

        # Add workouts to database
        conn = db.get_connection()
        cursor = conn.cursor()
        workouts_added = 0

        for workout in workouts_data.get("workouts", []):
            cursor.execute(db.convert_sql("""
                INSERT INTO workout_logs
                (user_id, workout_date, exercise_name, exercise_type, sets, reps,
                 weight, distance, duration_minutes, calories_burned, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """), (
                user_id,
                today_str,
                workout.get("exercise_name", "Unknown Exercise"),
                workout.get("exercise_type", "other"),
                workout.get("sets"),
                workout.get("reps"),
                workout.get("weight"),
                workout.get("distance"),
                workout.get("duration_minutes", 0),
                workout.get("calories_burned", 0),
                workout.get("notes", "")
            ))
            workouts_added += 1

        conn.commit()
        conn.close()

        return workouts_added, f"✅ Logged {workouts_added} workout(s)!"

    except Exception as e:
        return 0, f"Error logging workout: {str(e)}"


# AI Diet Logging with Image Support
def ai_log_food(user_prompt, user_id, db, image_file=None):
    """Use Gemini AI to log food from text or image"""
    if not st.session_state.get('GEMINI_AVAILABLE', False):
        return 0, "Google Generative AI not available"

    today_str = datetime.now().strftime("%Y-%m-%d")

    system_prompt = f"""You are a nutrition expert. Analyze food and return nutritional JSON.
    Today's date is {today_str}.

    Return ONLY valid JSON with "meals" array. Each meal must have:
    - meal_type: (breakfast/lunch/dinner/snack)
    - food_description: detailed description
    - calories: estimated total calories
    - protein: grams
    - carbs: grams
    - fats: grams
    - notes: any observations

    Be accurate with calorie estimates. Consider portion sizes carefully.

    Example: {{"meals": [{{"meal_type": "lunch", "food_description": "Grilled chicken breast with rice and broccoli",
    "calories": 450, "protein": 45, "carbs": 40, "fats": 8, "notes": "Healthy balanced meal"}}]}}
    """

    try:
        from app_multiuser import call_gemini

        # If image provided, use vision model
        if image_file is not None:
            # Convert image to base64
            image = Image.open(image_file)
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

            # Add image context to prompt
            user_prompt = f"Analyze this food image and tell me the nutritional information. {user_prompt}"

        response_text, status = call_gemini(system_prompt, user_prompt)

        if not response_text or status != "success":
            return 0, "Failed to get AI response"

        # Parse JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        meals_data = json.loads(response_text)

        # Add meals to database
        conn = db.get_connection()
        cursor = conn.cursor()
        meals_added = 0

        for meal in meals_data.get("meals", []):
            cursor.execute(db.convert_sql("""
                INSERT INTO diet_logs
                (user_id, meal_date, meal_type, food_description, calories, protein, carbs, fats, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """), (
                user_id,
                today_str,
                meal.get("meal_type", "snack"),
                meal.get("food_description", "Food"),
                meal.get("calories", 0),
                meal.get("protein", 0),
                meal.get("carbs", 0),
                meal.get("fats", 0),
                meal.get("notes", "")
            ))
            meals_added += 1

        conn.commit()
        conn.close()

        return meals_added, f"✅ Logged {meals_added} meal(s)!"

    except Exception as e:
        return 0, f"Error logging food: {str(e)}"


# Calculate Personal Records (PRs)
def calculate_prs(user_id, db):
    """Calculate PRs for different exercises, normalizing for distance/time variations"""
    conn = db.get_connection()

    # Strength PRs (max weight for each exercise)
    strength_prs = pd.read_sql_query(db.convert_sql("""
        SELECT
            exercise_name,
            MAX(weight) as max_weight,
            sets,
            reps,
            workout_date
        FROM workout_logs
        WHERE user_id = ? AND exercise_type = 'strength' AND weight IS NOT NULL
        GROUP BY exercise_name
        ORDER BY max_weight DESC
    """), conn, params=[user_id])

    # Cardio PRs (best pace - distance/time ratio)
    cardio_logs = pd.read_sql_query(db.convert_sql("""
        SELECT
            exercise_name,
            distance,
            duration_minutes,
            workout_date,
            (distance / NULLIF(duration_minutes, 0)) * 60 as pace_mph
        FROM workout_logs
        WHERE user_id = ? AND exercise_type = 'cardio'
        AND distance IS NOT NULL AND duration_minutes > 0
        ORDER BY workout_date DESC
    """), conn, params=[user_id])

    # Get best pace for each cardio exercise
    cardio_prs = cardio_logs.groupby('exercise_name').apply(
        lambda x: x.nlargest(1, 'pace_mph')
    ).reset_index(drop=True) if not cardio_logs.empty else pd.DataFrame()

    conn.close()

    return {
        'strength': strength_prs,
        'cardio': cardio_prs
    }


# Calculate weight loss timeline and metrics
def calculate_weight_metrics(user_id, db):
    """Calculate weight loss progress and timeline to goal"""
    conn = db.get_connection()

    # Get user profile
    profile = pd.read_sql_query(db.convert_sql("""
        SELECT * FROM fitness_profile WHERE user_id = ?
    """), conn, params=[user_id])

    if profile.empty:
        return None

    profile = profile.iloc[0]
    current_weight = profile['current_weight']
    goal_weight = profile['goal_weight']
    daily_calorie_goal = profile['daily_calorie_goal']

    # Get recent calorie intake (last 30 days)
    recent_intake = pd.read_sql_query(db.convert_sql("""
        SELECT
            meal_date,
            SUM(calories) as daily_calories
        FROM diet_logs
        WHERE user_id = ? AND meal_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY meal_date
        ORDER BY meal_date DESC
    """), conn, params=[user_id])

    conn.close()

    if recent_intake.empty:
        avg_daily_calories = daily_calorie_goal
    else:
        avg_daily_calories = recent_intake['daily_calories'].mean()

    # Calculate metrics
    weight_to_lose = current_weight - goal_weight
    daily_deficit = daily_calorie_goal - avg_daily_calories if avg_daily_calories < daily_calorie_goal else 0

    # 3500 calories = 1 pound
    days_to_goal = (weight_to_lose * 3500) / daily_deficit if daily_deficit > 0 else None
    estimated_date = datetime.now() + timedelta(days=days_to_goal) if days_to_goal else None

    # Calculate weekly rate
    weekly_rate = (daily_deficit * 7) / 3500 if daily_deficit > 0 else 0

    return {
        'current_weight': current_weight,
        'goal_weight': goal_weight,
        'weight_to_lose': weight_to_lose,
        'avg_daily_calories': avg_daily_calories,
        'daily_calorie_goal': daily_calorie_goal,
        'daily_deficit': daily_deficit,
        'days_to_goal': days_to_goal,
        'estimated_date': estimated_date,
        'weekly_rate': weekly_rate
    }
