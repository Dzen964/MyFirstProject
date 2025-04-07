from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app.models import NutritionPlan, Meal, Food, MealItem, NutritionLog, FoodLog
from app import db
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, SubmitField, SelectField, FloatField, TimeField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from flask_wtf import FlaskForm
from datetime import datetime, time

nutrition = Blueprint('nutrition', __name__)

class NutritionPlanForm(FlaskForm):
    """Form for creating and editing nutrition plans"""
    name = StringField('Plan Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    is_public = BooleanField('Make Public')
    submit = SubmitField('Save Plan')

class MealForm(FlaskForm):
    """Form for creating and editing meals"""
    name = StringField('Meal Name', validators=[DataRequired(), Length(max=100)])
    time = TimeField('Time', format='%H:%M', validators=[Optional()])
    submit = SubmitField('Save Meal')

class FoodSearchForm(FlaskForm):
    """Form for searching foods"""
    search = StringField('Search Foods', validators=[Length(min=2, max=100)])
    submit = SubmitField('Search')

class AddFoodToMealForm(FlaskForm):
    """Form for adding food to a meal"""
    food_id = SelectField('Food', coerce=int)
    quantity = FloatField('Quantity (servings)', validators=[DataRequired(), NumberRange(min=0.1)], default=1.0)
    notes = TextAreaField('Notes', validators=[Length(max=200)])
    submit = SubmitField('Add Food')

class FoodForm(FlaskForm):
    """Form for creating and editing foods"""
    name = StringField('Food Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    calories = IntegerField('Calories (per 100g)', validators=[DataRequired(), NumberRange(min=0)])
    protein = FloatField('Protein (g per 100g)', validators=[DataRequired(), NumberRange(min=0)])
    carbs = FloatField('Carbohydrates (g per 100g)', validators=[DataRequired(), NumberRange(min=0)])
    fat = FloatField('Fat (g per 100g)', validators=[DataRequired(), NumberRange(min=0)])
    fiber = FloatField('Fiber (g per 100g)', validators=[NumberRange(min=0)], default=0)
    sugar = FloatField('Sugar (g per 100g)', validators=[NumberRange(min=0)], default=0)
    serving_size = FloatField('Serving Size', validators=[DataRequired(), NumberRange(min=0.1)], default=100)
    serving_unit = StringField('Serving Unit', validators=[DataRequired(), Length(max=20)], default='g')
    submit = SubmitField('Save Food')

class LogFoodForm(FlaskForm):
    """Form for logging food intake"""
    food_id = SelectField('Food', coerce=int)
    meal_type = SelectField('Meal Type', 
                          choices=[('Breakfast', 'Breakfast'), 
                                   ('Lunch', 'Lunch'), 
                                   ('Dinner', 'Dinner'), 
                                   ('Snack', 'Snack')])
    quantity = FloatField('Quantity (servings)', validators=[DataRequired(), NumberRange(min=0.1)], default=1.0)
    notes = TextAreaField('Notes', validators=[Length(max=200)])
    submit = SubmitField('Log Food')

@nutrition.route('/nutrition-plans')
@login_required
def nutrition_plans():
    """Display user's nutrition plans"""
    plans = NutritionPlan.query.filter_by(user_id=current_user.id).all()
    public_plans = NutritionPlan.query.filter_by(is_public=True).filter(NutritionPlan.user_id != current_user.id).all()
    return render_template('nutrition/plans.html', title='Nutrition Plans', 
                          plans=plans, public_plans=public_plans)

@nutrition.route('/nutrition-plan/new', methods=['GET', 'POST'])
@login_required
def new_nutrition_plan():
    """Create a new nutrition plan"""
    form = NutritionPlanForm()
    
    if form.validate_on_submit():
        plan = NutritionPlan(
            name=form.name.data,
            description=form.description.data,
            is_public=form.is_public.data,
            user_id=current_user.id
        )
        db.session.add(plan)
        db.session.commit()
        flash('Your nutrition plan has been created!', 'success')
        return redirect(url_for('nutrition.nutrition_plan', plan_id=plan.id))
    
    return render_template('nutrition/create_plan.html', title='New Nutrition Plan', 
                          form=form, legend='Create Nutrition Plan')

@nutrition.route('/nutrition-plan/<int:plan_id>')
@login_required
def nutrition_plan(plan_id):
    """View a specific nutrition plan"""
    plan = NutritionPlan.query.get_or_404(plan_id)
    
    # Check if user has access to this plan
    if plan.user_id != current_user.id and not plan.is_public:
        flash('You do not have access to this nutrition plan.', 'danger')
        return redirect(url_for('nutrition.nutrition_plans'))
    
    meals = plan.meals.order_by(Meal.time).all()
    
    # Calculate nutrition totals for the plan
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    
    for meal in meals:
        for meal_item in meal.meal_items:
            food = meal_item.food
            quantity_factor = meal_item.quantity * (food.serving_size / 100)
            total_calories += food.calories * quantity_factor
            total_protein += food.protein * quantity_factor
            total_carbs += food.carbs * quantity_factor
            total_fat += food.fat * quantity_factor
    
    nutrition_totals = {
        'calories': round(total_calories),
        'protein': round(total_protein, 1),
        'carbs': round(total_carbs, 1),
        'fat': round(total_fat, 1)
    }
    
    return render_template('nutrition/view_plan.html', title=plan.name, 
                          plan=plan, meals=meals, nutrition_totals=nutrition_totals)

@nutrition.route('/nutrition-plan/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_nutrition_plan(plan_id):
    """Edit a nutrition plan"""
    plan = NutritionPlan.query.get_or_404(plan_id)
    
    # Check if user is the owner of this plan
    if plan.user_id != current_user.id:
        flash('You cannot edit this nutrition plan.', 'danger')
        return redirect(url_for('nutrition.nutrition_plans'))
    
    form = NutritionPlanForm()
    
    if form.validate_on_submit():
        plan.name = form.name.data
        plan.description = form.description.data
        plan.is_public = form.is_public.data
        db.session.commit()
        flash('Your nutrition plan has been updated!', 'success')
        return redirect(url_for('nutrition.nutrition_plan', plan_id=plan.id))
    
    elif request.method == 'GET':
        form.name.data = plan.name
        form.description.data = plan.description
        form.is_public.data = plan.is_public
    
    return render_template('nutrition/create_plan.html', title='Edit Nutrition Plan', 
                          form=form, legend='Edit Nutrition Plan')

@nutrition.route('/nutrition-plan/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_nutrition_plan(plan_id):
    """Delete a nutrition plan"""
    plan = NutritionPlan.query.get_or_404(plan_id)
    
    # Check if user is the owner of this plan
    if plan.user_id != current_user.id:
        flash('You cannot delete this nutrition plan.', 'danger')
        return redirect(url_for('nutrition.nutrition_plans'))
    
    db.session.delete(plan)
    db.session.commit()
    flash('Your nutrition plan has been deleted!', 'success')
    return redirect(url_for('nutrition.nutrition_plans'))

@nutrition.route('/nutrition-plan/<int:plan_id>/meal/new', methods=['GET', 'POST'])
@login_required
def new_meal(plan_id):
    """Add a new meal to a plan"""
    plan = NutritionPlan.query.get_or_404(plan_id)
    
    # Check if user is the owner of this plan
    if plan.user_id != current_user.id:
        flash('You cannot add meals to this plan.', 'danger')
        return redirect(url_for('nutrition.nutrition_plans'))
    
    form = MealForm()
    
    if form.validate_on_submit():
        meal = Meal(
            name=form.name.data,
            time=form.time.data,
            plan_id=plan.id
        )
        db.session.add(meal)
        db.session.commit()
        flash('Meal has been added to your plan!', 'success')
        return redirect(url_for('nutrition.meal', meal_id=meal.id))
    
    return render_template('nutrition/create_meal.html', title='New Meal', 
                          form=form, plan=plan)

@nutrition.route('/meal/<int:meal_id>')
@login_required
def meal(meal_id):
    """View a specific meal"""
    meal = Meal.query.get_or_404(meal_id)
    plan = NutritionPlan.query.get(meal.plan_id)
    
    # Check if user has access to this meal
    if plan.user_id != current_user.id and not plan.is_public:
        flash('You do not have access to this meal.', 'danger')
        return redirect(url_for('nutrition.nutrition_plans'))
    
    # Calculate nutrition totals for the meal
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    
    for meal_item in meal.meal_items:
        food = meal_item.food
        quantity_factor = meal_item.quantity * (food.serving_size / 100)
        total_calories += food.calories * quantity_factor
        total_protein += food.protein * quantity_factor
        total_carbs += food.carbs * quantity_factor
        total_fat += food.fat * quantity_factor
    
    nutrition_totals = {
        'calories': round(total_calories),
        'protein': round(total_protein, 1),
        'carbs': round(total_carbs, 1),
        'fat': round(total_fat, 1)
    }
    
    return render_template('nutrition/view_meal.html', title=meal.name, 
                          meal=meal, plan=plan, nutrition_totals=nutrition_totals)

@nutrition.route('/meal/<int:meal_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_meal(meal_id):
    """Edit a meal"""
    meal = Meal.query.get_or_404(meal_id)
    plan = NutritionPlan.query.get(meal.plan_id)
    
    # Check if user is the owner of this meal
    if plan.user_id != current_user.id:
        flash('You cannot edit this meal.', 'danger')
        return redirect(url_for('nutrition.nutrition_plans'))
    
    form = MealForm()
    
    if form.validate_on_submit():
        meal.name = form.name.data
        meal.time = form.time.data
        db.session.commit()
        flash('Your meal has been updated!', 'success')
        return redirect(url_for('nutrition.meal', meal_id=meal.id))
    
    elif request.method == 'GET':
        form.name.data = meal.name
        form.time.data = meal.time
    
    return render_template('nutrition/create_meal.html', title='Edit Meal', 
                          form=form, plan=plan)

@nutrition.route('/meal/<int:meal_id>/delete', methods=['POST'])
@login_required
def delete_meal(meal_id):
    """Delete a meal"""
    meal = Meal.query.get_or_404(meal_id)
    plan = NutritionPlan.query.get(meal.plan_id)
    
    # Check if user is the owner of this meal
    if plan.user_id != current_user.id:
        flash('You cannot delete this meal.', 'danger')
        return redirect(url_for('nutrition.nutrition_plans'))
    
    db.session.delete(meal)
    db.session.commit()
    flash('Your meal has been deleted!', 'success')
    return redirect(url_for('nutrition.nutrition_plan', plan_id=plan.id))

@nutrition.route('/meal/<int:meal_id>/add-food', methods=['GET', 'POST'])
@login_required
def add_food_to_meal(meal_id):
    """Add a food item to a meal"""
    meal = Meal.query.get_or_404(meal_id)
    plan = NutritionPlan.query.get(meal.plan_id)
    
    # Check if user is the owner of this meal
    if plan.user_id != current_user.id:
        flash('You cannot add foods to this meal.', 'danger')
        return redirect(url_for('nutrition.nutrition_plans'))
    
    search_form = FoodSearchForm()
    add_form = AddFoodToMealForm()
    
    # Default to all foods first
    foods = Food.query.order_by(Food.name).all()
    
    if search_form.validate_on_submit():
        search_term = search_form.search.data
        foods = Food.query.filter(Food.name.ilike(f'%{search_term}%')).order_by(Food.name).all()
    
    # Update food choices for add form
    add_form.food_id.choices = [(f.id, f.name) for f in foods]
    
    if add_form.validate_on_submit():
        meal_item = MealItem(
            meal_id=meal.id,
            food_id=add_form.food_id.data,
            quantity=add_form.quantity.data,
            notes=add_form.notes.data
        )
        db.session.add(meal_item)
        db.session.commit()
        flash('Food has been added to your meal!', 'success')
        return redirect(url_for('nutrition.meal', meal_id=meal.id))
    
    return render_template('nutrition/add_food_to_meal.html', title='Add Food to Meal', 
                          search_form=search_form, add_form=add_form, meal=meal, foods=foods)

@nutrition.route('/foods')
@login_required
def foods():
    """Display the food library"""
    search_form = FoodSearchForm()
    search_term = request.args.get('search', '')
    
    if search_term:
        foods = Food.query.filter(Food.name.ilike(f'%{search_term}%')).order_by(Food.name).all()
    else:
        foods = Food.query.order_by(Food.name).all()
    
    return render_template('nutrition/foods.html', title='Food Library', 
                          foods=foods, search_form=search_form, search_term=search_term)

@nutrition.route('/food/<int:food_id>')
@login_required
def food_detail(food_id):
    """View details of a specific food"""
    food = Food.query.get_or_404(food_id)
    return render_template('nutrition/food_detail.html', title=food.name, food=food)

@nutrition.route('/food/new', methods=['GET', 'POST'])
@login_required
def new_food():
    """Create a new food item"""
    form = FoodForm()
    
    if form.validate_on_submit():
        food = Food(
            name=form.name.data,
            description=form.description.data,
            calories=form.calories.data,
            protein=form.protein.data,
            carbs=form.carbs.data,
            fat=form.fat.data,
            fiber=form.fiber.data,
            sugar=form.sugar.data,
            serving_size=form.serving_size.data,
            serving_unit=form.serving_unit.data
        )
        db.session.add(food)
        db.session.commit()
        flash('Your food has been created!', 'success')
        return redirect(url_for('nutrition.food_detail', food_id=food.id))
    
    return render_template('nutrition/create_food.html', title='New Food', form=form)

@nutrition.route('/food/<int:food_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_food(food_id):
    """Edit a food item"""
    food = Food.query.get_or_404(food_id)
    form = FoodForm()
    
    if form.validate_on_submit():
        food.name = form.name.data
        food.description = form.description.data
        food.calories = form.calories.data
        food.protein = form.protein.data
        food.carbs = form.carbs.data
        food.fat = form.fat.data
        food.fiber = form.fiber.data
        food.sugar = form.sugar.data
        food.serving_size = form.serving_size.data
        food.serving_unit = form.serving_unit.data
        db.session.commit()
        flash('Food has been updated!', 'success')
        return redirect(url_for('nutrition.food_detail', food_id=food.id))
    
    elif request.method == 'GET':
        form.name.data = food.name
        form.description.data = food.description
        form.calories.data = food.calories
        form.protein.data = food.protein
        form.carbs.data = food.carbs
        form.fat.data = food.fat
        form.fiber.data = food.fiber
        form.sugar.data = food.sugar
        form.serving_size.data = food.serving_size
        form.serving_unit.data = food.serving_unit
    
    return render_template('nutrition/create_food.html', title='Edit Food', form=form)

@nutrition.route('/log-nutrition', methods=['GET', 'POST'])
@login_required
def log_nutrition():
    """Log food intake"""
    form = LogFoodForm()
    search_form = FoodSearchForm()
    
    # Get today's log or create a new one
    today = datetime.utcnow().date()
    log = NutritionLog.query.filter_by(user_id=current_user.id, date=today).first()
    
    if not log:
        log = NutritionLog(user_id=current_user.id, date=today)
        db.session.add(log)
        db.session.commit()
    
    # Handle food search
    search_term = request.args.get('search', '')
    if search_term:
        foods = Food.query.filter(Food.name.ilike(f'%{search_term}%')).order_by(Food.name).all()
    else:
        foods = Food.query.order_by(Food.name).all()
    
    # Update food choices
    form.food_id.choices = [(f.id, f.name) for f in foods]
    
    if form.validate_on_submit():
        food_log = FoodLog(
            nutrition_log_id=log.id,
            food_id=form.food_id.data,
            meal_type=form.meal_type.data,
            quantity=form.quantity.data,
            notes=form.notes.data
        )
        db.session.add(food_log)
        db.session.commit()
        flash('Food has been logged successfully!', 'success')
        return redirect(url_for('nutrition.nutrition_log', log_id=log.id))
    
    return render_template('nutrition/log_food.html', title='Log Nutrition', 
                          form=form, search_form=search_form, foods=foods, search_term=search_term)

@nutrition.route('/nutrition-history')
@login_required
def nutrition_history():
    """Display user's nutrition logs"""
    logs = NutritionLog.query.filter_by(user_id=current_user.id).order_by(NutritionLog.date.desc()).all()
    return render_template('nutrition/history.html', title='Nutrition History', logs=logs)

@nutrition.route('/nutrition-log/<int:log_id>')
@login_required
def nutrition_log(log_id):
    """View a specific nutrition log"""
    log = NutritionLog.query.get_or_404(log_id)
    
    # Check if user is the owner of this log
    if log.user_id != current_user.id:
        flash('You cannot access this nutrition log.', 'danger')
        return redirect(url_for('nutrition.nutrition_history'))
    
    # Group logs by meal type
    meals = {}
    for food_log in log.food_logs:
        meal_type = food_log.meal_type
        if meal_type not in meals:
            meals[meal_type] = []
        meals[meal_type].append(food_log)
    
    # Calculate nutrition totals
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    
    for food_log in log.food_logs:
        food = Food.query.get(food_log.food_id)
        if food:
            quantity_factor = food_log.quantity * (food.serving_size / 100)
            total_calories += food.calories * quantity_factor
            total_protein += food.protein * quantity_factor
            total_carbs += food.carbs * quantity_factor
            total_fat += food.fat * quantity_factor
    
    nutrition_totals = {
        'calories': round(total_calories),
        'protein': round(total_protein, 1),
        'carbs': round(total_carbs, 1),
        'fat': round(total_fat, 1)
    }
    
    return render_template('nutrition/log_detail.html', title='Nutrition Log', 
                          log=log, meals=meals, nutrition_totals=nutrition_totals)
