from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from app.models import User
from app import db
from urllib.parse import urlparse
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField, DateField, FloatField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed

auth = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    """Login form for user authentication"""
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """Registration form for new users"""
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        """Check if username already exists"""
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        """Check if email already exists"""
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ProfileForm(FlaskForm):
    """Form for editing user profile"""
    first_name = StringField('First Name', validators=[Length(max=64)])
    last_name = StringField('Last Name', validators=[Length(max=64)])
    date_of_birth = DateField('Date of Birth', validators=[], format='%Y-%m-%d')
    height = FloatField('Height (cm)')
    weight = FloatField('Weight (kg)')
    gender = SelectField('Gender', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')])
    theme = SelectField('Theme Preference', choices=[('light', 'Light Mode'), ('dark', 'Dark Mode')])
    profile_image = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update Profile')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        flash('Login successful!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)

@auth.route('/logout')
def logout():
    """Handle user logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Display and edit user profile"""
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.date_of_birth = form.date_of_birth.data
        current_user.height = form.height.data
        current_user.weight = form.weight.data
        current_user.gender = form.gender.data
        current_user.theme = form.theme.data
        
        if form.profile_image.data:
            # Save profile image
            image_file = save_profile_picture(form.profile_image.data)
            current_user.profile_image = image_file
            
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        # Pre-populate form with existing user data
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.date_of_birth.data = current_user.date_of_birth
        form.height.data = current_user.height
        form.weight.data = current_user.weight
        form.gender.data = current_user.gender
        form.theme.data = current_user.theme
    
    return render_template('auth/profile.html', title='Profile', form=form, user=current_user)

@auth.route('/update_theme', methods=['POST'])
@login_required
def update_theme():
    """Update user theme preference"""
    data = request.get_json()
    if data and 'theme' in data:
        theme = data['theme']
        if theme in ['light', 'dark']:
            current_user.theme = theme
            db.session.commit()
            return jsonify({'success': True, 'theme': theme})
    return jsonify({'success': False}), 400

def save_profile_picture(form_picture):
    """Save user profile picture with a unique filename"""
    random_hex = os.urandom(8).hex()
    _, f_ext = os.path.splitext(secure_filename(form_picture.filename))
    picture_filename = random_hex + f_ext
    picture_path = os.path.join('app', 'static', 'img', 'profile_pics', picture_filename)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    # Save the picture
    form_picture.save(picture_path)
    
    return f'img/profile_pics/{picture_filename}'
