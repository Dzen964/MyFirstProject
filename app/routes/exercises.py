from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_required
from app.models import Exercise
from app import db
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
import os
from werkzeug.utils import secure_filename

exercises = Blueprint('exercises', __name__)

class ExerciseForm(FlaskForm):
    """Form for creating and editing exercises"""
    name = StringField('Exercise Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    muscle_group = SelectField('Primary Muscle Group', 
                             choices=[
                                 ('Chest', 'Chest'),
                                 ('Back', 'Back'),
                                 ('Shoulders', 'Shoulders'),
                                 ('Legs', 'Legs'),
                                 ('Arms', 'Arms'),
                                 ('Core', 'Core'),
                                 ('Full Body', 'Full Body'),
                                 ('Cardio', 'Cardio')
                             ])
    equipment = StringField('Equipment Needed', validators=[Length(max=100)])
    difficulty = SelectField('Difficulty', 
                           choices=[
                               ('Beginner', 'Beginner'),
                               ('Intermediate', 'Intermediate'),
                               ('Advanced', 'Advanced')
                           ])
    instructions = TextAreaField('Instructions', validators=[Length(max=2000)])
    image = FileField('Exercise Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    video_url = StringField('Video URL', validators=[Length(max=255)])
    submit = SubmitField('Save Exercise')

@exercises.route('/exercise-library')
@login_required
def exercise_library():
    """Display the exercise library"""
    # Get filter parameters
    muscle_group = request.args.get('muscle_group', '')
    difficulty = request.args.get('difficulty', '')
    search_term = request.args.get('search', '')
    
    # Base query
    query = Exercise.query
    
    # Apply filters if they exist
    if muscle_group:
        query = query.filter_by(muscle_group=muscle_group)
    
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    
    if search_term:
        query = query.filter(Exercise.name.ilike(f'%{search_term}%'))
    
    # Get results and sort by name
    exercises_list = query.order_by(Exercise.name).all()
    
    # Get unique muscle groups and difficulties for filter options
    muscle_groups = db.session.query(Exercise.muscle_group).distinct().all()
    muscle_groups = sorted([mg[0] for mg in muscle_groups if mg[0]])
    
    difficulties = db.session.query(Exercise.difficulty).distinct().all()
    difficulties = sorted([d[0] for d in difficulties if d[0]])
    
    return render_template('exercises/library.html', title='Exercise Library', 
                          exercises=exercises_list, 
                          muscle_groups=muscle_groups,
                          difficulties=difficulties,
                          selected_muscle_group=muscle_group,
                          selected_difficulty=difficulty,
                          search_term=search_term)

@exercises.route('/exercise/<int:exercise_id>')
@login_required
def exercise_detail(exercise_id):
    """View details of a specific exercise"""
    exercise = Exercise.query.get_or_404(exercise_id)
    return render_template('exercises/detail.html', title=exercise.name, exercise=exercise)

@exercises.route('/exercise/new', methods=['GET', 'POST'])
@login_required
def new_exercise():
    """Create a new exercise"""
    form = ExerciseForm()
    
    if form.validate_on_submit():
        exercise = Exercise(
            name=form.name.data,
            description=form.description.data,
            muscle_group=form.muscle_group.data,
            equipment=form.equipment.data,
            difficulty=form.difficulty.data,
            instructions=form.instructions.data,
            video_url=form.video_url.data
        )
        
        if form.image.data:
            image_file = save_exercise_image(form.image.data)
            exercise.image = image_file
        
        db.session.add(exercise)
        db.session.commit()
        flash('Your exercise has been created!', 'success')
        return redirect(url_for('exercises.exercise_detail', exercise_id=exercise.id))
    
    return render_template('exercises/create_exercise.html', title='New Exercise', 
                          form=form, legend='Create Exercise')

@exercises.route('/exercise/<int:exercise_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_exercise(exercise_id):
    """Edit an exercise"""
    exercise = Exercise.query.get_or_404(exercise_id)
    form = ExerciseForm()
    
    if form.validate_on_submit():
        exercise.name = form.name.data
        exercise.description = form.description.data
        exercise.muscle_group = form.muscle_group.data
        exercise.equipment = form.equipment.data
        exercise.difficulty = form.difficulty.data
        exercise.instructions = form.instructions.data
        exercise.video_url = form.video_url.data
        
        if form.image.data:
            image_file = save_exercise_image(form.image.data)
            exercise.image = image_file
        
        db.session.commit()
        flash('Your exercise has been updated!', 'success')
        return redirect(url_for('exercises.exercise_detail', exercise_id=exercise.id))
    
    elif request.method == 'GET':
        form.name.data = exercise.name
        form.description.data = exercise.description
        form.muscle_group.data = exercise.muscle_group
        form.equipment.data = exercise.equipment
        form.difficulty.data = exercise.difficulty
        form.instructions.data = exercise.instructions
        form.video_url.data = exercise.video_url
    
    return render_template('exercises/create_exercise.html', title='Edit Exercise', 
                          form=form, legend='Edit Exercise')

def save_exercise_image(form_picture):
    """Save exercise image with a unique filename"""
    random_hex = os.urandom(8).hex()
    _, f_ext = os.path.splitext(secure_filename(form_picture.filename))
    picture_filename = random_hex + f_ext
    picture_path = os.path.join('app', 'static', 'img', 'exercises', picture_filename)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    # Save the picture
    form_picture.save(picture_path)
    
    return f'img/exercises/{picture_filename}'
