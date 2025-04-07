from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required

# Create the Blueprint instance named 'main'
main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Home page route"""
    return render_template('index.html', title='Home')

@main.route('/dashboard')
@login_required
def dashboard():
    """Dashboard route for logged-in users"""
    # Use a try-except block to handle potential database errors
    try:
        return render_template('dashboard.html', title='Dashboard')
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Dashboard error: {str(e)}")
        flash("There was an error loading your dashboard. Our team has been notified.", "danger")
        return render_template('error.html', title='Error'), 500

@main.route('/about')
def about():
    """About page route"""
    return render_template('about.html', title='About')

@main.route('/contact')
def contact():
    """Contact page route"""
    return render_template('contact.html', title='Contact')

@main.route('/theme/<theme>')
def set_theme(theme):
    """Set user theme preference (dark/light)"""
    if current_user.is_authenticated:
        if theme in ['dark', 'light']:
            current_user.theme = theme
            from app import db
            db.session.commit()
    next_page = request.args.get('next') or request.referrer or url_for('main.index')
    return redirect(next_page)
