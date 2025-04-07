from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app.models import WorkoutPlan, Workout, Exercise, WorkoutExercise, WorkoutLog, ExerciseLog
from app import db
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, SubmitField, SelectField, FloatField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from flask_wtf import FlaskForm
from datetime import datetime

workouts = Blueprint('workouts', __name__)

class WorkoutPlanForm(FlaskForm):
    """Form for creating and editing workout plans"""
    name = StringField('Plan Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    is_public = BooleanField('Make Public')
    submit = SubmitField('Save Plan')

class WorkoutForm(FlaskForm):
    """Form for creating and editing workouts"""
    name = StringField('Workout Name', validators=[DataRequired(), Length(max=100)])
    day_of_week = SelectField('Day', choices=[
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), 
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
    ], coerce=int)
    submit = SubmitField('Save Workout')

class WorkoutExerciseForm(FlaskForm):
    """Form for adding exercises to a workout"""
    exercise_id = SelectField('Exercise', coerce=int)
    sets = IntegerField('Sets', validators=[DataRequired(), NumberRange(min=1)], default=3)
    reps = StringField('Reps', validators=[DataRequired()], default='8-12')
    rest = IntegerField('Rest (seconds)', validators=[Optional()], default=60)
    notes = TextAreaField('Notes', validators=[Length(max=500)])
    submit = SubmitField('Add Exercise')

class WorkoutLogForm(FlaskForm):
    """Form for logging a completed workout"""
    workout_id = SelectField('Workout', coerce=int)
    duration = IntegerField('Duration (minutes)', validators=[DataRequired(), NumberRange(min=1)])
    notes = TextAreaField('Notes', validators=[Length(max=500)])
    submit = SubmitField('Log Workout')

class ExerciseLogForm(FlaskForm):
    """Form for logging completed exercises"""
    sets_completed = IntegerField('Sets Completed', validators=[DataRequired(), NumberRange(min=1)])
    reps = StringField('Reps (comma separated)', validators=[DataRequired()])
    weight = StringField('Weight (kg, comma separated)', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Length(max=500)])
    submit = SubmitField('Log Exercise')

@workouts.route('/workout-plans')
@login_required
def workout_plans():
    """Display user's workout plans"""
    plans = WorkoutPlan.query.filter_by(user_id=current_user.id).all()
    public_plans = WorkoutPlan.query.filter_by(is_public=True).filter(WorkoutPlan.user_id != current_user.id).all()
    return render_template('workouts/plans.html', title='Workout Plans', 
                          plans=plans, public_plans=public_plans)

@workouts.route('/workout-plan/new', methods=['GET', 'POST'])
@login_required
def new_workout_plan():
    """Create a new workout plan"""
    form = WorkoutPlanForm()
    
    if form.validate_on_submit():
        plan = WorkoutPlan(
            name=form.name.data,
            description=form.description.data,
            is_public=form.is_public.data,
            user_id=current_user.id
        )
        db.session.add(plan)
        db.session.commit()
        flash('Your workout plan has been created!', 'success')
        return redirect(url_for('workouts.workout_plan', plan_id=plan.id))
    
    return render_template('workouts/create_plan.html', title='New Workout Plan', 
                          form=form, legend='Create Workout Plan')

@workouts.route('/workout-plan/<int:plan_id>')
@login_required
def workout_plan(plan_id):
    """View a specific workout plan"""
    plan = WorkoutPlan.query.get_or_404(plan_id)
    
    # Check if user has access to this plan
    if plan.user_id != current_user.id and not plan.is_public:
        flash('You do not have access to this workout plan.', 'danger')
        return redirect(url_for('workouts.workout_plans'))
    
    workouts_by_day = {}
    for day in range(7):
        workouts_by_day[day] = []
    
    for workout in plan.workouts:
        if workout.day_of_week is not None:
            workouts_by_day[workout.day_of_week].append(workout)
    
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    return render_template('workouts/view_plan.html', title=plan.name, 
                          plan=plan, workouts_by_day=workouts_by_day, day_names=day_names)

@workouts.route('/workout-plan/<int:plan_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_workout_plan(plan_id):
    """Edit a workout plan"""
    plan = WorkoutPlan.query.get_or_404(plan_id)
    
    # Check if user is the owner of this plan
    if plan.user_id != current_user.id:
        flash('You cannot edit this workout plan.', 'danger')
        return redirect(url_for('workouts.workout_plans'))
    
    form = WorkoutPlanForm()
    
    if form.validate_on_submit():
        plan.name = form.name.data
        plan.description = form.description.data
        plan.is_public = form.is_public.data
        db.session.commit()
        flash('Your workout plan has been updated!', 'success')
        return redirect(url_for('workouts.workout_plan', plan_id=plan.id))
    
    elif request.method == 'GET':
        form.name.data = plan.name
        form.description.data = plan.description
        form.is_public.data = plan.is_public
    
    return render_template('workouts/create_plan.html', title='Edit Workout Plan', 
                          form=form, legend='Edit Workout Plan')

@workouts.route('/workout-plan/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_workout_plan(plan_id):
    """Delete a workout plan"""
    plan = WorkoutPlan.query.get_or_404(plan_id)
    
    # Check if user is the owner of this plan
    if plan.user_id != current_user.id:
        flash('You cannot delete this workout plan.', 'danger')
        return redirect(url_for('workouts.workout_plans'))
    
    db.session.delete(plan)
    db.session.commit()
    flash('Your workout plan has been deleted!', 'success')
    return redirect(url_for('workouts.workout_plans'))

@workouts.route('/workout-plan/<int:plan_id>/workout/new', methods=['GET', 'POST'])
@login_required
def new_workout(plan_id):
    """Add a new workout to a plan"""
    plan = WorkoutPlan.query.get_or_404(plan_id)
    
    # Check if user is the owner of this plan
    if plan.user_id != current_user.id:
        flash('You cannot add workouts to this plan.', 'danger')
        return redirect(url_for('workouts.workout_plans'))
    
    form = WorkoutForm()
    
    if form.validate_on_submit():
        workout = Workout(
            name=form.name.data,
            day_of_week=form.day_of_week.data,
            plan_id=plan.id
        )
        db.session.add(workout)
        db.session.commit()
        flash('Workout has been added to your plan!', 'success')
        return redirect(url_for('workouts.workout', workout_id=workout.id))
    
    return render_template('workouts/create_workout.html', title='New Workout', 
                          form=form, legend='Add Workout', plan=plan)

@workouts.route('/workout/<int:workout_id>')
@login_required
def workout(workout_id):
    """View a specific workout"""
    workout = Workout.query.get_or_404(workout_id)
    plan = WorkoutPlan.query.get(workout.plan_id)
    
    # Check if user has access to this workout
    if plan.user_id != current_user.id and not plan.is_public:
        flash('You do not have access to this workout.', 'danger')
        return redirect(url_for('workouts.workout_plans'))
    
    exercises = workout.exercises.order_by(WorkoutExercise.order).all()
    
    return render_template('workouts/view_workout.html', title=workout.name, 
                          workout=workout, plan=plan, exercises=exercises)

@workouts.route('/workout/<int:workout_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_workout(workout_id):
    """Edit a workout"""
    workout = Workout.query.get_or_404(workout_id)
    plan = WorkoutPlan.query.get(workout.plan_id)
    
    # Check if user is the owner of this workout
    if plan.user_id != current_user.id:
        flash('You cannot edit this workout.', 'danger')
        return redirect(url_for('workouts.workout_plans'))
    
    form = WorkoutForm()
    
    if form.validate_on_submit():
        workout.name = form.name.data
        workout.day_of_week = form.day_of_week.data
        db.session.commit()
        flash('Your workout has been updated!', 'success')
        return redirect(url_for('workouts.workout', workout_id=workout.id))
    
    elif request.method == 'GET':
        form.name.data = workout.name
        form.day_of_week.data = workout.day_of_week
    
    return render_template('workouts/create_workout.html', title='Edit Workout', 
                          form=form, legend='Edit Workout', plan=plan)

@workouts.route('/workout/<int:workout_id>/delete', methods=['POST'])
@login_required
def delete_workout(workout_id):
    """Delete a workout"""
    workout = Workout.query.get_or_404(workout_id)
    plan = WorkoutPlan.query.get(workout.plan_id)
    
    # Check if user is the owner of this workout
    if plan.user_id != current_user.id:
        flash('You cannot delete this workout.', 'danger')
        return redirect(url_for('workouts.workout_plans'))
    
    db.session.delete(workout)
    db.session.commit()
    flash('Your workout has been deleted!', 'success')
    return redirect(url_for('workouts.workout_plan', plan_id=plan.id))

@workouts.route('/workout/<int:workout_id>/exercise/add', methods=['GET', 'POST'])
@login_required
def add_exercise(workout_id):
    """Add an exercise to a workout"""
    workout = Workout.query.get_or_404(workout_id)
    plan = WorkoutPlan.query.get(workout.plan_id)
    
    # Check if user is the owner of this workout
    if plan.user_id != current_user.id:
        flash('You cannot add exercises to this workout.', 'danger')
        return redirect(url_for('workouts.workout_plans'))
    
    form = WorkoutExerciseForm()
    
    # Populate exercise choices
    exercises = Exercise.query.order_by(Exercise.name).all()
    form.exercise_id.choices = [(e.id, e.name) for e in exercises]
    
    if form.validate_on_submit():
        # Get the next order number
        max_order = db.session.query(db.func.max(WorkoutExercise.order)).filter_by(workout_id=workout_id).scalar() or 0
        
        workout_exercise = WorkoutExercise(
            workout_id=workout.id,
            exercise_id=form.exercise_id.data,
            sets=form.sets.data,
            reps=form.reps.data,
            rest=form.rest.data,
            notes=form.notes.data,
            order=max_order + 1
        )
        db.session.add(workout_exercise)
        db.session.commit()
        flash('Exercise has been added to your workout!', 'success')
        return redirect(url_for('workouts.workout', workout_id=workout.id))
    
    return render_template('workouts/add_exercise.html', title='Add Exercise', 
                          form=form, workout=workout)

@workouts.route('/exercises')
@login_required
def exercises():
    """Display the exercise library"""
    exercises = Exercise.query.order_by(Exercise.name).all()
    return render_template('workouts/exercises.html', title='Exercise Library', 
                          exercises=exercises)

@workouts.route('/exercise/<int:exercise_id>')
@login_required
def exercise_detail(exercise_id):
    """View details of a specific exercise"""
    exercise = Exercise.query.get_or_404(exercise_id)
    return render_template('workouts/exercise_detail.html', title=exercise.name, 
                          exercise=exercise)

@workouts.route('/log-workout', methods=['GET', 'POST'])
@login_required
def log_workout():
    """Log a completed workout"""
    form = WorkoutLogForm()
    
    # Get workouts from user's plans
    user_plans = WorkoutPlan.query.filter_by(user_id=current_user.id).all()
    workouts = []
    for plan in user_plans:
        workouts.extend(plan.workouts.all())
    
    # Populate workout choices
    form.workout_id.choices = [(w.id, f"{w.name} ({WorkoutPlan.query.get(w.plan_id).name})") for w in workouts]
    
    if form.validate_on_submit():
        workout_log = WorkoutLog(
            user_id=current_user.id,
            workout_id=form.workout_id.data,
            duration=form.duration.data,
            notes=form.notes.data
        )
        db.session.add(workout_log)
        db.session.commit()
        flash('Workout has been logged successfully!', 'success')
        return redirect(url_for('workouts.log_exercise', log_id=workout_log.id))
    
    return render_template('workouts/log_workout.html', title='Log Workout', 
                          form=form)

@workouts.route('/log-workout/<int:log_id>/exercises', methods=['GET', 'POST'])
@login_required
def log_exercise(log_id):
    """Log exercises for a completed workout"""
    workout_log = WorkoutLog.query.get_or_404(log_id)
    
    # Check if user is the owner of this log
    if workout_log.user_id != current_user.id:
        flash('You cannot access this workout log.', 'danger')
        return redirect(url_for('workouts.log_workout'))
    
    workout = Workout.query.get(workout_log.workout_id)
    if not workout:
        flash('The associated workout does not exist.', 'danger')
        return redirect(url_for('workouts.log_workout'))
    
    # Get exercises for this workout
    workout_exercises = workout.exercises.order_by(WorkoutExercise.order).all()
    
    return render_template('workouts/log_exercises.html', title='Log Exercises', 
                          workout_log=workout_log, workout=workout, workout_exercises=workout_exercises)

@workouts.route('/log-exercise/<int:log_id>/<int:exercise_id>', methods=['GET', 'POST'])
@login_required
def log_specific_exercise(log_id, exercise_id):
    """Log a specific exercise from a workout"""
    workout_log = WorkoutLog.query.get_or_404(log_id)
    
    # Check if user is the owner of this log
    if workout_log.user_id != current_user.id:
        flash('You cannot access this workout log.', 'danger')
        return redirect(url_for('workouts.log_workout'))
    
    exercise = Exercise.query.get_or_404(exercise_id)
    workout_exercise = WorkoutExercise.query.filter_by(workout_id=workout_log.workout_id, exercise_id=exercise_id).first_or_404()
    
    form = ExerciseLogForm()
    
    if form.validate_on_submit():
        exercise_log = ExerciseLog(
            workout_log_id=workout_log.id,
            exercise_id=exercise_id,
            sets_completed=form.sets_completed.data,
            reps=form.reps.data,
            weight=form.weight.data,
            notes=form.notes.data
        )
        db.session.add(exercise_log)
        db.session.commit()
        flash(f'{exercise.name} has been logged successfully!', 'success')
        
        # Check if all exercises have been logged
        workout = Workout.query.get(workout_log.workout_id)
        total_exercises = workout.exercises.count()
        logged_exercises = workout_log.exercise_logs.count()
        
        if logged_exercises >= total_exercises:
            flash('All exercises have been logged for this workout!', 'success')
            return redirect(url_for('workouts.workout_history'))
        else:
            # Find the next exercise that hasn't been logged yet
            logged_exercise_ids = [log.exercise_id for log in workout_log.exercise_logs.all()]
            next_exercise = workout.exercises.filter(~WorkoutExercise.exercise_id.in_(logged_exercise_ids)).first()
            
            if next_exercise:
                return redirect(url_for('workouts.log_specific_exercise', 
                                      log_id=log_id, exercise_id=next_exercise.exercise_id))
            else:
                return redirect(url_for('workouts.workout_history'))
    
    # Pre-fill form with suggested values
    form.sets_completed.data = workout_exercise.sets
    form.reps.data = workout_exercise.reps.replace('-', ',')
    
    return render_template('workouts/log_specific_exercise.html', title=f'Log {exercise.name}', 
                          form=form, exercise=exercise, workout_exercise=workout_exercise)

@workouts.route('/workout-history')
@login_required
def workout_history():
    """Display user's workout history"""
    logs = WorkoutLog.query.filter_by(user_id=current_user.id).order_by(WorkoutLog.date.desc()).all()
    return render_template('workouts/history.html', title='Workout History', logs=logs)

@workouts.route('/workout-log/<int:log_id>')
@login_required
def workout_log_detail(log_id):
    """Display details of a specific workout log"""
    log = WorkoutLog.query.get_or_404(log_id)
    
    # Check if user is the owner of this log
    if log.user_id != current_user.id:
        flash('You cannot access this workout log.', 'danger')
        return redirect(url_for('workouts.workout_history'))
    
    workout = Workout.query.get(log.workout_id)
    exercise_logs = log.exercise_logs.all()
    
    return render_template('workouts/log_detail.html', title='Workout Log Details', 
                          log=log, workout=workout, exercise_logs=exercise_logs)
