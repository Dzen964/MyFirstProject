from app import db
from datetime import datetime

class WorkoutPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=False)
    
    # Relationships
    workouts = db.relationship('Workout', backref='plan', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<WorkoutPlan {self.name}>'


class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    day_of_week = db.Column(db.Integer)  # 0-6 (Monday-Sunday)
    plan_id = db.Column(db.Integer, db.ForeignKey('workout_plan.id'), nullable=False)
    
    # Relationships
    exercises = db.relationship('WorkoutExercise', backref='workout', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Workout {self.name}>'


class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    muscle_group = db.Column(db.String(50))  # e.g. 'Chest', 'Back', 'Legs'
    equipment = db.Column(db.String(100))
    difficulty = db.Column(db.String(20))  # e.g. 'Beginner', 'Intermediate', 'Advanced'
    instructions = db.Column(db.Text)
    image = db.Column(db.String(255))
    video_url = db.Column(db.String(255))
    
    # Relationships
    workout_exercises = db.relationship('WorkoutExercise', backref='exercise', lazy='dynamic')
    
    def __repr__(self):
        return f'<Exercise {self.name}>'


class WorkoutExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)
    sets = db.Column(db.Integer, default=3)
    reps = db.Column(db.String(50))  # e.g. '8-12' or just '10'
    rest = db.Column(db.Integer)  # rest time in seconds
    notes = db.Column(db.Text)
    order = db.Column(db.Integer)  # to maintain the order of exercises
    
    def __repr__(self):
        return f'<WorkoutExercise {self.exercise_id} in Workout {self.workout_id}>'


class WorkoutLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    date_completed = db.Column(db.DateTime)  # New field: null when workout is not completed
    duration = db.Column(db.Integer)  # duration in minutes
    notes = db.Column(db.Text)
    
    # Relationships
    exercise_logs = db.relationship('ExerciseLog', backref='workout_log', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<WorkoutLog {self.id} by User {self.user_id}>'


class ExerciseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_log_id = db.Column(db.Integer, db.ForeignKey('workout_log.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)
    sets_completed = db.Column(db.Integer)
    reps = db.Column(db.String(100))  # e.g. '10,8,8' for 3 sets with respective reps
    weight = db.Column(db.String(100))  # e.g. '50,55,55' for 3 sets with respective weights in kg
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<ExerciseLog {self.id} for Exercise {self.exercise_id}>'
