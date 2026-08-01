from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from mealplanner.config import Config
import cloudinary

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    cloudinary.config(
        cloud_name=app.config.get('CLOUDINARY_CLOUD_NAME'),
        api_key=app.config.get('CLOUDINARY_API_KEY'),
        api_secret=app.config.get('CLOUDINARY_API_SECRET')
    )
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate = Migrate(app, db)

    from mealplanner.users.routes import users
    from mealplanner.meals.routes import meals
    from mealplanner.main.routes import main
    from mealplanner.errors.handlers import errors
    app.register_blueprint(users)
    app.register_blueprint(meals)
    app.register_blueprint(main)
    app.register_blueprint(errors)

    @app.context_processor
    def inject_vapid_key():
        return dict(vapid_public_key=app.config.get('VAPID_PUBLIC_KEY'))

    return app