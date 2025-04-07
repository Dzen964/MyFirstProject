from app import db
from datetime import datetime

class NutritionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    
    # Relationships
    meals = db.relationship('Meal', backref='plan', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<NutritionPlan {self.name}>'


class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g. 'Breakfast', 'Lunch', 'Dinner'
    time = db.Column(db.Time)  # Target time for the meal
    plan_id = db.Column(db.Integer, db.ForeignKey('nutrition_plan.id'), nullable=False)
    
    # Relationships
    meal_items = db.relationship('MealItem', backref='meal', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Meal {self.name} in Plan {self.plan_id}>'


class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    calories = db.Column(db.Integer)  # per 100g
    protein = db.Column(db.Float)  # in grams per 100g
    carbs = db.Column(db.Float)  # in grams per 100g
    fat = db.Column(db.Float)  # in grams per 100g
    fiber = db.Column(db.Float)  # in grams per 100g
    sugar = db.Column(db.Float)  # in grams per 100g
    serving_size = db.Column(db.Float)  # in grams
    serving_unit = db.Column(db.String(20))  # e.g. 'g', 'ml', 'piece'
    image = db.Column(db.String(255))
    
    # Relationships
    meal_items = db.relationship('MealItem', backref='food', lazy='dynamic')
    
    def __repr__(self):
        return f'<Food {self.name}>'


class MealItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('food.id'), nullable=False)
    quantity = db.Column(db.Float, default=1.0)  # number of servings
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<MealItem {self.food_id} in Meal {self.meal_id}>'


class NutritionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    notes = db.Column(db.Text)
    
    # Relationships
    food_logs = db.relationship('FoodLog', backref='nutrition_log', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<NutritionLog {self.id} for User {self.user_id} on {self.date}>'


class FoodLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nutrition_log_id = db.Column(db.Integer, db.ForeignKey('nutrition_log.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('food.id'), nullable=False)
    meal_type = db.Column(db.String(50))  # e.g. 'Breakfast', 'Lunch', 'Dinner', 'Snack'
    time = db.Column(db.DateTime, default=datetime.utcnow)
    quantity = db.Column(db.Float)  # number of servings
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<FoodLog {self.id} for Food {self.food_id}>'
