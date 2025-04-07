from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-dev-key-replace-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness_app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
      # Import and register blueprints
    from app.routes.main_routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.routes.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    from app.routes.workouts import workouts as workouts_blueprint
    app.register_blueprint(workouts_blueprint)
    
    from app.routes.nutrition import nutrition as nutrition_blueprint
    app.register_blueprint(nutrition_blueprint)
    
    from app.routes.exercises import exercises as exercises_blueprint
    app.register_blueprint(exercises_blueprint)
    
    from app.routes.progress import progress as progress_blueprint
    app.register_blueprint(progress_blueprint)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
