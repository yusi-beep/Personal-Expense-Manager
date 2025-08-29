import os
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager
from config import DevConfig, ProdConfig
from models.models import db, User

# load .env early
load_dotenv()

def create_app():
    app = Flask(__name__)

    # configuration (APP_ENV = production / development)
    app_env = os.environ.get("APP_ENV", "development").lower()
    app.config.from_object(ProdConfig if app_env == "production" else DevConfig)

    # DB init
    db.init_app(app)

    # Blueprints
    from routes.api import api_bp
    from routes.auth import auth_bp
    from routes.home import home_bp
    from routes.records import records_bp
    from routes.categories import categories_bp
    

    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(categories_bp)

    # Login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # only for DEV; in production – Alembic migrations
        db.create_all()
    app.run(debug=True)  # в production clear debug=True
