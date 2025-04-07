from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import WorkoutLog, ExerciseLog, NutritionLog, FoodLog, Workout, Exercise, Meal, Food
from app import db
from datetime import datetime, timedelta
import calendar
from collections import defaultdict

progress = Blueprint('progress', __name__)

@progress.route('/progress')
@login_required
def dashboard():
    """Main progress tracking dashboard showing recent activities and summary"""
    # Get time period for stats (default: last 30 days)
    period = request.args.get('period', '30')
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get recent workout logs
    workout_logs = WorkoutLog.query.filter_by(user_id=current_user.id)\
        .filter(WorkoutLog.date >= start_date)\
        .order_by(WorkoutLog.date.desc())\
        .limit(10).all()
    
    # Get recent nutrition logs
    nutrition_logs = NutritionLog.query.filter_by(user_id=current_user.id)\
        .filter(NutritionLog.date >= start_date)\
        .order_by(NutritionLog.date.desc())\
        .limit(10).all()
    
    # Calculate workout statistics
    workout_stats = {
        'total_workouts': WorkoutLog.query.filter_by(user_id=current_user.id)
            .filter(WorkoutLog.date >= start_date).count(),
        'total_exercises': ExerciseLog.query.join(WorkoutLog)
            .filter(WorkoutLog.user_id == current_user.id)
            .filter(WorkoutLog.date >= start_date).count(),
        'total_weight': db.session.query(db.func.sum(ExerciseLog.weight))
            .join(WorkoutLog)
            .filter(WorkoutLog.user_id == current_user.id)
            .filter(WorkoutLog.date >= start_date)
            .scalar() or 0
    }
    
    # Calculate nutrition statistics
    nutrition_stats = {
        'total_meals': NutritionLog.query.filter_by(user_id=current_user.id)
            .filter(NutritionLog.date >= start_date).count(),
        'total_calories': db.session.query(db.func.sum(FoodLog.calories))
            .join(NutritionLog)
            .filter(NutritionLog.user_id == current_user.id)
            .filter(NutritionLog.date >= start_date)
            .scalar() or 0,
        'total_protein': db.session.query(db.func.sum(FoodLog.protein))
            .join(NutritionLog)
            .filter(NutritionLog.user_id == current_user.id)
            .filter(NutritionLog.date >= start_date)
            .scalar() or 0
    }
    
    return render_template('progress/dashboard.html', 
                          workout_logs=workout_logs, 
                          nutrition_logs=nutrition_logs,
                          workout_stats=workout_stats,
                          nutrition_stats=nutrition_stats,
                          days=days)

@progress.route('/progress/workout-history')
@login_required
def workout_history():
    """Show detailed workout history with filtering options"""
    # Get filter parameters
    workout_id = request.args.get('workout_id', type=int)
    exercise_id = request.args.get('exercise_id', type=int)
    
    # Base query
    query = WorkoutLog.query.filter_by(user_id=current_user.id)
    
    # Apply filters if they exist
    if workout_id:
        query = query.filter_by(workout_id=workout_id)
    
    # Get workout logs
    logs = query.order_by(WorkoutLog.date.desc()).all()
    
    # Get all workouts for the filter dropdown
    workouts = Workout.query.join(WorkoutLog).filter_by(user_id=current_user.id).distinct().all()
    
    # Filter exercise logs if exercise filter is applied
    if exercise_id:
        for log in logs:
            log.exercise_logs = [el for el in log.exercise_logs if el.exercise_id == exercise_id]
    
    # Get all exercises for the filter dropdown
    exercises = Exercise.query.join(ExerciseLog).join(WorkoutLog).filter_by(user_id=current_user.id).distinct().all()
    
    return render_template('progress/workout_history.html', 
                          logs=logs, 
                          workouts=workouts,
                          exercises=exercises,
                          selected_workout=workout_id,
                          selected_exercise=exercise_id)

@progress.route('/progress/nutrition-history')
@login_required
def nutrition_history():
    """Show detailed nutrition history with filtering options"""
    # Get filter parameters
    meal_id = request.args.get('meal_id', type=int)
    food_id = request.args.get('food_id', type=int)
    
    # Base query
    query = NutritionLog.query.filter_by(user_id=current_user.id)
    
    # Apply filters if they exist
    if meal_id:
        query = query.filter_by(meal_id=meal_id)
    
    # Get nutrition logs
    logs = query.order_by(NutritionLog.date.desc()).all()
    
    # Get all meals for the filter dropdown
    meals = Meal.query.join(NutritionLog).filter_by(user_id=current_user.id).distinct().all()
    
    # Filter food logs if food filter is applied
    if food_id:
        for log in logs:
            log.food_logs = [fl for fl in log.food_logs if fl.food_id == food_id]
    
    # Get all foods for the filter dropdown
    foods = Food.query.join(FoodLog).join(NutritionLog).filter_by(user_id=current_user.id).distinct().all()
    
    return render_template('progress/nutrition_history.html', 
                          logs=logs, 
                          meals=meals,
                          foods=foods,
                          selected_meal=meal_id,
                          selected_food=food_id)

@progress.route('/progress/weight-tracker')
@login_required
def weight_tracker():
    """Track user weight changes over time"""
    # Get weights from user profile changes (would need to be logged)
    # For now, return a simple placeholder
    return render_template('progress/weight_tracker.html')

@progress.route('/progress/statistics')
@login_required
def statistics():
    """Show detailed statistics and charts"""
    # Determine time period
    period = request.args.get('period', '30')
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Workout activity by day
    workout_by_day = defaultdict(int)
    for log in WorkoutLog.query.filter_by(user_id=current_user.id)\
        .filter(WorkoutLog.date >= start_date).all():
        day = log.date.strftime("%Y-%m-%d")
        workout_by_day[day] += 1
    
    # Nutrition tracking by day (calories)
    calories_by_day = defaultdict(float)
    for log in NutritionLog.query.filter_by(user_id=current_user.id)\
        .filter(NutritionLog.date >= start_date).all():
        day = log.date.strftime("%Y-%m-%d")
        calories_sum = sum(food_log.calories for food_log in log.food_logs)
        calories_by_day[day] += calories_sum
    
    # Exercise frequency
    exercise_frequency = defaultdict(int)
    exercise_logs = db.session.query(ExerciseLog, Exercise.name)\
        .join(Exercise)\
        .join(WorkoutLog)\
        .filter(WorkoutLog.user_id == current_user.id)\
        .filter(WorkoutLog.date >= start_date).all()
    
    for log, name in exercise_logs:
        exercise_frequency[name] += 1
    
    # Food frequency
    food_frequency = defaultdict(int)
    food_logs = db.session.query(FoodLog, Food.name)\
        .join(Food)\
        .join(NutritionLog)\
        .filter(NutritionLog.user_id == current_user.id)\
        .filter(NutritionLog.date >= start_date).all()
    
    for log, name in food_logs:
        food_frequency[name] += 1
    
    return render_template('progress/statistics.html',
                          workout_by_day=workout_by_day,
                          calories_by_day=calories_by_day,
                          exercise_frequency=dict(sorted(exercise_frequency.items(), key=lambda x: x[1], reverse=True)[:10]),
                          food_frequency=dict(sorted(food_frequency.items(), key=lambda x: x[1], reverse=True)[:10]),
                          days=days)
