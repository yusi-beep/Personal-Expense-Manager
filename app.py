from flask import Flask
from flask_login import LoginManager
from config import DevConfig, ProdConfig
from models.models import db, User

def create_app():
    app = Flask(__name__)

    # select configuration:
    # - if APP_ENV=production => ProdConfig
    # - else DevConfig (default)
    app_env = os.environ.get("APP_ENV", "development").lower()
    if app_env == "production":
        app.config.from_object(ProdConfig)
    else:
        app.config.from_object(DevConfig)

    db.init_app(app)

    from routes.auth import auth_bp
    from routes.home import home_bp
    from routes.records import records_bp
    from routes.categories import categories_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(records_bp)
    app.register_blueprint(categories_bp)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

if __name__ == "__main__":
    import os
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run()

