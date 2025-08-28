from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from models.models import db, User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

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
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
